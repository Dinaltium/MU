"""
app/api/routes/doctors.py
Doctor-specific routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.doctor import DoctorProfile
from app.models.doctor_patient import DoctorPatient
from app.models.patient import PatientProfile
from app.models.user import User
from app.models.consent import PatientConsent, DEFAULT_SCOPE
from app.schemas.schemas import DoctorProfileResponse, DoctorProfileUpdate, PatientProfileResponse, AssignPatientRequest, SuccessResponse
from app.core.security import require_doctor
from app.services.audit_service import log_action, AuditAction
from app.services.notification_service import notify_consent_granted

router = APIRouter()

@router.get("/me", response_model=DoctorProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user["sub"])
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.patch("/me", response_model=DoctorProfileResponse)
async def update_my_profile(
    request: Request,
    data: DoctorProfileUpdate,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user["sub"])
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await log_action(db, current_user["sub"], "doctor", AuditAction.UPDATE, "doctor_profile", profile.id, None, request, True)
    return profile

@router.post("/assign-patient", response_model=SuccessResponse)
async def assign_patient(
    request: Request,
    data: AssignPatientRequest,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    # 1. Get doctor profile
    d_stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor = d_res.scalar_one_or_none()

    # 2. Find patient by email
    u_stmt = select(User).where(User.email == data.patient_email, User.role == "patient")
    u_res = await db.execute(u_stmt)
    patient_user = u_res.scalar_one_or_none()
    if not patient_user:
        raise HTTPException(status_code=404, detail="Patient not found")

    p_stmt = select(PatientProfile).where(PatientProfile.user_id == patient_user.id)
    p_res = await db.execute(p_stmt)
    patient = p_res.scalar_one_or_none()

    # 3. Create DoctorPatient assignment
    dp = DoctorPatient(
        doctor_id=doctor.id,
        patient_id=patient.id,
        assigned_clinic_name=data.assigned_clinic_name,
        assigned_clinic_address=data.assigned_clinic_address,
        status="active"
    )
    db.add(dp)

    # 4. Auto-grant consent
    consent = PatientConsent(
        patient_id=patient.id,
        doctor_id=doctor.id,
        is_active=True,
        consent_scope=DEFAULT_SCOPE,
        auto_granted=True
    )
    db.add(consent)
    
    await log_action(db, current_user["sub"], "doctor", AuditAction.CREATE, "doctor_patient", f"{doctor.id}-{patient.id}", patient.id, request, True)
    
    # 5. Notify patient
    await notify_consent_granted(db, patient_user.id, doctor.full_name)

    return {"success": True}

@router.get("/my-patients", response_model=List[PatientProfileResponse])
async def get_my_patients(
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    stmt = select(PatientProfile).join(DoctorPatient, DoctorPatient.patient_id == PatientProfile.id).where(
        DoctorPatient.doctor_id == doctor_id,
        DoctorPatient.status == "active"
    )
    result = await db.execute(stmt)
    return result.scalars().all()
