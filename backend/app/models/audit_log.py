"""
app/models/audit_log.py
APPEND-ONLY audit trail. Application NEVER calls UPDATE or DELETE on this table.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    user_agent: Mapped[str] = mapped_column(String, default="")
    request_path: Mapped[str] = mapped_column(String, default="")
    request_method: Mapped[str] = mapped_column(String, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_actor", "actor_user_id"),
        Index("ix_audit_logs_patient", "patient_id"),
    )
