"""
app/services/report_service.py
Service for generating and managing clinical reports.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.services import gemini_service

async def generate_and_save_report(
    db: AsyncSession,
    doctor_id: str,
    patient_id: str,
    diagnosis_id: str | None,
    state_dict: dict,
    report_type: str = "progress"
) -> Report:
    """
    Calls Gemini to generate a structured report and saves it to the DB.
    """
    # Generate content using Gemini
    report_data = await gemini_service.generate_consultation_report(state_dict)
    
    # Generate patient-friendly version
    patient_name = state_dict.get("patient_name", "Patient")
    patient_friendly = await gemini_service.generate_patient_friendly_report(
        report_data.get("report_content", ""),
        patient_name
    )

    report = Report(
        doctor_id=doctor_id,
        patient_id=patient_id,
        diagnosis_id=diagnosis_id,
        report_type=report_type,
        title=report_data.get("report_title", "Consultation Report"),
        content=report_data.get("report_content", ""),
        patient_friendly_content=patient_friendly,
        treatment_plan=report_data.get("treatment_plan"),
        generated_at=datetime.utcnow()
    )
    
    db.add(report)
    await db.flush()
    return report
