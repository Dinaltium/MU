"""
agents/resistance_check.py

WHY PK/PD MODELLING:
  Most antibiotic resistance checks in simpler systems just flag
  "this drug is resistant in this region." Our system goes further:
  it calculates whether the ACHIEVABLE DRUG CONCENTRATION in THIS
  specific patient exceeds the MIC (minimum inhibitory concentration)
  of the pathogen.

  A drug might be flagged as "moderate resistance" in the region,
  but if we can prescribe a higher dose that still achieves 4× the
  MIC in this patient's body (accounting for their weight and renal
  function), it may still be clinically effective.

  Conversely, a drug with low regional resistance might still fail
  if the patient's renal impairment causes it to be cleared too fast.

SECURITY NOTE:
  • MIC values come from a trusted local JSON database, not from
    LLM output — the LLM cannot be prompted to return a false MIC.
  • Patient PII (name, ID) is not passed to the PK/PD model — only
    weight and renal_function are needed for pharmacokinetics.
  • Division by MIC is guarded against zero with a fallback of 1.0.
"""

import json
import os
import logging
from models.pkpd_model import PKPDModel
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

try:
    with open(os.path.join(_DATA_DIR, "mic_database.json")) as f:
        MIC_DB = json.load(f)
except FileNotFoundError:
    logger.warning("mic_database.json not found — using empty MIC database")
    MIC_DB = {}

_pkpd = PKPDModel()


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "ResistanceCheckAgent:running:Running PK/PD model..."
    )

    drug      = state["top_drug"]
    diagnosis = state["top_diagnosis"]
    patient   = state["patient_profile"]

    # MIC lookup — default to 1.0 mg/L if unknown
    mic = MIC_DB.get(drug, {}).get(diagnosis, 1.0)
    mic = max(mic, 0.001)  # Guard against zero-division

    achievable = _pkpd.calculate_concentration(
        drug=drug,
        weight=patient.get("weight_kg", 70),
        renal_function=patient.get("renal_function", 1.0),
    )

    ratio = achievable / mic

    # Clinical thresholds:
    #   ratio < 1  → drug cannot reach inhibitory concentration → HIGH risk
    #   ratio 1-4  → marginal efficacy → MODERATE risk
    #   ratio > 4  → robust killing → LOW risk
    if ratio < 1:
        risk = "HIGH"
    elif ratio < 4:
        risk = "MODERATE"
    else:
        risk = "LOW"

    state["resistance_risk"] = risk
    state["pkpd_ratio"]      = round(ratio, 2)
    state["mic_value"]       = mic

    state["step_updates"].append(
        f"ResistanceCheckAgent:complete:"
        f"Risk={risk}, PK/PD ratio={ratio:.2f}, MIC={mic}"
    )
    return state
