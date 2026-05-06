"""
app/core/consent_gate.py
Consent gate — every doctor→patient data access MUST call assert_consent().
Raises 403 (not 404) to prevent patient enumeration.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def assert_consent(
    doctor_id: str,
    patient_id: str,
    scope: str,
    db: AsyncSession,
    purpose: str = "treatment",
) -> None:
    """
    Verifies an active PatientConsent exists for this doctor-patient pair
    and that the requested scope is included.
    Always logs the access check to audit_logs (handled by caller).
    Break-the-glass: purpose='emergency' bypasses scope check.
    """
    # Import here to avoid circular dependency at module load
    from app.models.consent import PatientConsent

    stmt = select(PatientConsent).where(
        PatientConsent.doctor_id == doctor_id,
        PatientConsent.patient_id == patient_id,
        PatientConsent.is_active.is_(True),
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()

    if consent is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient consent required — no active consent found",
        )

    # Emergency break-the-glass bypasses scope check
    if purpose == "emergency":
        return

    if scope not in (consent.consent_scope or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Consent scope '{scope}' not granted by patient",
        )


async def get_consent(
    doctor_id: str,
    patient_id: str,
    db: AsyncSession,
):
    """Return consent row or None — for read-only checks."""
    from app.models.consent import PatientConsent

    stmt = select(PatientConsent).where(
        PatientConsent.doctor_id == doctor_id,
        PatientConsent.patient_id == patient_id,
        PatientConsent.is_active.is_(True),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
