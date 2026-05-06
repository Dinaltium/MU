"""
app/models/__init__.py
Imports all models so SQLAlchemy registers them with Base.metadata.
Required for init_db() to create all tables correctly.
"""
from app.models.user import User  # noqa: F401
from app.models.patient import PatientProfile  # noqa: F401
from app.models.doctor import DoctorProfile  # noqa: F401
from app.models.lab import LabProfile  # noqa: F401
from app.models.doctor_patient import DoctorPatient  # noqa: F401
from app.models.consent import PatientConsent  # noqa: F401
from app.models.diagnosis import Diagnosis  # noqa: F401
from app.models.lab_order import LabOrder  # noqa: F401
from app.models.lab_report import LabReport  # noqa: F401
from app.models.medication import Medication, MedicationLog  # noqa: F401
from app.models.recovery import SymptomCheckin, RecoveryScore  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
from app.models.sos_alert import SosAlert  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.pipeline_run import PipelineRun  # noqa: F401

__all__ = [
    "User",
    "PatientProfile",
    "DoctorProfile",
    "LabProfile",
    "DoctorPatient",
    "PatientConsent",
    "Diagnosis",
    "LabOrder",
    "LabReport",
    "Medication",
    "MedicationLog",
    "SymptomCheckin",
    "RecoveryScore",
    "Report",
    "CalendarEvent",
    "SosAlert",
    "Notification",
    "AuditLog",
    "PipelineRun",
]
