"""
app/models/patient.py
PatientProfile — one-to-one with User (role=patient).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_group: Mapped[str] = mapped_column(String, default="Unknown")
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    chronic_conditions: Mapped[list] = mapped_column(JSON, default=list)
    emergency_contact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctors: Mapped[list] = relationship("DoctorPatient", back_populates="patient", lazy="select")
    diagnoses: Mapped[list] = relationship("Diagnosis", back_populates="patient", lazy="select")
    medications: Mapped[list] = relationship("Medication", back_populates="patient", lazy="select")
    recovery_scores: Mapped[list] = relationship("RecoveryScore", back_populates="patient", lazy="select")
    symptom_checkins: Mapped[list] = relationship("SymptomCheckin", back_populates="patient", lazy="select")
    sos_alerts: Mapped[list] = relationship("SosAlert", back_populates="patient", lazy="select")
    consents: Mapped[list] = relationship("PatientConsent", back_populates="patient", lazy="select")
    lab_orders: Mapped[list] = relationship("LabOrder", back_populates="patient", lazy="select")
    lab_reports: Mapped[list] = relationship("LabReport", foreign_keys="LabReport.patient_id", back_populates="patient", lazy="select")

    def __repr__(self) -> str:
        return f"<PatientProfile id={self.id} name={self.full_name}>"
