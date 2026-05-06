"""
app/api/routes/admin.py
Admin management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.lab import LabProfile
from app.schemas.schemas import UserListResponse, AuditLogResponse, SuccessResponse
from app.core.security import require_admin

router = APIRouter()

@router.get("/users", response_model=List[UserListResponse])
async def get_all_users(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/labs/{lab_id}/approve", response_model=SuccessResponse)
async def approve_lab(
    lab_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LabProfile).where(LabProfile.id == lab_id)
    result = await db.execute(stmt)
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    lab.is_approved = True
    lab.approved_by = current_user["sub"]
    lab.approved_at = datetime.utcnow()
    
    return {"success": True}
