"""
app/api/routes/recovery.py
Recovery tracking routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import date

from app.db.database import get_db
from app.models.recovery import SymptomCheckin, RecoveryScore
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.schemas.schemas import SymptomCheckinCreate, RecoveryScoreResponse, SuccessResponse
from app.core.security import require_patient, require_any_role
from app.core.consent_gate import assert_consent
from app.services.audit_service import log_action, AuditAction
from app.services.recovery_service import compute_recovery_score

router = APIRouter()

@router.post("/checkin", response_model=SuccessResponse)
async def symptom_checkin(
    request: Request,
    data: SymptomCheckinCreate,
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
    p_res = await db.execute(p_stmt)
    patient_id = p_res.scalar_one_or_none()

    checkin = SymptomCheckin(
        patient_id=patient_id,
        checkin_date=date.today(),
        feel_status=data.feel_status,
        symptoms_present=data.symptoms_present,
        severity=data.severity,
        temperature_c=data.temperature_c,
        bp_systolic=data.bp_systolic,
        bp_diastolic=data.bp_diastolic,
        heart_rate=data.heart_rate,
        spo2=data.spo2,
        blood_glucose=data.blood_glucose,
        patient_note=data.patient_note
    )
    db.add(checkin)
    
    await log_action(db, current_user["sub"], "patient", AuditAction.CREATE, "symptom_checkin", checkin.id, patient_id, request, True)
    
    # Recalculate recovery score
    await compute_recovery_score(patient_id, db)

    return {"success": True}

@router.get("/score/{patient_id}", response_model=List[RecoveryScoreResponse])
async def get_recovery_scores(
    patient_id: str,
    current_user: dict = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    if current_user["role"] == "doctor":
        d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
        d_res = await db.execute(d_stmt)
        doctor_id = d_res.scalar_one_or_none()
        await assert_consent(doctor_id, patient_id, "read_recovery", db)
    elif current_user["role"] == "patient":
        p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
        p_res = await db.execute(p_stmt)
        my_patient_id = p_res.scalar_one_or_none()
        if my_patient_id != patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    stmt = select(RecoveryScore).where(RecoveryScore.patient_id == patient_id).order_by(RecoveryScore.score_date.desc()).limit(30)
    result = await db.execute(stmt)
    return result.scalars().all()
