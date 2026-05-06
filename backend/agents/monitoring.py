"""
agents/monitoring.py

WHY CUSUM (Cumulative Sum Control Chart):
  CUSUM is a statistical process control method designed to detect
  PERSISTENT SHIFTS in a metric, not just single outliers.

  In clinical context: a patient who consistently scores 40/100 on
  recovery for 5 days is more concerning than one who had a single
  bad day at 30/100. CUSUM accumulates deviation from the expected
  trajectory — it fires when the cumulative drift exceeds a threshold.

  This is far more clinically meaningful than a simple "score < X"
  alert that would flood doctors with noise.

SECURITY NOTE:
  • The monitoring loop runs on a server-side schedule (every 6 hours).
    No client can trigger it via an API call, preventing DoS via
    computation exhaustion.
  • Alert records are created with target_id = doctor_id — only that
    doctor can read the alert. The patient's name in the alert message
    is acceptable (the doctor treats that patient), but the alert does
    not contain the patient's full clinical record.
  • Telegram notifications are fire-and-forget after the DB record is
    created. A Telegram failure does not roll back the DB alert.
"""

import asyncio
import logging
from models.cusum import CUSUMMonitor
from utils.db import get_pool
from utils.telegram import send_alert

logger = logging.getLogger(__name__)

_monitor = CUSUMMonitor(target=70, slack=5, threshold=10)


async def run_monitoring_cycle() -> None:
    """
    Scan all active consultations and compute CUSUM on check-in history.
    Fire alerts for consultations showing persistent deterioration.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        active = await conn.fetch(
            """
            SELECT c.id, c.patient_id, c.doctor_id, p.name AS patient_name
            FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            WHERE c.status = 'complete'
              AND c.created_at > NOW() - INTERVAL '14 days'
            """
        )

        for consultation in active:
            checkins = await conn.fetch(
                """
                SELECT recovery_score, created_at
                FROM monitoring_checkins
                WHERE consultation_id = $1::uuid
                ORDER BY created_at ASC
                """,
                consultation["id"],
            )

            if len(checkins) < 2:
                continue

            scores = [c["recovery_score"] for c in checkins]
            result = _monitor.update(scores)

            # Update CUSUM value on most recent check-in
            await conn.execute(
                """
                UPDATE monitoring_checkins
                SET cusum_value = $1
                WHERE consultation_id = $2::uuid
                  AND created_at = (
                      SELECT MAX(created_at)
                      FROM monitoring_checkins
                      WHERE consultation_id = $2::uuid
                  )
                """,
                result["cusum_value"],
                consultation["id"],
            )

            if result["alert"]:
                logger.warning(
                    "CUSUM alert for consultation %s — %s",
                    consultation["id"],
                    result["message"],
                )
                # Insert DB alert first (primary record)
                await conn.execute(
                    """
                    INSERT INTO alerts
                    (target_id, target_type, alert_type, severity, message)
                    VALUES ($1::uuid, 'doctor', 'treatment_failure', 'HIGH', $2)
                    """,
                    consultation["doctor_id"],
                    f"Patient {consultation['patient_name']}: {result['message']}",
                )

                # Telegram notification (secondary, non-blocking)
                await send_alert(
                    str(consultation["doctor_id"]),
                    consultation["patient_name"],
                    result["message"],
                )


async def start_monitoring() -> None:
    """
    Background task — runs every 6 hours indefinitely.
    Errors in a single cycle are logged but do not stop the loop.
    """
    while True:
        try:
            await run_monitoring_cycle()
        except Exception as exc:
            logger.exception("Monitoring cycle failed: %s", exc)
        await asyncio.sleep(21_600)  # 6 hours
