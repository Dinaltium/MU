"""
app/models/medication.py
Medication + MedicationLog tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    diagnosis_id: Mapped[str | None] = mapped_column(String, ForeignKey("diagnoses.id"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dosage: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)
    route: Mapped[str] = mapped_column(String, default="oral")
    schedule_times: Mapped[list] = mapped_column(JSON, default=list)  # ["08:00", "20:00"]
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "completed", "stopped", "paused", name="medication_status_enum"),
        default="active",
    )
    prescribed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="medications", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="Medication.patient_id == PatientProfile.id",
    )
    diagnosis: Mapped["Diagnosis"] = relationship(  # noqa: F821
        "Diagnosis", back_populates="medications", lazy="select",
        foreign_keys=[diagnosis_id],
        primaryjoin="Medication.diagnosis_id == Diagnosis.id",
    )
    logs: Mapped[list] = relationship(
        "MedicationLog", back_populates="medication",
        cascade="all, delete-orphan", lazy="select",
    )


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    medication_id: Mapped[str] = mapped_column(String, ForeignKey("medications.id"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_taken: Mapped[bool] = mapped_column(Boolean, default=False)
    is_missed: Mapped[bool] = mapped_column(Boolean, default=False)
    patient_note: Mapped[str | None] = mapped_column(String, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    medication: Mapped["Medication"] = relationship(
        "Medication", back_populates="logs", lazy="select",
        foreign_keys=[medication_id],
        primaryjoin="MedicationLog.medication_id == Medication.id",
    )
