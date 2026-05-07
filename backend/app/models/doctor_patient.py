"""
app/models/doctor_patient.py
DoctorPatient — assignment + care relationship + diet/suggestions store.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DoctorPatient(Base):
    __tablename__ = "doctor_patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_clinic_name: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_clinic_address: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "discharged", "transferred", name="dp_status_enum"),
        default="active",
    )
    doctor_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_suggestions: Mapped[list] = mapped_column(JSON, default=list)
    diet_plan: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor: Mapped["DoctorProfile"] = relationship(  # noqa: F821
        "DoctorProfile", back_populates="patients", lazy="select",
        foreign_keys=[doctor_id],
        primaryjoin="DoctorPatient.doctor_id == DoctorProfile.id",
    )
    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="doctors", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="DoctorPatient.patient_id == PatientProfile.id",
    )

    __table_args__ = (UniqueConstraint("doctor_id", "patient_id", name="uq_doctor_patient"),)
