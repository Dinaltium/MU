"""
app/models/pipeline_run.py
Stores each AI pipeline execution — supports HITL pause/resume.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    diagnosis_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trigger_reason: Mapped[str] = mapped_column(String, nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    agent_outputs: Mapped[list] = mapped_column(JSON, default=list)
    final_recommendation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pipeline_status: Mapped[str] = mapped_column(
        Enum("running", "hitl_pending", "complete", "failed", name="pipeline_status_enum"),
        default="running",
    )
    hitl_required: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    hitl_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hitl_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pipeline_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    diagnosis: Mapped["Diagnosis"] = relationship(  # noqa: F821
        "Diagnosis", back_populates="pipeline_runs", lazy="select",
        foreign_keys=[diagnosis_id],
        primaryjoin="PipelineRun.diagnosis_id == Diagnosis.id",
    )
