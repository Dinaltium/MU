"""
app/schemas/schemas.py
All Pydantic v2 schemas. ConfigDict(from_attributes=True) on every response schema.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# SHARED
# ─────────────────────────────────────────────────────────────────────────────
class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(patient|doctor|lab)$")
    full_name: str = Field(min_length=2)
    # Patient-specific
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    blood_group: Optional[str] = "Unknown"
    phone: Optional[str] = None
    address: Optional[str] = None
    # Doctor-specific
    specialization: Optional[str] = None
    medical_registration_number: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    # Lab-specific
    lab_registration_id: Optional[str] = None
    lab_address: Optional[str] = None
    lab_city: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    profile_id: str
    full_name: str


class UserMeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    profile_id: str
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────────────────────────────────────────
# PATIENT
# ─────────────────────────────────────────────────────────────────────────────
class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    blood_group: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact: Optional[dict] = None


class PatientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    weight_kg: Optional[float]
    height_cm: Optional[float]
    blood_group: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    allergies: List[Any] = []
    chronic_conditions: List[Any] = []
    emergency_contact: Optional[dict]
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# DOCTOR
# ─────────────────────────────────────────────────────────────────────────────
class ClinicInfo(BaseModel):
    name: str
    address: str
    city: str
    phone: Optional[str] = None


class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    phone: Optional[str] = None
    clinics: Optional[List[dict]] = None


class DoctorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    specialization: str
    medical_registration_number: str
    hospital_affiliation: str
    phone: Optional[str]
    clinics: List[Any] = []
    created_at: datetime
    updated_at: datetime


class AssignPatientRequest(BaseModel):
    patient_email: EmailStr
    assigned_clinic_name: Optional[str] = None
    assigned_clinic_address: Optional[str] = None


class DoctorSummaryUpdate(BaseModel):
    doctor_summary: str


class DietPlanUpdate(BaseModel):
    diet_plan: List[dict]


class SuggestionsUpdate(BaseModel):
    improvement_suggestions: List[str]


class PatientStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|discharged|transferred)$")


# ─────────────────────────────────────────────────────────────────────────────
# LAB
# ─────────────────────────────────────────────────────────────────────────────
class LabProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    lab_name: str
    registration_id: str
    address: str
    city: str
    phone: Optional[str]
    is_approved: bool
    created_at: datetime


class LabReportCreate(BaseModel):
    lab_order_id: str
    report_title: str
    report_type: str
    raw_report_data: List[dict]  # [{test_name, result_value, unit, reference_range, is_abnormal}]
    lab_technician_name: str
    report_pdf_url: Optional[str] = None
    diagnosis_id: Optional[str] = None


class LabReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lab_order_id: str
    lab_id: str
    patient_id: str
    doctor_id: str
    report_title: str
    report_type: str
    raw_report_data: List[Any]
    report_hash: str
    status: str
    lab_technician_name: str
    submitted_at: datetime
    is_amended: bool
    amendment_reason: Optional[str]
    previous_version_id: Optional[str]


class AmendReportRequest(BaseModel):
    amendment_reason: str
    raw_report_data: List[dict]
    lab_technician_name: str


# ─────────────────────────────────────────────────────────────────────────────
# LAB ORDER
# ─────────────────────────────────────────────────────────────────────────────
class LabOrderCreate(BaseModel):
    patient_id: str
    diagnosis_id: Optional[str] = None
    tests_requested: List[dict]  # [{test_name, purpose, urgency}]
    clinical_notes: Optional[str] = None
    priority: str = "routine"


class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    lab_id: Optional[str]
    diagnosis_id: Optional[str]
    order_code: str
    tests_requested: List[Any]
    clinical_notes: Optional[str]
    priority: str
    status: str
    ordered_at: datetime
    expires_at: Optional[datetime]


# ─────────────────────────────────────────────────────────────────────────────
# CONSENT
# ─────────────────────────────────────────────────────────────────────────────
class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    is_active: bool
    consent_scope: List[str]
    purpose: str
    granted_at: datetime
    revoked_at: Optional[datetime]
    auto_granted: bool


class ConsentRevokeRequest(BaseModel):
    reason: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# DIAGNOSIS
# ─────────────────────────────────────────────────────────────────────────────
class DiagnosisCreate(BaseModel):
    patient_id: str
    disease_name: str
    disease_category: Optional[str] = None
    icd_10_code: Optional[str] = None
    stage: Optional[str] = None
    severity: str = "mild"
    doctor_notes: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None


class DiagnosisUpdate(BaseModel):
    disease_name: Optional[str] = None
    stage: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    doctor_notes: Optional[str] = None
    icd_10_code: Optional[str] = None


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    disease_name: str
    disease_category: Optional[str]
    icd_10_code: Optional[str]
    stage: Optional[str]
    severity: str
    status: str
    doctor_notes: Optional[str]
    ai_pipeline_output: Optional[dict]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    diagnosed_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# MEDICATION
# ─────────────────────────────────────────────────────────────────────────────
class MedicationCreate(BaseModel):
    patient_id: str
    diagnosis_id: Optional[str] = None
    name: str
    dosage: str
    frequency: str
    route: str = "oral"
    schedule_times: List[str] = []
    instructions: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[int] = None


class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    schedule_times: Optional[List[str]] = None
    instructions: Optional[str] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    diagnosis_id: Optional[str]
    name: str
    dosage: str
    frequency: str
    route: str
    schedule_times: List[Any]
    instructions: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    duration_days: Optional[int]
    status: str
    prescribed_at: datetime


class MedicationLogUpdate(BaseModel):
    medication_id: str
    scheduled_at: datetime
    is_taken: bool
    taken_at: Optional[datetime] = None
    patient_note: Optional[str] = None


class MedicationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    medication_id: str
    patient_id: str
    scheduled_at: datetime
    taken_at: Optional[datetime]
    is_taken: bool
    is_missed: bool
    patient_note: Optional[str]
    logged_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# RECOVERY
# ─────────────────────────────────────────────────────────────────────────────
class SymptomCheckinCreate(BaseModel):
    feel_status: str = Field(pattern="^(better|same|worse)$")
    symptoms_present: List[str] = []
    severity: Optional[int] = Field(None, ge=1, le=10)
    temperature_c: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    blood_glucose: Optional[float] = None
    patient_note: Optional[str] = None


class RecoveryScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    score_date: date
    score: float
    medication_adherence_score: Optional[float]
    symptom_score: Optional[float]
    vitals_score: Optional[float]
    trend: str
    color_status: str
    missed_doses_today: int
    consecutive_missed_days: int
    missed_dose_alert: Optional[str]
    follow_up_in_days: Optional[int]
    follow_up_reason: Optional[str]
    computed_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────
class ReportCreate(BaseModel):
    patient_id: str
    diagnosis_id: Optional[str] = None
    report_type: str
    title: str
    content: str
    patient_friendly_content: Optional[str] = None
    treatment_plan: Optional[dict] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    is_shared_with_patient: bool = True


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    diagnosis_id: Optional[str]
    report_type: str
    title: str
    content: str
    patient_friendly_content: Optional[str]
    treatment_plan: Optional[dict]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    is_shared_with_patient: bool
    generated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR
# ─────────────────────────────────────────────────────────────────────────────
class CalendarEventCreate(BaseModel):
    patient_id: Optional[str] = None
    title: str
    event_type: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    room: Optional[str] = None
    notes: Optional[str] = None
    reminder_minutes_before: int = 30


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    clinic_name: Optional[str] = None
    room: Optional[str] = None
    notes: Optional[str] = None
    is_cancelled: Optional[bool] = None


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: Optional[str]
    title: str
    event_type: str
    description: Optional[str]
    start_datetime: datetime
    end_datetime: Optional[datetime]
    clinic_name: Optional[str]
    room: Optional[str]
    notes: Optional[str]
    reminder_minutes_before: int
    is_cancelled: bool
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# SOS
# ─────────────────────────────────────────────────────────────────────────────
class SOSCreate(BaseModel):
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    message: Optional[str] = None


class SOSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    triggered_at: datetime
    location_lat: Optional[float]
    location_lng: Optional[float]
    message: Optional[str]
    status: str
    responded_by_doctor_id: Optional[str]
    responded_at: Optional[datetime]
    resolution_notes: Optional[str]


class SOSRespondRequest(BaseModel):
    action: str = Field(pattern="^(accepted|rejected)$")
    resolution_notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_user_id: str
    sender_user_id: Optional[str]
    notification_type: str
    title: str
    message: str
    priority: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
class PipelineRunRequest(BaseModel):
    trigger_reason: str = "doctor_initiated"
    image_base64: Optional[str] = None  # For Agent 9 vision


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    diagnosis_id: Optional[str]
    pipeline_status: str
    hitl_required: bool
    hitl_reason: Optional[str]
    hitl_approved: Optional[bool]
    agent_outputs: List[Any]
    final_recommendation: Optional[dict]
    step_logs: List[str] = []
    pipeline_duration_ms: Optional[int]
    run_at: datetime
    completed_at: Optional[datetime]


class HITLApproveRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT
# ─────────────────────────────────────────────────────────────────────────────
class ChatbotMessage(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatbotResponse(BaseModel):
    response: str
    suggested_actions: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────────────────────────
class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    patient_id: Optional[str]
    ip_address: str
    request_path: str
    request_method: str
    success: bool
    timestamp: datetime
