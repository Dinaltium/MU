"""
app/api/routes/medications.py
Medication management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.medication import Medication, MedicationLog
from app.models.doctor import DoctorProfile
from app.models.patient import PatientProfile
from app.schemas.schemas import MedicationResponse, MedicationCreate, MedicationLogUpdate, MedicationLogResponse, SuccessResponse
from app.core.security import require_doctor, require_patient, require_any_role
from app.core.consent_gate import assert_consent
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.post("/", response_model=MedicationResponse)
async def prescribe_medication(
    request: Request,
    data: MedicationCreate,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    await assert_consent(doctor_id, data.patient_id, "read_medications", db)

    medication = Medication(
        patient_id=data.patient_id,
        doctor_id=doctor_id,
        diagnosis_id=data.diagnosis_id,
        name=data.name,
        dosage=data.dosage,
        frequency=data.frequency,
        route=data.route,
        schedule_times=data.schedule_times,
        instructions=data.instructions,
        start_date=data.start_date,
        end_date=data.end_date,
        duration_days=data.duration_days,
        status="active"
    )
    db.add(medication)
    await db.flush()

    await log_action(db, current_user["sub"], "doctor", AuditAction.CREATE, "medication", medication.id, data.patient_id, request, True)
    return medication

@router.get("/my-schedule", response_model=List[MedicationResponse])
async def get_my_medications(
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
    p_res = await db.execute(p_stmt)
    patient_id = p_res.scalar_one_or_none()

    stmt = select(Medication).where(Medication.patient_id == patient_id, Medication.status == "active")
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/log", response_model=SuccessResponse)
async def log_medication_intake(
    request: Request,
    data: MedicationLogUpdate,
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
    p_res = await db.execute(p_stmt)
    patient_id = p_res.scalar_one_or_none()

    log = MedicationLog(
        medication_id=data.medication_id,
        patient_id=patient_id,
        scheduled_at=data.scheduled_at,
        taken_at=data.taken_at or (datetime.utcnow() if data.is_taken else None),
        is_taken=data.is_taken,
        is_missed=not data.is_taken,
        patient_note=data.patient_note
    )
    db.add(log)
    
    await log_action(db, current_user["sub"], "patient", AuditAction.UPDATE, "medication_log", log.id, patient_id, request, True)
    
    # Recalculate recovery score after logging
    from app.services.recovery_service import compute_recovery_score
    await compute_recovery_score(patient_id, db)

    return {"success": True}
