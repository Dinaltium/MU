"""
app/models/recovery.py
SymptomCheckin + RecoveryScore — recovery tracking and monitoring.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SymptomCheckin(Base):
    __tablename__ = "symptom_checkins"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    checkin_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    feel_status: Mapped[str] = mapped_column(
        Enum("better", "same", "worse", name="feel_status_enum"), nullable=False
    )
    symptoms_present: Mapped[list] = mapped_column(JSON, default=list)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    bp_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_glucose: Mapped[float | None] = mapped_column(Float, nullable=True)
    patient_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="symptom_checkins", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="SymptomCheckin.patient_id == PatientProfile.id",
    )


class RecoveryScore(Base):
    __tablename__ = "recovery_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    score_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)           # 0-100
    medication_adherence_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-40
    symptom_score: Mapped[float | None] = mapped_column(Float, nullable=True)               # 0-35
    vitals_score: Mapped[float | None] = mapped_column(Float, nullable=True)                # 0-25
    trend: Mapped[str] = mapped_column(
        Enum("improving", "stable", "declining", name="recovery_trend_enum"), default="stable"
    )
    color_status: Mapped[str] = mapped_column(
        Enum("green", "yellow", "red", name="recovery_color_enum"), default="yellow"
    )
    missed_doses_today: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_missed_days: Mapped[int] = mapped_column(Integer, default=0)
    missed_dose_alert: Mapped[str | None] = mapped_column(String, nullable=True)
    follow_up_in_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    follow_up_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["PatientProfile"] = relationship(  # noqa: F821
        "PatientProfile", back_populates="recovery_scores", lazy="select",
        foreign_keys=[patient_id],
        primaryjoin="RecoveryScore.patient_id == PatientProfile.id",
    )

    __table_args__ = (UniqueConstraint("patient_id", "score_date", name="uq_recovery_score_date"),)
