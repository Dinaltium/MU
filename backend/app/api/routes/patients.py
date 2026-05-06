"""
app/api/routes/patients.py
Patient-specific routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.patient import PatientProfile
from app.models.doctor_patient import DoctorPatient
from app.models.doctor import DoctorProfile
from app.schemas.schemas import PatientProfileResponse, PatientProfileUpdate, DoctorProfileResponse
from app.core.security import get_current_user, require_patient
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.get("/me", response_model=PatientProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PatientProfile).where(PatientProfile.user_id == current_user["sub"])
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.patch("/me", response_model=PatientProfileResponse)
async def update_my_profile(
    request: Request,
    data: PatientProfileUpdate,
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PatientProfile).where(PatientProfile.user_id == current_user["sub"])
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await log_action(db, current_user["sub"], "patient", AuditAction.UPDATE, "patient_profile", profile.id, profile.id, request, True)
    return profile

@router.get("/my-doctors", response_model=List[DoctorProfileResponse])
async def get_my_doctors(
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    # Get patient_id first
    p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
    p_res = await db.execute(p_stmt)
    patient_id = p_res.scalar_one_or_none()
    
    # Get assigned doctors
    stmt = select(DoctorProfile).join(DoctorPatient, DoctorPatient.doctor_id == DoctorProfile.id).where(
        DoctorPatient.patient_id == patient_id,
        DoctorPatient.status == "active"
    )
    result = await db.execute(stmt)
    return result.scalars().all()
