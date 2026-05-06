"""
app/services/notification_service.py
Creates Notification rows + optionally pushes via WebSocket.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    recipient_user_id: str,
    notification_type: str,
    title: str,
    message: str,
    sender_user_id: str | None = None,
    priority: str = "normal",
    metadata: dict | None = None,
    push_ws: bool = True,
) -> Notification:
    """
    Persist notification to DB and optionally push to WebSocket.
    notification_type values: missed_dose | critical_alert | follow_up_reminder |
    report_ready | lab_report_ready | lab_order_created | appointment_reminder |
    recovery_update | doctor_note | sos_accepted | sos_rejected | consent_granted |
    consent_revoked | hitl_required
    """
    notif = Notification(
        recipient_user_id=recipient_user_id,
        sender_user_id=sender_user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        metadata_=metadata or {},
        priority=priority,
        created_at=datetime.utcnow(),
    )
    db.add(notif)
    await db.flush()  # Get the ID before commit

    if push_ws:
        try:
            from app.api.websocket import manager  # avoid circular at module load
            await manager.send_to_user(recipient_user_id, {
                "type": "notification",
                "id": notif.id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
            })
        except Exception:
            pass  # WebSocket push is best-effort; DB record always written

    return notif


async def notify_doctor_critical(
    db: AsyncSession,
    doctor_user_id: str,
    patient_name: str,
    message: str,
    metadata: dict | None = None,
) -> None:
    await create_notification(
        db=db,
        recipient_user_id=doctor_user_id,
        notification_type="critical_alert",
        title=f"⚠️ Critical Alert — {patient_name}",
        message=message,
        priority="critical",
        metadata=metadata,
    )


async def notify_patient_report_ready(
    db: AsyncSession,
    patient_user_id: str,
    report_title: str,
) -> None:
    await create_notification(
        db=db,
        recipient_user_id=patient_user_id,
        notification_type="report_ready",
        title="Your medical report is ready",
        message=f"Dr. has generated a new report: {report_title}",
        priority="normal",
    )


async def notify_consent_granted(
    db: AsyncSession,
    patient_user_id: str,
    doctor_name: str,
) -> None:
    await create_notification(
        db=db,
        recipient_user_id=patient_user_id,
        notification_type="consent_granted",
        title="Doctor assigned",
        message=f"Dr. {doctor_name} has been assigned to your care. Your consent was auto-granted. You can revoke it anytime.",
        priority="normal",
    )


async def notify_lab_order_created(
    db: AsyncSession,
    patient_user_id: str,
    order_code: str,
    tests: list[str],
) -> None:
    await create_notification(
        db=db,
        recipient_user_id=patient_user_id,
        notification_type="lab_order_created",
        title="Lab tests ordered",
        message=f"Your doctor ordered lab tests. Show code {order_code} at any approved lab. Tests: {', '.join(tests)}",
        priority="normal",
        metadata={"order_code": order_code},
    )


async def notify_lab_report_ready(
    db: AsyncSession,
    doctor_user_id: str,
    patient_user_id: str,
    report_title: str,
) -> None:
    for uid in [doctor_user_id, patient_user_id]:
        await create_notification(
            db=db,
            recipient_user_id=uid,
            notification_type="lab_report_ready",
            title="Lab report submitted",
            message=f"Lab report available: {report_title}",
            priority="high",
        )


async def notify_hitl_required(
    db: AsyncSession,
    doctor_user_id: str,
    run_id: str,
    reason: str,
) -> None:
    await create_notification(
        db=db,
        recipient_user_id=doctor_user_id,
        notification_type="hitl_required",
        title="🛑 Pipeline paused — Your approval required",
        message=f"The AI pipeline has paused and requires your review: {reason}",
        priority="critical",
        metadata={"run_id": run_id},
    )
