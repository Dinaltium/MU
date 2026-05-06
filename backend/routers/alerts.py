"""
routers/alerts.py

Alerts are surfaced to doctors and patients.
Security: users can only read their own alerts.
"""

import logging
from fastapi import APIRouter, Depends, Query
from utils.db import get_pool
from utils.security import get_current_user

router = APIRouter(tags=["alerts"])
logger = logging.getLogger(__name__)


@router.get("/")
async def list_alerts(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    """
    Return alerts for the currently authenticated user only.

    SECURITY:
      The query filters by target_id = user["sub"] — the authenticated
      user's own ID extracted from the JWT. The client cannot pass a
      different user ID to read someone else's alerts.
    """
    pool = await get_pool()
    query = """
        SELECT id, alert_type, severity, message, read, created_at
        FROM alerts
        WHERE target_id = $1::uuid
    """
    params = [user["sub"]]

    if unread_only:
        query += " AND read = FALSE"

    query += " ORDER BY created_at DESC LIMIT $2"
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


@router.post("/{alert_id}/read")
async def mark_read(
    alert_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Mark an alert as read.
    The UPDATE WHERE clause includes target_id to prevent a user from
    marking another user's alert as read (IDOR prevention).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE alerts SET read=TRUE WHERE id=$1::uuid AND target_id=$2::uuid",
            alert_id, user["sub"]
        )
    # asyncpg returns 'UPDATE N' — if N=0 the alert didn't belong to this user
    updated = int(result.split()[-1])
    return {"updated": updated > 0}
