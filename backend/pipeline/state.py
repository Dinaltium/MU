"""
pipeline/state.py

WHY THIS EXISTS:
  A single typed dictionary that flows through every agent in the pipeline.
  Using TypedDict (instead of a plain dict) gives us:
    - Static type checking — catch mistakes before runtime
    - Self-documenting code — anyone reading the file knows exactly what
      data travels between agents
    - No accidental key creation — keys are declared up front

SECURITY NOTE:
  The state object is INTERNAL only. It is never serialised and sent
  directly to the frontend. The report agent writes a curated subset
  to the database, and the explainability agent produces human-readable
  summaries. Raw pipeline state must never appear in an HTTP response.
"""
from typing import TypedDict, List, Optional


class PipelineState(TypedDict):
    # ──────────────────────────────────────────────
    # INPUT — populated before the pipeline starts
    # ──────────────────────────────────────────────
    patient_id:      str
    doctor_id:       str
    consultation_id: str
    symptoms:        List[str]
    patient_profile: dict   # age, weight, conditions, allergies, medications
    region:          str    # e.g. "south_india" — used for regional resistance data

    # ──────────────────────────────────────────────
    # SYMPTOM ANALYSIS AGENT OUTPUT
    # ──────────────────────────────────────────────
    urgency_score:   Optional[str]        # LOW | MODERATE | HIGH | CRITICAL
    key_findings:    Optional[List[str]]  # symptom cluster label(s)
    red_flags:       Optional[List[str]]  # life-threatening patterns detected

    # ──────────────────────────────────────────────
    # DIAGNOSIS AGENT OUTPUT
    # ──────────────────────────────────────────────
    diagnoses:       Optional[List[dict]]  # [{condition, probability, icd_code}, …]
    top_diagnosis:   Optional[str]
    icd_code:        Optional[str]

    # ──────────────────────────────────────────────
    # DRUG RECOMMENDATION AGENT OUTPUT
    # ──────────────────────────────────────────────
    drug_candidates: Optional[List[dict]]  # [{name, score, …}, …] sorted desc
    top_drug:        Optional[str]

    # ──────────────────────────────────────────────
    # RESISTANCE CHECK AGENT OUTPUT
    # ──────────────────────────────────────────────
    resistance_risk: Optional[str]    # LOW | MODERATE | HIGH
    pkpd_ratio:      Optional[float]  # achievable_conc / MIC
    mic_value:       Optional[float]  # minimum inhibitory concentration

    # ──────────────────────────────────────────────
    # PATIENT SAFETY AGENT OUTPUT
    # ──────────────────────────────────────────────
    safety_flags:        Optional[List[str]]  # human-readable warnings
    interaction_alerts:  Optional[List[str]]  # raw interaction objects

    # ──────────────────────────────────────────────
    # EXPLAINABILITY AGENT OUTPUT
    # ──────────────────────────────────────────────
    doctor_summary:      Optional[str]  # clinical prose for the doctor
    patient_explanation: Optional[str]  # plain-language text for the patient

    # ──────────────────────────────────────────────
    # REPORT AGENT OUTPUT
    # ──────────────────────────────────────────────
    report_id:    Optional[str]

    # ──────────────────────────────────────────────
    # AUDIT TRAIL — every agent appends here
    # Format: "AgentName:status:message"
    # ──────────────────────────────────────────────
    step_updates: List[str]
