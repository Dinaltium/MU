"""
app/models/doctor.py
DoctorProfile — one-to-one with User (role=doctor).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    specialization: Mapped[str] = mapped_column(String, nullable=False)
    medical_registration_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hospital_affiliation: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    clinics: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patients: Mapped[list] = relationship("DoctorPatient", back_populates="doctor", lazy="select")
    diagnoses: Mapped[list] = relationship("Diagnosis", back_populates="doctor", lazy="select")
    calendar_events: Mapped[list] = relationship("CalendarEvent", back_populates="doctor", lazy="select")
    lab_orders: Mapped[list] = relationship("LabOrder", back_populates="doctor", lazy="select")
    lab_reports: Mapped[list] = relationship("LabReport", back_populates="doctor", lazy="select")

    def __repr__(self) -> str:
        return f"<DoctorProfile id={self.id} name={self.full_name}>"
