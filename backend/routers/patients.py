"""
routers/patients.py

SECURITY DECISIONS:
  • Every endpoint requires authentication (get_current_user dependency).
  • Doctors can only access patients assigned to them — this is ABAC
    (attribute-based) on top of RBAC (role-based). A doctor-role token
    is not sufficient; the data must belong to that doctor.
  • Patients can only read their own record — never another patient's.
  • Bulk list endpoints return paginated results capped at 50 to prevent
    data scraping via a single API call.
  • Input is validated by Pydantic before touching the database. No raw
    string concatenation in SQL — asyncpg's parameterised queries prevent
    SQL injection entirely.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List

from utils.db import get_pool
from utils.security import get_current_user, require_role

router = APIRouter(tags=["patients"])
logger = logging.getLogger(__name__)


class PatientCreate(BaseModel):
    name:           str
    age:            int
    gender:         Optional[str] = None
    location:       Optional[str] = None
    weight_kg:      Optional[float] = None
    renal_function: Optional[float] = 1.0
    conditions:     Optional[List[str]] = []
    allergies:      Optional[List[str]] = []
    medications:    Optional[List[str]] = []


# ──────────────────────────────────────────────────────────
# Create patient (doctors only)
# ──────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    user: dict = Depends(require_role("doctor", "admin")),
):
    """
    WHY ONLY DOCTORS CREATE PATIENTS:
      Patients self-register in the users table, but a patient record
      (which contains clinical data) is created by the assigned doctor.
      This ensures someone cannot create a patient record with falsified
      clinical history.
    """
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO patients
            (doctor_id, name, age, gender, location, weight_kg,
             renal_function, conditions, allergies, medications)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb)
            RETURNING id
            """,
            user["sub"],
            body.name,
            body.age,
            body.gender,
            body.location,
            body.weight_kg,
            body.renal_function,
            body.conditions,
            body.allergies,
            body.medications,
        )
    logger.info("Patient created by doctor %s", user["sub"])
    return {"id": str(row["id"])}


# ──────────────────────────────────────────────────────────
# List doctor's patients
# ──────────────────────────────────────────────────────────

def _sanitize_patient(data: dict) -> dict:
    import json
    for field in ["conditions", "allergies", "medications"]:
        val = data.get(field)
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    data[field] = parsed
                else:
                    data[field] = [val] if val else []
            except:
                data[field] = [val] if val else []
        elif val is None:
            data[field] = []
    return data


@router.get("/")
async def list_patients(
    limit: int = Query(default=20, ge=1, le=50),  # cap at 50 — prevent scraping
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_role("doctor", "admin")),
):
    """
    Returns only patients belonging to the requesting doctor.
    Admin can see all (for support purposes).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        if user["role"] == "admin":
            rows = await conn.fetch(
                "SELECT id, name, age, gender, location, conditions, allergies, medications FROM patients ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset
            )
        else:
            rows = await conn.fetch(
                "SELECT id, name, age, gender, location, conditions, allergies, medications FROM patients WHERE doctor_id=$1::uuid ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                user["sub"], limit, offset
            )
    return [_sanitize_patient(dict(r)) for r in rows]


# ──────────────────────────────────────────────────────────
# Get a single patient
# ──────────────────────────────────────────────────────────

@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    user: dict = Depends(get_current_user),
):
    """
    ABAC check:
      - Doctor: must own the patient
      - Patient: can only retrieve their own record (user_id must match)
      - Admin: unrestricted
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM patients WHERE id = $1::uuid",
            patient_id
        )

    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")

    if user["role"] == "doctor" and str(row["doctor_id"]) != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if user["role"] == "patient" and str(row["user_id"]) != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return _sanitize_patient(dict(row))
