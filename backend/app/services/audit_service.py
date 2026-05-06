"""
app/services/audit_service.py
Append-only audit logging. Never UPDATE or DELETE audit_logs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    actor_user_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    patient_id: str | None,
    request: Request,
    success: bool,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Append an immutable audit record.
    Called from route handlers — do NOT call commit here (get_db handles it).
    """
    log = AuditLog(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        patient_id=patient_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        request_path=str(request.url.path),
        request_method=request.method,
        metadata_=metadata or {},
        success=success,
        timestamp=datetime.utcnow(),
    )
    db.add(log)


# Action constants
class AuditAction:
    VIEW = "VIEW"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    CONSENT_GRANT = "CONSENT_GRANT"
    CONSENT_REVOKE = "CONSENT_REVOKE"
    SOS_TRIGGER = "SOS_TRIGGER"
    SOS_RESPOND = "SOS_RESPOND"
    PIPELINE_RUN = "PIPELINE_RUN"
    PIPELINE_APPROVE = "PIPELINE_APPROVE"
    LAB_SUBMIT = "LAB_SUBMIT"
    LAB_AMEND = "LAB_AMEND"
    LAB_ORDER_CREATE = "LAB_ORDER_CREATE"
    LAB_INITIATE = "LAB_INITIATE"
