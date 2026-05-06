# RxBridge — Backend Architecture Specification (Final)

**Product**: RxBridge ("Rx" = prescription, "Bridge" = connected clinical care)
**Compliance inspiration**: NHS UK FHIR R4 + UAE NABIDH HISS
**AI Model**: Gemini 2.0 Flash (`gemini-2.0-flash`) via `google-generativeai` SDK
**Runtime**: Python 3.11 · FastAPI (async) · SQLAlchemy 2.x async · PostgreSQL (dev: SQLite)

---

## 0. Clarifications Locked In

| # | Answer | Implication |
|---|--------|-------------|
| Consent | Auto-granted when doctor assigns patient | PatientConsent row created automatically on DoctorPatient insert; patient notified; patient can revoke anytime |
| Lab flow | Doctor orders test → patient initiates at lab → lab submits report | Three-party LabOrder table ties doctor + patient + lab; lab sees only their specific order |
| SOS routing | Assigned doctors of that patient only | WebSocket broadcast filtered to doctor_ids from DoctorPatient where patient_id matches |
| Vision | X-rays, MRIs, skin photos, lab slides (all types) | Agent 9 prompt auto-detects modality from image content |

---

## 1. Meta-Instructions for Claude Sonnet 4.6

When generating code from this spec:
- Use **async/await everywhere** — no sync DB calls, no `session.query()`
- Use **SQLAlchemy 2.x async ORM**: `await session.execute(select(Model).where(...))`
- Use **Pydantic v2**: `model_config = ConfigDict(from_attributes=True)` — never `orm_mode = True`
- Use **`python-jose`** for JWT, **`passlib[bcrypt]`** for hashing
- Use **`google-generativeai`** SDK — `genai.GenerativeModel("gemini-2.0-flash")`
- Every route uses `db: AsyncSession = Depends(get_db)` and a role-guard dependency
- All IDs: `Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`
- Zero hardcoded strings — all config via `.env` through `pydantic-settings`
- Audit log every data access and mutation — append-only, never UPDATE/DELETE audit_logs
- Data isolation: every query scoped by `current_user["sub"]` — never trust client-sent IDs for ownership
- Response envelope: `{"success": bool, "data": ..., "error": str|None}`
- Async relationship loading: always use `selectinload()` in query options, never `lazy="joined"`
- Never import one model inside another model file — use string FK references only

---

## 2. Product Overview — Four Isolated Views

| View | Role Token | Can Read | Can Write |
|------|-----------|----------|-----------|
| **Patient** | `patient` | Own profile, diagnoses, meds, lab reports, reports, recovery scores | Check-in, dose log, SOS, consent revoke |
| **Doctor** | `doctor` | Assigned patients full clinical record (consent-gated) | Diagnoses, medications, reports, diet, suggestions, calendar, pipeline |
| **Lab** | `lab` | Only LabOrder rows assigned to this lab | Submit LabReport for that order only |
| **Admin** | `admin` | User list, audit logs | Approve lab accounts |

Zero cross-contamination: patient data never accessible to another patient, another doctor without assignment and consent, or a lab beyond their specific order.

---

## 3. Complete Database Schema

### 3.1 Auth

**`users`**
```
id                     String PK (uuid4)
email                  String UNIQUE NOT NULL INDEX
hashed_password        String NOT NULL
role                   Enum(patient|doctor|lab|admin) NOT NULL
is_active              Boolean DEFAULT true
mfa_enabled            Boolean DEFAULT false
mfa_secret             String NULLABLE
failed_login_attempts  Integer DEFAULT 0
locked_until           DateTime NULLABLE
last_login_at          DateTime NULLABLE
created_at             DateTime DEFAULT utcnow
updated_at             DateTime DEFAULT utcnow ON UPDATE
```

---

### 3.2 Profiles

**`patient_profiles`**
```
id                  String PK (uuid4)
user_id             String FK(users.id) UNIQUE NOT NULL
full_name           String NOT NULL
date_of_birth       Date NOT NULL
gender              String NOT NULL
weight_kg           Float NOT NULL
height_cm           Float NOT NULL
blood_group         Enum(A+|A-|B+|B-|AB+|AB-|O+|O-|Unknown) DEFAULT Unknown
phone               String NULLABLE
address             Text NULLABLE
allergies           JSON DEFAULT []
chronic_conditions  JSON DEFAULT []
emergency_contact   JSON NULLABLE        # {name, phone, relation}
created_at          DateTime
updated_at          DateTime
```

**`doctor_profiles`**
```
id                             String PK (uuid4)
user_id                        String FK(users.id) UNIQUE NOT NULL
full_name                      String NOT NULL
specialization                 String NOT NULL
medical_registration_number    String UNIQUE NOT NULL
hospital_affiliation           String NOT NULL
phone                          String NULLABLE
clinics                        JSON DEFAULT []   # [{name, address, city, phone}]
created_at                     DateTime
updated_at                     DateTime
```

**`lab_profiles`**
```
id               String PK (uuid4)
user_id          String FK(users.id) UNIQUE NOT NULL
lab_name         String NOT NULL
registration_id  String UNIQUE NOT NULL
address          String NOT NULL
city             String NOT NULL
phone            String NULLABLE
is_approved      Boolean DEFAULT false
approved_by      String NULLABLE
approved_at      DateTime NULLABLE
created_at       DateTime
updated_at       DateTime
```

---

### 3.3 Consent and Assignment

**`doctor_patients`** — Assignment record
```
id                       String PK
doctor_id                String FK(doctor_profiles.id) NOT NULL
patient_id               String FK(patient_profiles.id) NOT NULL
assigned_at              DateTime DEFAULT utcnow
assigned_clinic_name     String NULLABLE
assigned_clinic_address  String NULLABLE
status                   Enum(active|discharged|transferred) DEFAULT active
doctor_summary           Text NULLABLE
improvement_suggestions  JSON DEFAULT []
diet_plan                JSON DEFAULT []   # [{meal, items, notes, foods_to_avoid}]
updated_at               DateTime
UNIQUE(doctor_id, patient_id)
```

**`patient_consents`** — Auto-created on DoctorPatient insert; patient can revoke
```
id              String PK
patient_id      String FK(patient_profiles.id) NOT NULL
doctor_id       String FK(doctor_profiles.id) NOT NULL
is_active       Boolean DEFAULT true
consent_scope   JSON DEFAULT ["read_diagnoses","read_labs","read_medications","read_reports","read_recovery"]
purpose         String DEFAULT "treatment"
granted_at      DateTime DEFAULT utcnow
revoked_at      DateTime NULLABLE
auto_granted    Boolean DEFAULT true
UNIQUE(patient_id, doctor_id)
```

---

### 3.4 Lab Order Flow (Three-Party)

**`lab_orders`** — Doctor creates, patient initiates, lab fulfills
```
id                    String PK
doctor_id             String FK(doctor_profiles.id) NOT NULL
patient_id            String FK(patient_profiles.id) NOT NULL
lab_id                String FK(lab_profiles.id) NULLABLE    # set when patient initiates
diagnosis_id          String FK(diagnoses.id) NULLABLE
order_code            String UNIQUE NOT NULL                  # short code patient shows at lab e.g. RXB-ABCD
tests_requested       JSON NOT NULL                          # [{test_name, purpose, urgency}]
clinical_notes        Text NULLABLE
priority              Enum(routine|urgent|stat) DEFAULT routine
status                Enum(ordered|patient_initiated|in_progress|submitted|verified|cancelled) DEFAULT ordered
ordered_at            DateTime DEFAULT utcnow
patient_initiated_at  DateTime NULLABLE
submitted_at          DateTime NULLABLE
verified_at           DateTime NULLABLE
expires_at            DateTime                               # 30 days from ordered_at
```

**`lab_reports`** — Immutable after submission
```
id                    String PK
lab_order_id          String FK(lab_orders.id) NOT NULL
lab_id                String FK(lab_profiles.id) NOT NULL
patient_id            String FK(patient_profiles.id) NOT NULL
doctor_id             String FK(doctor_profiles.id) NOT NULL
diagnosis_id          String FK(diagnoses.id) NULLABLE
report_title          String NOT NULL
report_type           String NOT NULL                        # CBC|LFT|RFT|culture|imaging|biopsy|other
raw_report_data       JSON NOT NULL                         # [{test_name, result_value, unit, reference_range, is_abnormal}]
report_hash           String NOT NULL                       # SHA256 of raw_report_data — SET ONCE, NEVER UPDATE
report_pdf_url        String NULLABLE
status                Enum(submitted|verified|rejected) DEFAULT submitted
lab_technician_name   String NOT NULL
submitted_at          DateTime DEFAULT utcnow
is_amended            Boolean DEFAULT false
amendment_reason      Text NULLABLE
previous_version_id   String FK(lab_reports.id) NULLABLE    # self-ref for amendments
```

IMMUTABILITY RULE: Once submitted, raw_report_data and report_hash are never updated.
Any correction creates a new LabReport row with is_amended=True and previous_version_id set.

---

### 3.5 Clinical

**`diagnoses`**
```
id                   String PK
doctor_id            String FK(doctor_profiles.id) NOT NULL
patient_id           String FK(patient_profiles.id) NOT NULL
disease_name         String NOT NULL
disease_category     String NULLABLE
icd_10_code          String NULLABLE
stage                String NULLABLE
severity             Enum(mild|moderate|severe|critical) DEFAULT mild
status               Enum(active|improving|stable|critical|discharged) DEFAULT active
doctor_notes         Text NULLABLE
ai_pipeline_output   JSON NULLABLE
clinic_name          String NULLABLE
clinic_address       String NULLABLE
diagnosed_at         DateTime DEFAULT utcnow
updated_at           DateTime
```

**`medications`**
```
id              String PK
patient_id      String FK(patient_profiles.id) NOT NULL
doctor_id       String FK(doctor_profiles.id) NOT NULL
diagnosis_id    String FK(diagnoses.id) NULLABLE
name            String NOT NULL
dosage          String NOT NULL
frequency       String NOT NULL
route           String DEFAULT "oral"
schedule_times  JSON DEFAULT []
instructions    Text NULLABLE
start_date      DateTime NOT NULL
end_date        DateTime NULLABLE
duration_days   Integer NULLABLE
status          Enum(active|completed|stopped|paused) DEFAULT active
prescribed_at   DateTime DEFAULT utcnow
updated_at      DateTime
```

**`medication_logs`**
```
id              String PK
medication_id   String FK(medications.id) NOT NULL
patient_id      String FK(patient_profiles.id) NOT NULL
scheduled_at    DateTime NOT NULL
taken_at        DateTime NULLABLE
is_taken        Boolean DEFAULT false
is_missed       Boolean DEFAULT false
patient_note    String NULLABLE
logged_at       DateTime DEFAULT utcnow
```

---

### 3.6 Recovery and Monitoring

**`symptom_checkins`**
```
id                String PK
patient_id        String FK(patient_profiles.id) NOT NULL
checkin_date      Date DEFAULT today
feel_status       Enum(better|same|worse) NOT NULL
symptoms_present  JSON DEFAULT []
severity          Integer NULLABLE              # 1-10
temperature_c     Float NULLABLE
bp_systolic       Integer NULLABLE
bp_diastolic      Integer NULLABLE
heart_rate        Integer NULLABLE
spo2              Float NULLABLE
blood_glucose     Float NULLABLE
patient_note      Text NULLABLE
checked_in_at     DateTime DEFAULT utcnow
```

**`recovery_scores`** — Computed only, never manually inserted
```
id                          String PK
patient_id                  String FK(patient_profiles.id) NOT NULL
score_date                  Date DEFAULT today
score                       Float NOT NULL                # 0-100
medication_adherence_score  Float                         # 0-40
symptom_score               Float                         # 0-35
vitals_score                Float                         # 0-25
trend                       Enum(improving|stable|declining) DEFAULT stable
color_status                Enum(green|yellow|red) DEFAULT yellow
missed_doses_today          Integer DEFAULT 0
consecutive_missed_days     Integer DEFAULT 0
missed_dose_alert           String NULLABLE
follow_up_in_days           Integer NULLABLE
follow_up_reason            String NULLABLE
computed_at                 DateTime DEFAULT utcnow
UNIQUE(patient_id, score_date)
```

---

### 3.7 Reports and Calendar

**`reports`**
```
id                        String PK
doctor_id                 String FK(doctor_profiles.id) NOT NULL
patient_id                String FK(patient_profiles.id) NOT NULL
diagnosis_id              String FK(diagnoses.id) NULLABLE
report_type               Enum(progress|treatment_plan|discharge|follow_up|lab_summary) NOT NULL
title                     String NOT NULL
content                   Text NOT NULL
patient_friendly_content  Text NULLABLE
treatment_plan            JSON NULLABLE
clinic_name               String NULLABLE
clinic_address            String NULLABLE
is_shared_with_patient    Boolean DEFAULT true
generated_at              DateTime DEFAULT utcnow
```

**`calendar_events`**
```
id                       String PK
doctor_id                String FK(doctor_profiles.id) NOT NULL
patient_id               String FK(patient_profiles.id) NULLABLE
title                    String NOT NULL
event_type               String NOT NULL     # surgery|follow_up|consultation|personal
description              Text NULLABLE
start_datetime           DateTime NOT NULL
end_datetime             DateTime NULLABLE
clinic_name              String NULLABLE
clinic_address           String NULLABLE
room                     String NULLABLE
notes                    Text NULLABLE
reminder_minutes_before  Integer DEFAULT 30
is_cancelled             Boolean DEFAULT false
requires_hitl_approval   Boolean DEFAULT false
hitl_approved            Boolean NULLABLE
hitl_approved_at         DateTime NULLABLE
created_at               DateTime DEFAULT utcnow
```

---

### 3.8 SOS, Notifications, Audit, Pipeline

**`sos_alerts`**
```
id                       String PK
patient_id               String FK(patient_profiles.id) NOT NULL
triggered_at             DateTime DEFAULT utcnow
location_lat             Float NULLABLE
location_lng             Float NULLABLE
message                  Text NULLABLE
status                   Enum(pending|accepted|rejected|resolved) DEFAULT pending
responded_by_doctor_id   String FK(doctor_profiles.id) NULLABLE
responded_at             DateTime NULLABLE
resolution_notes         Text NULLABLE
```

**`notifications`**
```
id                  String PK
recipient_user_id   String FK(users.id) NOT NULL
sender_user_id      String NULLABLE
notification_type   String NOT NULL
title               String NOT NULL
message             Text NOT NULL
metadata            JSON DEFAULT {}
priority            Enum(low|normal|high|critical) DEFAULT normal
is_read             Boolean DEFAULT false
read_at             DateTime NULLABLE
created_at          DateTime DEFAULT utcnow
```

**`audit_logs`** — APPEND ONLY, application never calls UPDATE or DELETE on this table
```
id               String PK
actor_user_id    String NOT NULL
actor_role       String NOT NULL
action           String NOT NULL
resource_type    String NOT NULL
resource_id      String NOT NULL
patient_id       String NULLABLE
ip_address       String NOT NULL
user_agent       String
request_path     String
request_method   String
metadata         JSON DEFAULT {}
success          Boolean NOT NULL
timestamp        DateTime NOT NULL INDEX
```

**`pipeline_runs`**
```
id                   String PK
doctor_id            String FK(doctor_profiles.id)
patient_id           String FK(patient_profiles.id)
diagnosis_id         String FK(diagnoses.id) NULLABLE
trigger_reason       String
input_payload        JSON
agent_outputs        JSON                            # list of up to 9 agent result dicts
final_recommendation JSON
pipeline_status      Enum(running|hitl_pending|complete|failed) DEFAULT running
hitl_required        Boolean DEFAULT false
hitl_reason          String NULLABLE
hitl_approved        Boolean NULLABLE
hitl_approved_at     DateTime NULLABLE
pipeline_duration_ms Integer NULLABLE
run_at               DateTime DEFAULT utcnow
completed_at         DateTime NULLABLE
```

---

## 4. Lab Order Flow — Complete Lifecycle

1. **Doctor creates Lab Order** (`POST /lab-orders`). Status = `ordered`.
2. **Patient presents Order Code at Lab**.
3. **Lab initiates Order** (`POST /labs/orders/{code}/initiate`). `lab_id` set, status = `patient_initiated`.
4. **Lab submits Report** (`POST /labs/reports`). Status = `submitted`.
5. **Doctor & Patient notified**.

---

## 5. The 8-Agent + Vision Pipeline

### 5.1 PipelineState Dataclass
- Inputs: patient_id, doctor_id, diagnosis_id, symptoms, lab_results, meds, etc.
- Agent outputs: dicts for each agent.
- HITL control: hitl_pause, reason, status.

### 5.2 Agent Contracts
- **Agent 9 (Vision)**: Auto-detects image modality and findings.
- **Agent 1 (Symptom)**: Bayesian urgency scoring.
- **Agent 2 (Diagnosis)**: Differential diagnosis with ICD-10.
- **Agent 3 (Drug)**: Evidence-ranked candidates.
- **Agent 4 (Resistance)**: AMR assessment. (HITL trigger if resistant).
- **Agent 5 (Safety)**: Interactions & allergies. (HITL trigger if unsafe).
- **Agent 6 (Explainability)**: Summary for doctor & patient.
- **Agent 7 (Report)**: Final treatment plan.
- **Agent 8 (Monitoring)**: CUSUM statistical deterioration detection.

---

## 6. Recovery Score Algorithm
- Adherence (40) + Symptom (35) + Vitals (25) = Total (100).
- Trend: improving/stable/declining.
- Color: green/yellow/red.

---

## 7. Security Implementation Details
- **Consent Gate**: Every access check logged to audit_logs.
- **JWT Blacklist**: Redis-based revocation.
- **Login Protection**: Lockout after 5 failed attempts.
- **Lab Immutability**: SHA256 hash on insert.
- **Rate Limiting**: via `slowapi`.

---

## 8. Exact Folder Structure
Defined in architecture.md section 11.
