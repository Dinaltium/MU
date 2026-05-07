"""
app/models/diagnosis.py
Diagnosis — links doctor, patient, and stores AI pipeline output.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    disease_name: Mapped[str] = mapped_column(String, nullable=False)
    disease_category: Mapped[str | None] = mapped_column(String, nullable=True)
    icd_10_code: Mapped[str | None] = mapped_column(String, nullable=True)
    stage: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(
        Enum("mild", "moderate", "severe", "critical", name="diagnosis_severity_enum"),
        default="mild",
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "improving", "stable", "critical", "discharged", name="diagnosis_status_enum"),
        default="active",
    )
    doctor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_pipeline_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    clinic_name: Mapped[str | None] = mapped_column(String, nullable=True)
    clinic_address: Mapped[str | None] = mapped_column(String, nullable=True)
    diagnosed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor: Mapped["DoctorProfile"] = relationship(  # noqa: F821
        "DoctorProfile", back_populates="diagnoses", lazy="select",
        foreign_keys=[doctor_id],
        primaryjoin="Diagnosis.doctor_id == DoctorProfile.id",
    )
    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="diagnoses", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="Diagnosis.patient_id == PatientProfile.id",
    )
    lab_reports: Mapped[list] = relationship("LabReport", back_populates="diagnosis", lazy="select",
        foreign_keys="LabReport.diagnosis_id")
    medications: Mapped[list] = relationship("Medication", back_populates="diagnosis", lazy="select",
        foreign_keys="Medication.diagnosis_id")
    pipeline_runs: Mapped[list] = relationship("PipelineRun", back_populates="diagnosis", lazy="select",
        foreign_keys="PipelineRun.diagnosis_id")
    lab_orders: Mapped[list] = relationship("LabOrder", back_populates="diagnosis", lazy="select",
        foreign_keys="LabOrder.diagnosis_id")
