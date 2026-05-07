"""
app/api/routes/ai_assist.py
AI Assist routes for pipeline execution and clinical decision support.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.diagnosis import Diagnosis
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.medication import Medication
from app.schemas.schemas import PipelineRunRequest, PipelineRunResponse, SuccessResponse, HITLApproveRequest
from app.agents.pipeline_state import PipelineState
from app.agents.orchestrator import run_pipeline
from app.core.security import require_doctor
from app.core.consent_gate import assert_consent

router = APIRouter()

@router.post("/run-pipeline/{diagnosis_id}", response_model=PipelineRunResponse)
async def trigger_ai_pipeline(
    diagnosis_id: str,
    data: PipelineRunRequest,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    # 1. Get diagnosis and doctor profile
    d_stmt = select(Diagnosis).where(Diagnosis.id == diagnosis_id)
    d_res = await db.execute(d_stmt)
    diagnosis = d_res.scalar_one_or_none()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    doc_stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user["sub"])
    doc_res = await db.execute(doc_stmt)
    doctor = doc_res.scalar_one_or_none()

    # 2. Assert consent
    await assert_consent(doctor.id, diagnosis.patient_id, "read_diagnoses", db)

    # 3. Get patient context
    p_stmt = select(PatientProfile).where(PatientProfile.id == diagnosis.patient_id)
    p_res = await db.execute(p_stmt)
    patient = p_res.scalar_one_or_none()

    # Get current medications
    m_stmt = select(Medication.name).where(Medication.patient_id == patient.id, Medication.status == "active")
    m_res = await db.execute(m_stmt)
    meds = m_res.scalars().all()

    # 4. Initialize pipeline state
    state = PipelineState(
        patient_id=patient.id,
        doctor_id=doctor.id,
        diagnosis_id=diagnosis.id,
        disease_name=diagnosis.disease_name,
        severity=diagnosis.severity,
        symptoms=[], # In a real app, these would come from check-ins or request
        current_medications=list(meds),
        allergies=patient.allergies or [],
        chronic_conditions=patient.chronic_conditions or [],
        patient_age=0, # Need to calculate from DOB
        patient_gender=patient.gender,
        stage=diagnosis.stage
    )

    # 5. Run pipeline
    final_state = await run_pipeline(state, data.image_base64, db)

    # Convert state to response (Pydantic model)
    # This is a bit manual because PipelineRunResponse is a schema
    return {
        "id": final_state.pipeline_run_id or "pending",
        "doctor_id": final_state.doctor_id,
        "patient_id": final_state.patient_id,
        "diagnosis_id": final_state.diagnosis_id,
        "pipeline_status": final_state.pipeline_status,
        "hitl_required": final_state.hitl_pause,
        "hitl_reason": final_state.hitl_reason,
        "hitl_approved": None,
        "agent_outputs": [
            final_state.agent_1_output, final_state.agent_2_output, final_state.agent_3_output,
            final_state.agent_4_output, final_state.agent_5_output, final_state.agent_6_output,
            final_state.agent_7_output, final_state.agent_8_output, final_state.agent_9_output
        ],
        "final_recommendation": final_state.agent_7_output,
        "step_logs": final_state.step_logs,
        "pipeline_duration_ms": 0,
        "run_at": datetime.utcnow(),
        "completed_at": datetime.utcnow() if final_state.pipeline_status == "complete" else None
    }

@router.get("/medication-search")
async def medication_search(query: str, current_user: dict = Depends(require_doctor)):
    from app.services import gemini_service
    return await gemini_service.search_medications(query)

@router.get("/disease-list")
async def disease_list(current_user: dict = Depends(require_doctor)):
    from app.services import gemini_service
    return await gemini_service.get_disease_list()
