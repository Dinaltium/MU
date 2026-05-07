"""
agents/diagnosis.py

WHY BAYESIAN NETWORK:
  Unlike a simple lookup table, the Bayesian Network models
  CONDITIONAL PROBABILITY — it naturally combines multiple symptoms with
  prior probabilities (disease prevalence in the region and age group).
  This is how real clinicians think: "fever alone is common, but fever +
  neck stiffness in a 25-year-old from South India strongly suggests
  bacterial meningitis."

SECURITY NOTE:
  • Only key_findings (symptom cluster), age, and region from the state
    are passed to the network. Patient name / ID / PII never enter the
    inference engine.
  • We cap results at top 3 — returning all possible diagnoses would
    overwhelm the downstream agents and the doctor.
  • Exception from individual disease queries are caught and skipped;
    a broken CPT for one disease should not abort the entire diagnosis.

INTERPRETABILITY:
  The output includes probability scores. This lets judges/doctors
  audit why the system chose a diagnosis, satisfying explainability
  requirements without needing a separate XAI library.
"""

import os
from models.bayesian_network import DiagnosisNetwork
from pipeline.state import PipelineState

_network  = DiagnosisNetwork()
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_network.load(os.path.join(_DATA_DIR, "diagnosis_network.pkl"))


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "DiagnosisAgent:running:Running Bayesian inference..."
    )

    results = _network.infer(
        symptoms=state["key_findings"],
        age=state["patient_profile"].get("age", 30),
        region=state["region"],
    )

    if not results:
        state["step_updates"].append(
            "DiagnosisAgent:failed:No diagnosis result produced"
        )
        raise RuntimeError("Bayesian inference returned empty results")

    state["diagnoses"]     = results
    state["top_diagnosis"] = results[0]["condition"]
    state["icd_code"]      = results[0]["icd_code"]

    state["step_updates"].append(
        f"DiagnosisAgent:complete:"
        f"Top={results[0]['condition']} at {results[0]['probability']}% confidence"
    )
    return state
