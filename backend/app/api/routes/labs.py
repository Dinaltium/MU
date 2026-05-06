"""
app/api/routes/labs.py
Lab-specific routes.
"""
from __future__ import annotations

import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.lab import LabProfile
from app.models.lab_order import LabOrder
from app.models.lab_report import LabReport
from app.schemas.schemas import LabProfileResponse, LabReportCreate, LabReportResponse, LabOrderResponse, AmendReportRequest
from app.core.security import require_lab
from app.services.audit_service import log_action, AuditAction
from app.services.notification_service import notify_lab_report_ready

router = APIRouter()

@router.get("/me", response_model=LabProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(require_lab),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LabProfile).where(LabProfile.user_id == current_user["sub"])
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    return profile

@router.get("/active-orders", response_model=List[LabOrderResponse])
async def get_active_orders(
    current_user: dict = Depends(require_lab),
    db: AsyncSession = Depends(get_db)
):
    l_stmt = select(LabProfile.id).where(LabProfile.user_id == current_user["sub"])
    l_res = await db.execute(l_stmt)
    lab_id = l_res.scalar_one_or_none()

    # Labs see orders where lab_id is either NULL (unassigned) or assigned to them
    stmt = select(LabOrder).where(
        (LabOrder.lab_id == lab_id) | (LabOrder.lab_id.is_(None)),
        LabOrder.status.in_(["ordered", "patient_initiated", "in_progress"])
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/submit-report", response_model=LabReportResponse)
async def submit_report(
    request: Request,
    data: LabReportCreate,
    current_user: dict = Depends(require_lab),
    db: AsyncSession = Depends(get_db)
):
    l_stmt = select(LabProfile.id).where(LabProfile.user_id == current_user["sub"])
    l_res = await db.execute(l_stmt)
    lab_id = l_res.scalar_one_or_none()

    # 1. Verify order
    o_stmt = select(LabOrder).where(LabOrder.id == data.lab_order_id)
    o_res = await db.execute(o_stmt)
    order = o_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Create hash
    report_content = json.dumps(data.raw_report_data, sort_keys=True)
    report_hash = hashlib.sha256(report_content.encode()).hexdigest()

    # 3. Create report
    report = LabReport(
        lab_order_id=order.id,
        lab_id=lab_id,
        patient_id=order.patient_id,
        doctor_id=order.doctor_id,
        diagnosis_id=data.diagnosis_id or order.diagnosis_id,
        report_title=data.report_title,
        report_type=data.report_type,
        raw_report_data=data.raw_report_data,
        report_hash=report_hash,
        report_pdf_url=data.report_pdf_url,
        status="submitted",
        lab_technician_name=data.lab_technician_name
    )
    db.add(report)

    # 4. Update order
    order.status = "submitted"
    order.lab_id = lab_id
    order.submitted_at = report.submitted_at

    await log_action(db, current_user["sub"], "lab", AuditAction.LAB_SUBMIT, "lab_report", report.id, order.patient_id, request, True)
    
    # 5. Notify doctor and patient
    # We need doctor user_id and patient user_id
    from app.models.doctor import DoctorProfile
    from app.models.patient import PatientProfile
    
    d_stmt = select(DoctorProfile.user_id).where(DoctorProfile.id == order.doctor_id)
    d_res = await db.execute(d_stmt)
    doctor_uid = d_res.scalar_one_or_none()
    
    p_stmt = select(PatientProfile.user_id).where(PatientProfile.id == order.patient_id)
    p_res = await db.execute(p_stmt)
    patient_uid = p_res.scalar_one_or_none()
    
    await notify_lab_report_ready(db, doctor_uid, patient_uid, report.report_title)

    return report
