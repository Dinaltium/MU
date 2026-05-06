"""
app/api/routes/reports.py
Clinical report management routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.database import get_db
from app.models.report import Report
from app.models.doctor import DoctorProfile
from app.models.patient import PatientProfile
from app.schemas.schemas import ReportResponse, ReportCreate
from app.core.security import require_doctor, require_any_role
from app.core.consent_gate import assert_consent
from app.services.audit_service import log_action, AuditAction

router = APIRouter()

@router.post("/", response_model=ReportResponse)
async def create_report(
    request: Request,
    data: ReportCreate,
    current_user: dict = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
    d_res = await db.execute(d_stmt)
    doctor_id = d_res.scalar_one_or_none()

    await assert_consent(doctor_id, data.patient_id, "read_reports", db)

    report = Report(
        doctor_id=doctor_id,
        patient_id=data.patient_id,
        diagnosis_id=data.diagnosis_id,
        report_type=data.report_type,
        title=data.title,
        content=data.content,
        patient_friendly_content=data.patient_friendly_content,
        treatment_plan=data.treatment_plan,
        clinic_name=data.clinic_name,
        clinic_address=data.clinic_address,
        is_shared_with_patient=data.is_shared_with_patient
    )
    db.add(report)
    await db.flush()

    await log_action(db, current_user["sub"], "doctor", AuditAction.CREATE, "report", report.id, data.patient_id, request, True)
    return report

@router.get("/patient/{patient_id}", response_model=List[ReportResponse])
async def get_patient_reports(
    patient_id: str,
    current_user: dict = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    if current_user["role"] == "doctor":
        d_stmt = select(DoctorProfile.id).where(DoctorProfile.user_id == current_user["sub"])
        d_res = await db.execute(d_stmt)
        doctor_id = d_res.scalar_one_or_none()
        await assert_consent(doctor_id, patient_id, "read_reports", db)
    elif current_user["role"] == "patient":
        p_stmt = select(PatientProfile.id).where(PatientProfile.user_id == current_user["sub"])
        p_res = await db.execute(p_stmt)
        my_patient_id = p_res.scalar_one_or_none()
        if my_patient_id != patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    stmt = select(Report).where(
        Report.patient_id == patient_id
    )
    # Patients only see reports shared with them
    if current_user["role"] == "patient":
        stmt = stmt.where(Report.is_shared_with_patient == True)
        
    stmt = stmt.order_by(Report.generated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
