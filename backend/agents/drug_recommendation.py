"""
agents/drug_recommendation.py

WHY FIVE-AXIS SCORING (not just efficacy):
  A drug that is highly efficacious against a pathogen is useless if:
    - It's resisted by local bacteria (resistance_score axis)
    - It interacts badly with a patient's existing medications (safety axis)
    - The patient had a bad reaction to it before (prior_response axis)
    - It's not available at the local pharmacy (availability axis)

  The weighted sum forces the system to make real-world trade-offs
  rather than recommending the "textbook best" drug blindly.

SECURITY NOTE:
  • Drug formulary and resistance data are loaded at module startup from
    trusted JSON files — never from user input.
  • The scoring function reads only the fields it needs from the patient
    profile (conditions, drug_responses) — it does not have access to
    patient PII.
  • Drug scores are rounded to 4 decimal places to prevent
    floating-point fingerprinting.
"""

import json
import os
import logging
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(filename: str) -> dict:
    path = os.path.join(_DATA_DIR, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Data file %s not found — using empty dict", filename)
        return {}


FORMULARY  = _load("drug_formulary.json")
RESISTANCE = _load("resistance_patterns.json")


def score_drug(drug: dict, diagnosis: str, region: str, patient_profile: dict) -> float:
    """
    Five-axis scoring — all axes normalised to [0, 1].

    Weights were chosen to reflect clinical priorities:
      0.35 efficacy     — core therapeutic effectiveness
      0.30 resistance   — critical for India where AMR is a major problem
      0.20 safety       — patient-specific contraindication check
      0.10 prior resp.  — personalised medicine signal
      0.05 availability — pragmatic local context
    """
    efficacy = drug.get("efficacy_rates", {}).get(diagnosis, 0.5)

    resistance_rate = RESISTANCE.get(region, {}).get(drug.get("class", ""), 0.1)
    resistance_score = 1.0 - resistance_rate  # higher resistance → lower score

    safety_score = 1.0
    for condition in patient_profile.get("conditions", []):
        if condition in drug.get("contraindications", []):
            safety_score -= 0.5
    safety_score = max(0.0, safety_score)  # floor at 0

    prior_response  = patient_profile.get("drug_responses", {}).get(drug.get("name", ""), 0.5)
    availability    = drug.get("availability_india", 1.0)

    total = (
        efficacy         * 0.35 +
        resistance_score * 0.30 +
        safety_score     * 0.20 +
        prior_response   * 0.10 +
        availability     * 0.05
    )
    return round(total, 4)


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "DrugRecommendationAgent:running:Scoring drug candidates..."
    )

    diagnosis  = state["top_diagnosis"]
    candidates = FORMULARY.get(diagnosis, [])

    if not candidates:
        logger.warning("No formulary entries for diagnosis: %s", diagnosis)
        # Fall back to broad-spectrum placeholder to avoid pipeline crash
        candidates = FORMULARY.get("default", [])

    scored = []
    for drug in candidates:
        score = score_drug(drug, diagnosis, state["region"], state["patient_profile"])
        scored.append({**drug, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)

    state["drug_candidates"] = scored
    state["top_drug"]        = scored[0]["name"] if scored else "consult_specialist"

    state["step_updates"].append(
        f"DrugRecommendationAgent:complete:"
        f"Top={state['top_drug']} score={scored[0]['score'] if scored else 'N/A'}"
    )
    return state
