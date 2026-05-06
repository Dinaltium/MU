"""
app/api/routes/diagnoses.py
Diagnosis management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.db.database import get_db
from app.models.diagnosis import Diagnosis
from app.models.doctor import DoctorProfile
from app.schemas.schemas import DiagnosisResponse, DiagnosisCreate, DiagnosisUpdate
from app.core.security import get_current_user, require_doctor, require_any_role
from app.core.consent_gate import assert_consent
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.post("/", response_model=DiagnosisResponse)
async def create_diagnosis(
    request: Request,
    data: DiagnosisCreate,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    # Verify consent
    await assert_consent(doctor_id, data.patient_id, "read_diagnoses", db)

    diagnosis = Diagnosis(
        doctor_id=doctor_id,
        patient_id=data.patient_id,
        disease_name=data.disease_name,
        disease_category=data.disease_category,
        icd_10_code=data.icd_10_code,
        stage=data.stage,
        severity=data.severity,
        doctor_notes=data.doctor_notes,
        clinic_name=data.clinic_name,
        clinic_address=data.clinic_address
    )
    db.add(diagnosis)
    await db.flush()

    await log_action(db, current_user["sub"], "doctor", AuditAction.CREATE, "diagnosis", diagnosis.id, data.patient_id, request, True)
    return diagnosis

@router.get("/patient/{patient_id}", response_model=List[DiagnosisResponse])
async def get_patient_diagnoses(
    patient_id: str,
    current_user: dict = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    # If doctor, check consent
    if current_user["role"] == "doctor":
        d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
        d_res = await db.execute(d_stmt)
        doctor_id = d_res.scalar_one_or_none()
        await assert_consent(doctor_id, patient_id, "read_diagnoses", db)
    # If patient, verify it's their own ID
    elif current_user["role"] == "patient":
        from app.models.patient import PatientProfile
        p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
        p_res = await db.execute(p_stmt)
        my_patient_id = p_res.scalar_one_or_none()
        if my_patient_id != patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to patient data")

    stmt = select(Diagnosis).where(Diagnosis.patient_id == patient_id).order_by(Diagnosis.diagnosed_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
