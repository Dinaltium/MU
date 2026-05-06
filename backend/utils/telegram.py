"""
utils/telegram.py

WHY TELEGRAM FOR ALERTS:
  Doctors in India commonly use Telegram for hospital communication.
  It's reliable, has read receipts, and its Bot API is simple to
  integrate. Unlike email, Telegram messages are received within
  seconds, which matters for CUSUM treatment-failure alerts.

SECURITY DECISIONS:
  1. Bot token from environment — Telegram tokens grant full control
     of the bot; committing them to Git would allow anyone to send
     messages as the bot.
  2. chat_id lookup from database — we never let the API caller
     specify a Telegram chat ID directly. Only the authenticated
     doctor's verified chat ID (stored at registration) is used.
     This prevents an attacker from redirecting alerts to themselves.
  3. HTTPS-only — httpx uses TLS by default. No plaintext HTTP.
  4. We swallow Telegram errors after logging them — a Telegram
     outage must not break the monitoring pipeline. The DB alert
     record is the primary artefact; Telegram is a notification layer.
"""

import os
import logging
import httpx
from utils.db import get_pool

logger = logging.getLogger(__name__)

TELEGRAM_BASE = "https://api.telegram.org/bot{token}/sendMessage"


async def send_alert(doctor_id: str, patient_name: str, message: str) -> None:
    """
    Send a Telegram message to the doctor identified by doctor_id.

    The doctor's Telegram handle is resolved from the database — the
    caller never supplies it directly, preventing handle spoofing.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping notification")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT telegram_handle FROM users WHERE id = $1::uuid",
            doctor_id,
        )

    if not row or not row["telegram_handle"]:
        logger.info("No Telegram handle for doctor %s — skipping", doctor_id)
        return

    text = (
        f"🚨 *RxBridge Alert*\n"
        f"Patient: *{patient_name}*\n"
        f"{message}"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                TELEGRAM_BASE.format(token=token),
                json={
                    "chat_id": row["telegram_handle"],
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )
            resp.raise_for_status()
    except Exception as exc:
        # Non-fatal — the DB alert is the source of truth
        logger.error("Telegram send failed for doctor %s: %s", doctor_id, exc)
