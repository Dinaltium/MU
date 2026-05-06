"""
agents/report.py

WHY A DEDICATED REPORT AGENT:
  Persisting results is treated as its own pipeline step because:
    1. It creates an immutable audit record — even if the consultation
       is later queried differently, the pipeline output is preserved.
    2. Failure to write should be explicit (pipeline fails) rather than
       silent (result computed but lost).
    3. Separating persistence from computation means we can re-run
       the report step alone if a write fails without re-running
       expensive inference steps.

SECURITY NOTE:
  • We write a CURATED subset of state to pipeline_output — not the
    full state dict. This prevents internal fields (step_updates, raw
    probabilities) from leaking to the client via the consultations API.
  • Parameterised queries (asyncpg $1 placeholders) are used exclusively.
    No string formatting is used to build SQL. This eliminates SQL injection.
  • The report agent does not return data to the user — it writes to the
    DB and sets state["report_id"] for audit trail purposes only.
"""

import json
import logging
from utils.db import get_pool
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "ReportAgent:running:Persisting consultation results..."
    )

    # Only persist curated fields — never raw pipeline internals
    curated_output = {
        "diagnoses":           state["diagnoses"],
        "top_diagnosis":       state["top_diagnosis"],
        "icd_code":            state["icd_code"],
        "top_drug":            state["top_drug"],
        "resistance_risk":     state["resistance_risk"],
        "pkpd_ratio":          state["pkpd_ratio"],
        "safety_flags":        state["safety_flags"],
        "doctor_summary":      state["doctor_summary"],
        "patient_explanation": state["patient_explanation"],
    }

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Atomic update: set status + pipeline_output in one statement
        await conn.execute(
            """
            UPDATE consultations
            SET pipeline_output = $1::jsonb,
                status          = 'complete'
            WHERE id = $2::uuid
            """,
            json.dumps(curated_output),
            state["consultation_id"],
        )

        row = await conn.fetchrow(
            """
            INSERT INTO recommendations
            (consultation_id, drug_name, diagnosis, resistance_risk, doctor_approved)
            VALUES ($1::uuid, $2, $3, $4, false)
            RETURNING id
            """,
            state["consultation_id"],
            state["top_drug"],
            state["top_diagnosis"],
            state["resistance_risk"],
        )

    state["report_id"] = str(row["id"])

    state["step_updates"].append(
        f"ReportAgent:complete:Report {state['report_id']} written to database"
    )
    logger.info(
        "Consultation %s complete — report %s",
        state["consultation_id"],
        state["report_id"],
    )
    return state
