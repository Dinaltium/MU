"""
app/models/calendar_event.py
Doctor calendar — appointments, surgeries, follow-ups, personal events.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # surgery|follow_up|consultation|personal
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clinic_name: Mapped[str | None] = mapped_column(String, nullable=True)
    clinic_address: Mapped[str | None] = mapped_column(String, nullable=True)
    room: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_minutes_before: Mapped[int] = mapped_column(Integer, default=30)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_hitl_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hitl_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    doctor: Mapped["DoctorProfile"] = relationship(  # noqa: F821
        "DoctorProfile", back_populates="calendar_events", lazy="select",
        foreign_keys=[doctor_id],
        primaryjoin="CalendarEvent.doctor_id == DoctorProfile.id",
    )
