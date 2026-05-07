"""
app/models/consent.py
PatientConsent — auto-created on DoctorPatient insert; patient can revoke.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

DEFAULT_SCOPE = ["read_diagnoses", "read_labs", "read_medications", "read_reports", "read_recovery"]


class PatientConsent(Base):
    __tablename__ = "patient_consents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_scope: Mapped[list] = mapped_column(JSON, default=lambda: list(DEFAULT_SCOPE))
    purpose: Mapped[str] = mapped_column(String, default="treatment")
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_granted: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="consents", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="PatientConsent.patient_id == PatientProfile.id",
    )

    __table_args__ = (UniqueConstraint("patient_id", "doctor_id", name="uq_consent"),)
