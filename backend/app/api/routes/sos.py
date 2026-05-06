"""
app/api/routes/sos.py
SOS emergency routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.sos_alert import SosAlert
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.doctor_patient import DoctorPatient
from app.models.user import User
from app.schemas.schemas import SOSResponse, SOSCreate, SOSRespondRequest, SuccessResponse
from app.core.security import require_patient, require_doctor
from app.services.audit_service import log_action, AuditAction
from app.api.websocket import manager

router = APIRouter()

@router.post("/trigger", response_model=SOSResponse)
async def trigger_sos(
    request: Request,
    data: SOSCreate,
    current_user: dict = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    p_stmt = select(PatientProfile).where(PatientProfile.user_id == current_user["sub"])
    p_res = await db.execute(p_stmt)
    patient = p_res.scalar_one_or_none()

    sos = SosAlert(
        patient_id=patient.id,
        triggered_at=datetime.utcnow(),
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        message=data.message,
        status="pending"
    )
    db.add(sos)
    await db.flush()

    await log_action(db, current_user["sub"], "patient", AuditAction.SOS_TRIGGER, "sos_alert", sos.id, patient.id, request, True)

    # Broadcast to assigned doctors
    dp_stmt = select(DoctorProfile.user_id).join(DoctorPatient, DoctorPatient.doctor_id == DoctorProfile.id).where(
        DoctorPatient.patient_id == patient.id,
        DoctorPatient.status == "active"
    )
    dp_res = await db.execute(dp_stmt)
    doctor_uids = dp_res.scalars().all()

    await manager.broadcast_sos(doctor_uids, {
        "id": sos.id,
        "patient_name": patient.full_name,
        "location": {"lat": sos.location_lat, "lng": sos.location_lng},
        "message": sos.message,
        "triggered_at": sos.triggered_at.isoformat()
    })

    return sos

@router.post("/{sos_id}/respond", response_model=SuccessResponse)
async def respond_sos(
    request: Request,
    sos_id: str,
    data: SOSRespondRequest,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    stmt = select(SosAlert).where(SosAlert.id == sos_id)
    result = await db.execute(stmt)
    sos = result.scalar_one_or_none()
    
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")

    sos.status = data.action
    sos.responded_by_doctor_id = doctor_id
    sos.responded_at = datetime.utcnow()
    sos.resolution_notes = data.resolution_notes

    await log_action(db, current_user["sub"], "doctor", AuditAction.SOS_RESPOND, "sos_alert", sos.id, sos.patient_id, request, True)

    return {"success": True}
