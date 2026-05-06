"""
app/models/notification.py
In-app notifications — real-time delivery via WebSocket + DB persistence.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    sender_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notification_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    priority: Mapped[str] = mapped_column(
        Enum("low", "normal", "high", "critical", name="notification_priority_enum"),
        default="normal",
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    recipient: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="notifications",
        foreign_keys=[recipient_user_id],
        primaryjoin="Notification.recipient_user_id == User.id",
        lazy="select",
    )
