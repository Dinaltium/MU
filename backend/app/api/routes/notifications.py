"""
app/api/routes/notifications.py
Notification management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.notification import Notification
from app.schemas.schemas import NotificationResponse, SuccessResponse
from app.core.security import require_any_role

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: dict = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.recipient_user_id == current_user["sub"]
    ).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_as_read(
    current_user: dict = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    stmt = update(Notification).where(
        Notification.recipient_user_id == current_user["sub"],
        Notification.is_read == False
    ).values(is_read=True, read_at=datetime.utcnow())
    await db.execute(stmt)
    return {"success": True}
