"""
app/api/routes/auth.py
Authentication routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.lab import LabProfile
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, SuccessResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    await db.flush()

    profile_id = ""
    # Create role-specific profile
    if data.role == "patient":
        profile = PatientProfile(
            user_id=user.id,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            blood_group=data.blood_group or "Unknown"
        )
        db.add(profile)
        await db.flush()
        profile_id = profile.id
    elif data.role == "doctor":
        profile = DoctorProfile(
            user_id=user.id,
            full_name=data.full_name,
            specialization=data.specialization or "General Medicine",
            medical_registration_number=data.medical_registration_number or "",
            hospital_affiliation=data.hospital_affiliation or ""
        )
        db.add(profile)
        await db.flush()
        profile_id = profile.id
    elif data.role == "lab":
        profile = LabProfile(
            user_id=user.id,
            lab_name=data.full_name,
            registration_id=data.lab_registration_id or "",
            address=data.lab_address or "",
            city=data.lab_city or ""
        )
        db.add(profile)
        await db.flush()
        profile_id = profile.id

    token = create_access_token({"sub": user.id, "role": user.role, "profile_id": profile_id})
    
    await log_action(db, user.id, user.role, AuditAction.CREATE, "user", user.id, None, request, True)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "profile_id": profile_id,
        "full_name": data.full_name
    }

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        # Update failed attempts if user exists
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            await log_action(db, user.id, user.role, AuditAction.LOGIN_FAILED, "user", user.id, None, request, False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account locked. Try again later.")

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    
    # Get profile_id
    profile_id = ""
    full_name = ""
    if user.role == "patient":
        p_stmt = select(PatientProfile).where(PatientProfile.user_id == user.id)
        p_res = await db.execute(p_stmt)
        p = p_res.scalar_one_or_none()
        profile_id = p.id if p else ""
        full_name = p.full_name if p else ""
    elif user.role == "doctor":
        d_stmt = select(DoctorProfile).where(DoctorProfile.user_id == user.id)
        d_res = await db.execute(d_stmt)
        d = d_res.scalar_one_or_none()
        profile_id = d.id if d else ""
        full_name = d.full_name if d else ""
    elif user.role == "lab":
        l_stmt = select(LabProfile).where(LabProfile.user_id == user.id)
        l_res = await db.execute(l_stmt)
        l = l_res.scalar_one_or_none()
        profile_id = l.id if l else ""
        full_name = l.lab_name if l else ""

    token = create_access_token({"sub": user.id, "role": user.role, "profile_id": profile_id, "email": user.email})
    
    await log_action(db, user.id, user.role, AuditAction.LOGIN, "user", user.id, None, request, True)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "profile_id": profile_id,
        "full_name": full_name
    }
