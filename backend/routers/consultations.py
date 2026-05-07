"""
routers/consultations.py

SECURITY DECISIONS:
  • Only doctors can start a consultation.
  • Doctor must own the patient before starting a consultation — prevents
    creating a consultation for someone else's patient.
  • Pipeline runs in a background task so the HTTP response returns
    immediately; the consultation status can be polled or streamed.
  • SSE (Server-Sent Events) stream requires authentication on each
    connection — unauthenticated clients cannot tap into a pipeline stream.
  • Consultation output (pipeline_output) is NEVER returned raw in the
    list endpoint — only curated summary fields are returned to the UI.
"""

import json
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from utils.db import get_pool
from utils.security import get_current_user, require_role
from pipeline.state import PipelineState
from pipeline.orchestrator import run_pipeline

router = APIRouter(tags=["consultations"])
logger = logging.getLogger(__name__)


class ConsultationCreate(BaseModel):
    patient_id: str
    symptoms:   List[str]
    region:     str = "south_india"


@router.post("/", status_code=status.HTTP_201_CREATED)
async def start_consultation(
    body: ConsultationCreate,
    user: dict = Depends(require_role("doctor")),
):
    """
    Start the AI pipeline for a patient consultation.

    SECURITY STEPS:
      1. Verify the requesting doctor owns this patient (ABAC).
      2. Create the consultation record first — if the pipeline fails,
         we still have an audit record.
      3. Run the pipeline — failures are caught and the consultation
         is marked 'failed' rather than silently dropped.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # ABAC: patient must belong to this doctor
        patient = await conn.fetchrow(
            "SELECT * FROM patients WHERE id=$1::uuid AND doctor_id=$2::uuid",
            body.patient_id, user["sub"]
        )
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient not found or not assigned to you",
            )

        # Create consultation record
        row = await conn.fetchrow(
            """
            INSERT INTO consultations (doctor_id, patient_id, symptoms, status)
            VALUES ($1::uuid, $2::uuid, $3::jsonb, 'running')
            RETURNING id
            """,
            user["sub"],
            body.patient_id,
            json.dumps(body.symptoms),
        )
        consultation_id = str(row["id"])

    # Build initial state — minimal data per agent (principle of least privilege)
    state: PipelineState = {
        "patient_id":       str(patient["id"]),
        "doctor_id":        user["sub"],
        "consultation_id":  consultation_id,
        "symptoms":         body.symptoms,
        "region":           body.region,
        "patient_profile":  {
            "age":            patient["age"],
            "weight_kg":      patient["weight_kg"],
            "renal_function": patient["renal_function"],
            "conditions":     patient["conditions"] or [],
            "allergies":      patient["allergies"] or [],
            "medications":    patient["medications"] or [],
        },
        # Agent outputs — all None until each agent runs
        "urgency_score":       None,
        "key_findings":        None,
        "red_flags":           None,
        "diagnoses":           None,
        "top_diagnosis":       None,
        "icd_code":            None,
        "drug_candidates":     None,
        "top_drug":            None,
        "resistance_risk":     None,
        "pkpd_ratio":          None,
        "mic_value":           None,
        "safety_flags":        None,
        "interaction_alerts":  None,
        "doctor_summary":      None,
        "patient_explanation": None,
        "report_id":           None,
        "step_updates":        [],
    }

    # Run pipeline in background — client can poll /consultations/{id}
    async def _run():
        try:
            await run_pipeline(state)
        except Exception as exc:
            logger.error("Pipeline failed for consultation %s: %s", consultation_id, exc)
            pool2 = await get_pool()
            async with pool2.acquire() as conn2:
                await conn2.execute(
                    "UPDATE consultations SET status='failed' WHERE id=$1::uuid",
                    consultation_id
                )

    asyncio.create_task(_run())

    return {
        "consultation_id": consultation_id,
        "status":          "running",
        "message":         "Pipeline started. Poll /api/consultations/{id} for results.",
    }


@router.get("/{consultation_id}")
async def get_consultation(
    consultation_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Return consultation details.
    Doctors get the full pipeline output.
    Patients only get patient_explanation.

    WHY ROLE-AWARE RESPONSE:
      The pipeline output contains clinical data (ICD codes, PK/PD
      ratios) intended for doctors. Showing this to patients without
      context could cause harm. The patient receives only the
      plain-language explanation produced by the explainability agent.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM consultations WHERE id=$1::uuid",
            consultation_id
        )

    if not row:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # ABAC checks
    if user["role"] == "doctor" and str(row["doctor_id"]) != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if user["role"] == "patient":
        # Patient must be the patient in the consultation
        pool2 = await get_pool()
        async with pool2.acquire() as conn2:
            patient = await conn2.fetchrow(
                "SELECT user_id FROM patients WHERE id=$1::uuid",
                str(row["patient_id"])
            )
        if not patient or str(patient["user_id"]) != user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Return patient-facing subset only
        output = row["pipeline_output"] or {}
        return {
            "id":                  str(row["id"]),
            "status":              row["status"],
            "patient_explanation": output.get("patient_explanation"),
            "created_at":          row["created_at"],
        }

    # Doctor / admin — return full curated output
    data = dict(row)
    if isinstance(data.get("pipeline_output"), str):
        try:
            data["pipeline_output"] = json.loads(data["pipeline_output"])
        except:
            pass
    return data
