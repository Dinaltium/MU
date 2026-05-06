"""
routers/monitoring.py

Patient check-in endpoint.
SECURITY: patient can only submit check-ins for their own consultation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from utils.db import get_pool
from utils.security import require_role

router = APIRouter(tags=["monitoring"])
logger = logging.getLogger(__name__)


class CheckinCreate(BaseModel):
    consultation_id:  str
    feel_status:      str = Field(..., pattern="^(better|same|worse)$")
    symptom_severity: int = Field(..., ge=1, le=10)


@router.post("/checkin")
async def checkin(
    body: CheckinCreate,
    user: dict = Depends(require_role("patient")),
):
    """
    Submit a daily check-in.

    SECURITY:
      1. Verify the consultation belongs to this patient.
      2. Compute recovery_score from severity (0-100 scale).
      3. Monitoring agent runs separately on a schedule — no user
         can trigger it directly, preventing DoS of the scoring loop.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verify consultation ownership
        row = await conn.fetchrow(
            """
            SELECT c.id FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            WHERE c.id = $1::uuid AND p.user_id = $2::uuid
            """,
            body.consultation_id, user["sub"]
        )
        if not row:
            raise HTTPException(
                status_code=403,
                detail="Consultation not found or not yours",
            )

        # Map severity (1=worst, 10=best) → recovery score (0=worst, 100=best)
        recovery_score = (body.symptom_severity / 10) * 100

        patient_row = await conn.fetchrow(
            "SELECT id FROM patients WHERE user_id=$1::uuid", user["sub"]
        )

        await conn.execute(
            """
            INSERT INTO monitoring_checkins
            (patient_id, consultation_id, feel_status, symptom_severity, recovery_score)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5)
            """,
            str(patient_row["id"]),
            body.consultation_id,
            body.feel_status,
            body.symptom_severity,
            recovery_score,
        )

    return {"message": "Check-in recorded", "recovery_score": recovery_score}
