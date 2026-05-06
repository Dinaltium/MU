"""
agents/symptom_analysis.py

WHY NAIVE BAYES FOR SYMPTOM CLASSIFICATION:
  Naive Bayes is the right choice here because:
    1. Probabilistic — it outputs a confidence score, not a boolean
    2. Interpretable — judges and doctors can understand why it chose a cluster
    3. Fast — classification is sub-millisecond even without GPU
    4. Handles sparse features — medical symptoms are high-dimensional but sparse

SECURITY NOTE:
  • Only symptom strings from the PipelineState are passed to the model.
    The patient's name, ID, or other PII is never passed to the classifier.
  • Red flag detection is a deterministic rule-based override — it cannot
    be fooled by an adversarially crafted symptom list in the way an LLM
    could be. The RED_FLAGS dictionary is hardcoded, not LLM-generated.

PRINCIPLE OF LEAST PRIVILEGE:
  This agent only reads: state["symptoms"]
  It only writes:       state["urgency_score"], state["key_findings"], state["red_flags"]
  It does not read patient PII, doctor IDs, or drug data.
"""

from models.naive_bayes import SymptomClassifier
from pipeline.state import PipelineState

# Deterministic red-flag rules — these override any model prediction.
# Clinical justification: these symptoms have high mortality if missed.
RED_FLAGS = {
    "neck_stiffness":        "meningeal_irritation",
    "chest_pain":            "cardiac_event",
    "difficulty_breathing":  "respiratory_failure",
    "sudden_vision_loss":    "neurological_emergency",
    "severe_headache":       "possible_haemorrhagic_stroke",
    "unconsciousness":       "neurological_emergency",
    "coughing_blood":        "pulmonary_emergency",
}

_classifier = SymptomClassifier()


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "SymptomAnalysisAgent:running:Analysing symptom cluster..."
    )

    symptoms = state["symptoms"]

    # Normalise inputs to lowercase to match training data labels
    symptoms_lower = [s.lower().replace(" ", "_") for s in symptoms]

    cluster, urgency = _classifier.predict(symptoms_lower)

    # Red-flag override — escalate to CRITICAL if any known flag is present
    flags = []
    for symptom in symptoms_lower:
        if symptom in RED_FLAGS:
            flags.append(RED_FLAGS[symptom])
            urgency = "CRITICAL"

    state["urgency_score"] = urgency
    state["key_findings"] = cluster if isinstance(cluster, list) else [cluster]
    state["red_flags"]    = flags

    state["step_updates"].append(
        f"SymptomAnalysisAgent:complete:"
        f"Urgency={urgency}, {len(flags)} red flags, cluster={cluster}"
    )
    return state
