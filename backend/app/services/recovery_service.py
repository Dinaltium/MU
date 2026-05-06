"""
app/services/recovery_service.py
Computes the 0-100 recovery score from adherence + symptoms + vitals.
Algorithm exactly as defined in architecture.md section 8.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import MedicationLog
from app.models.recovery import RecoveryScore, SymptomCheckin

logger = logging.getLogger(__name__)


async def compute_recovery_score(patient_id: str, db: AsyncSession) -> RecoveryScore:
    today = date.today()
    now = datetime.utcnow()

    # ── 1. Medication Adherence (max 40 pts) ─────────────────────────────────
    week_ago = now - timedelta(days=7)
    logs_stmt = select(MedicationLog).where(
        and_(
            MedicationLog.patient_id == patient_id,
            MedicationLog.scheduled_at >= week_ago,
        )
    )
    logs_result = await db.execute(logs_stmt)
    logs = logs_result.scalars().all()

    scheduled_count = len(logs)
    taken_count = sum(1 for l in logs if l.is_taken)

    if scheduled_count == 0:
        medication_adherence_score = 20.0  # neutral
    else:
        medication_adherence_score = (taken_count / scheduled_count) * 40

    # ── 2. Symptom Score (max 35 pts) ────────────────────────────────────────
    checkin_stmt = select(SymptomCheckin).where(
        and_(
            SymptomCheckin.patient_id == patient_id,
            SymptomCheckin.checkin_date == today,
        )
    ).order_by(SymptomCheckin.checked_in_at.desc()).limit(1)
    checkin_result = await db.execute(checkin_stmt)
    checkin = checkin_result.scalar_one_or_none()

    if checkin is None:
        symptom_score = 17.5  # neutral
    else:
        base = {"better": 35, "same": 22, "worse": 8}.get(checkin.feel_status, 17)
        penalty = (checkin.severity / 10) * 12 if checkin.severity else 0
        symptom_score = max(0.0, base - penalty)

    # ── 3. Vitals Score (max 25 pts) ─────────────────────────────────────────
    if checkin is None:
        vitals_score = 12.5  # neutral
    else:
        checks: list[bool] = []
        if checkin.temperature_c is not None:
            checks.append(36.1 <= checkin.temperature_c <= 37.2)
        if checkin.heart_rate is not None:
            checks.append(60 <= checkin.heart_rate <= 100)
        if checkin.spo2 is not None:
            checks.append(checkin.spo2 >= 95.0)
        if checkin.bp_systolic is not None:
            checks.append(90 <= checkin.bp_systolic <= 120)

        if not checks:
            vitals_score = 12.5  # neutral
        else:
            vitals_score = (sum(checks) / len(checks)) * 25

    # ── 4. Total score ────────────────────────────────────────────────────────
    total = medication_adherence_score + symptom_score + vitals_score
    total = round(min(100.0, max(0.0, total)), 2)

    # ── 5. Trend ──────────────────────────────────────────────────────────────
    three_days_ago = today - timedelta(days=3)
    prev_stmt = select(RecoveryScore).where(
        and_(
            RecoveryScore.patient_id == patient_id,
            RecoveryScore.score_date >= three_days_ago,
            RecoveryScore.score_date < today,
        )
    )
    prev_result = await db.execute(prev_stmt)
    prev_scores = prev_result.scalars().all()
    avg_3day = sum(s.score for s in prev_scores) / len(prev_scores) if prev_scores else total
    diff = total - avg_3day
    if diff > 5:
        trend = "improving"
    elif diff < -5:
        trend = "declining"
    else:
        trend = "stable"

    # ── 6. Color status ───────────────────────────────────────────────────────
    color_status = "green" if total >= 70 else ("yellow" if total >= 40 else "red")

    # ── 7. Missed doses today ─────────────────────────────────────────────────
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    missed_today_stmt = select(MedicationLog).where(
        and_(
            MedicationLog.patient_id == patient_id,
            MedicationLog.scheduled_at >= today_start,
            MedicationLog.scheduled_at <= today_end,
            MedicationLog.is_missed.is_(True),
        )
    )
    missed_today_res = await db.execute(missed_today_stmt)
    missed_doses_today = len(missed_today_res.scalars().all())

    # ── 8. Consecutive missed days ────────────────────────────────────────────
    consecutive_missed_days = 0
    check_date = today - timedelta(days=1)
    for _ in range(30):
        day_start = datetime.combine(check_date, datetime.min.time())
        day_end = datetime.combine(check_date, datetime.max.time())
        day_missed_stmt = select(MedicationLog).where(
            and_(
                MedicationLog.patient_id == patient_id,
                MedicationLog.scheduled_at >= day_start,
                MedicationLog.scheduled_at <= day_end,
                MedicationLog.is_missed.is_(True),
            )
        )
        day_missed_res = await db.execute(day_missed_stmt)
        if len(day_missed_res.scalars().all()) > 0:
            consecutive_missed_days += 1
            check_date -= timedelta(days=1)
        else:
            break

    # ── 9. Gemini-powered alerts ──────────────────────────────────────────────
    missed_dose_alert: str | None = None
    follow_up_in_days: int | None = None
    follow_up_reason: str | None = None

    try:
        from app.services import gemini_service

        if missed_doses_today > 0:
            from app.models.medication import Medication
            med_stmt = select(Medication).where(
                and_(Medication.patient_id == patient_id, Medication.status == "active")
            ).limit(1)
            med_res = await db.execute(med_stmt)
            med = med_res.scalar_one_or_none()
            disease = med.name if med else "active condition"
            alert_data = await gemini_service.analyze_missed_doses(
                missed_doses_today, consecutive_missed_days, disease, total
            )
            missed_dose_alert = alert_data.get("alert_message", "")

        followup_data = await gemini_service.predict_follow_up(
            disease="active condition",
            score=total,
            trend=trend,
            days_since_diagnosis=0,
        )
        follow_up_in_days = followup_data.get("follow_up_in_days")
        follow_up_reason = followup_data.get("reason")
    except Exception as e:
        logger.warning("Gemini enrichment failed for recovery score: %s", e)

    # ── 10. Upsert recovery score ─────────────────────────────────────────────
    existing_stmt = select(RecoveryScore).where(
        and_(RecoveryScore.patient_id == patient_id, RecoveryScore.score_date == today)
    )
    existing_res = await db.execute(existing_stmt)
    existing = existing_res.scalar_one_or_none()

    if existing:
        existing.score = total
        existing.medication_adherence_score = medication_adherence_score
        existing.symptom_score = symptom_score
        existing.vitals_score = vitals_score
        existing.trend = trend
        existing.color_status = color_status
        existing.missed_doses_today = missed_doses_today
        existing.consecutive_missed_days = consecutive_missed_days
        existing.missed_dose_alert = missed_dose_alert
        existing.follow_up_in_days = follow_up_in_days
        existing.follow_up_reason = follow_up_reason
        existing.computed_at = now
        score_record = existing
    else:
        score_record = RecoveryScore(
            patient_id=patient_id,
            score_date=today,
            score=total,
            medication_adherence_score=medication_adherence_score,
            symptom_score=symptom_score,
            vitals_score=vitals_score,
            trend=trend,
            color_status=color_status,
            missed_doses_today=missed_doses_today,
            consecutive_missed_days=consecutive_missed_days,
            missed_dose_alert=missed_dose_alert,
            follow_up_in_days=follow_up_in_days,
            follow_up_reason=follow_up_reason,
            computed_at=now,
        )
        db.add(score_record)

    await db.flush()

    # ── 11. Critical alert to doctors if red ─────────────────────────────────
    if color_status == "red":
        await _alert_doctors_critical(patient_id, total, trend, db)

    return score_record


async def _alert_doctors_critical(
    patient_id: str,
    score: float,
    trend: str,
    db: AsyncSession,
) -> None:
    try:
        from app.models.doctor_patient import DoctorPatient
        from app.models.patient import PatientProfile
        from app.models.user import User
        from app.services.notification_service import notify_doctor_critical

        dp_stmt = select(DoctorPatient).where(
            and_(DoctorPatient.patient_id == patient_id, DoctorPatient.status == "active")
        )
        dp_res = await db.execute(dp_stmt)
        assignments = dp_res.scalars().all()

        patient_stmt = select(PatientProfile).where(PatientProfile.id == patient_id)
        p_res = await db.execute(patient_stmt)
        patient = p_res.scalar_one_or_none()
        patient_name = patient.full_name if patient else "Patient"

        for dp in assignments:
            doc_stmt = select(User).where(User.id == (
                select(User.id).where(User.id == dp.doctor_id).scalar_subquery()
            ))
            # Get doctor user_id via DoctorProfile
            from app.models.doctor import DoctorProfile
            doc_profile_stmt = select(DoctorProfile).where(DoctorProfile.id == dp.doctor_id)
            doc_profile_res = await db.execute(doc_profile_stmt)
            doc_profile = doc_profile_res.scalar_one_or_none()
            if doc_profile:
                user_stmt = select(User).where(User.id == doc_profile.user_id)
                user_res = await db.execute(user_stmt)
                doc_user = user_res.scalar_one_or_none()
                if doc_user:
                    await notify_doctor_critical(
                        db=db,
                        doctor_user_id=doc_user.id,
                        patient_name=patient_name,
                        message=f"Recovery score is critically low: {score}/100 (trend: {trend}). Immediate review recommended.",
                        metadata={"score": score, "trend": trend, "patient_id": patient_id},
                    )
    except Exception as e:
        logger.error("Failed to alert doctors for critical score: %s", e)
