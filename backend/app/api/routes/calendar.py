"""
app/api/routes/calendar.py
Calendar management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.calendar_event import CalendarEvent
from app.models.doctor import DoctorProfile
from app.schemas.schemas import CalendarEventResponse, CalendarEventCreate, CalendarEventUpdate
from app.core.security import require_doctor, require_any_role
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.post("/", response_model=CalendarEventResponse)
async def create_event(
    request: Request,
    data: CalendarEventCreate,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    event = CalendarEvent(
        doctor_id=doctor_id,
        patient_id=data.patient_id,
        title=data.title,
        event_type=data.event_type,
        description=data.description,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        clinic_name=data.clinic_name,
        clinic_address=data.clinic_address,
        room=data.room,
        notes=data.notes,
        reminder_minutes_before=data.reminder_minutes_before
    )
    db.add(event)
    await db.flush()

    await log_action(db, current_user["sub"], "doctor", AuditAction.CREATE, "calendar_event", event.id, data.patient_id, request, True)
    return event

@router.get("/", response_model=List[CalendarEventResponse])
async def get_my_events(
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    stmt = select(CalendarEvent).where(CalendarEvent.doctor_id == doctor_id).order_by(CalendarEvent.start_datetime.asc())
    result = await db.execute(stmt)
    return result.scalars().all()
