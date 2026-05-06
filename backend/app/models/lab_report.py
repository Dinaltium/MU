"""
app/models/lab_report.py
LabReport — immutable after submission. Amendments create new rows.
SHA256 hash set once on INSERT — never updated.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_order_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    lab_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    diagnosis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    report_title: Mapped[str] = mapped_column(String, nullable=False)
    report_type: Mapped[str] = mapped_column(String, nullable=False)  # CBC|LFT|RFT|culture|imaging|biopsy|other
    raw_report_data: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    report_hash: Mapped[str] = mapped_column(String, nullable=False)  # SHA256 — SET ONCE, NEVER UPDATE
    report_pdf_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("submitted", "verified", "rejected", name="lab_report_status_enum"),
        default="submitted",
    )
    lab_technician_name: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_amended: Mapped[bool] = mapped_column(Boolean, default=False)
    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_version_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    lab: Mapped["LabProfile"] = relationship(  # noqa: F821
        "LabProfile", back_populates="reports", lazy="select",
        foreign_keys=[lab_id],
        primaryjoin="LabReport.lab_id == LabProfile.id",
    )
    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="lab_reports", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="LabReport.patient_id == PatientProfile.id",
    )
    diagnosis: Mapped["Diagnosis"] = relationship(  # noqa: F821
        "Diagnosis", back_populates="lab_reports", lazy="select",
        foreign_keys=[diagnosis_id],
        primaryjoin="LabReport.diagnosis_id == Diagnosis.id",
    )
    lab_order: Mapped["LabOrder"] = relationship(  # noqa: F821
        "LabOrder", back_populates="lab_report", lazy="select",
        foreign_keys=[lab_order_id],
        primaryjoin="LabReport.lab_order_id == LabOrder.id",
    )
