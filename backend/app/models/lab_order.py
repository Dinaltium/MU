"""
app/models/lab_order.py
LabOrder — three-party flow: doctor orders → patient initiates at lab → lab submits.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    lab_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    diagnosis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    order_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    tests_requested: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        Enum("routine", "urgent", "stat", name="lab_order_priority_enum"), default="routine"
    )
    status: Mapped[str] = mapped_column(
        Enum("ordered", "patient_initiated", "in_progress", "submitted", "verified", "cancelled",
             name="lab_order_status_enum"),
        default="ordered",
    )
    ordered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient_initiated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    doctor: Mapped["DoctorProfile"] = relationship(  # noqa: F821
        "DoctorProfile", back_populates="lab_orders", lazy="select",
        foreign_keys=[doctor_id],
        primaryjoin="LabOrder.doctor_id == DoctorProfile.id",
    )
    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="lab_orders", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="LabOrder.patient_id == PatientProfile.id",
    )
    lab: Mapped["LabProfile"] = relationship(  # noqa: F821
        "LabProfile", back_populates="orders", lazy="select",
        foreign_keys=[lab_id],
        primaryjoin="LabOrder.lab_id == LabProfile.id",
    )
    diagnosis: Mapped["Diagnosis"] = relationship(  # noqa: F821
        "Diagnosis", back_populates="lab_orders", lazy="select",
        foreign_keys=[diagnosis_id],
        primaryjoin="LabOrder.diagnosis_id == Diagnosis.id",
    )
    lab_report: Mapped["LabReport"] = relationship(  # noqa: F821
        "LabReport", back_populates="lab_order", lazy="select",
        foreign_keys="LabReport.lab_order_id",
    )
