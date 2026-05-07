"""
app/models/sos_alert.py
SOS alerts — patient-triggered emergency broadcast to assigned doctors.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SosAlert(Base):
    __tablename__ = "sos_alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "accepted", "rejected", "resolved", name="sos_status_enum"),
        default="pending",
    )
    responded_by_doctor_id: Mapped[str | None] = mapped_column(String, ForeignKey("doctor_profiles.id"), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="sos_alerts", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="SosAlert.patient_id == PatientProfile.id",
    )
