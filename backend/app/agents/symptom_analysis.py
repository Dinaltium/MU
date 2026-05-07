"""
app/agents/symptom_analysis.py
Bayesian urgency scoring using Naive Bayes and clinical red-flag rules.
"""
from __future__ import annotations

import os
import logging
from app.agents.pipeline_state import PipelineState
from app.agents.models.naive_bayes import SymptomClassifier

logger = logging.getLogger(__name__)

# Deterministic red-flag rules — these override any model prediction.
RED_FLAGS = {
    "neck_stiffness":        "meningeal_irritation",
    "chest_pain":            "cardiac_event",
    "difficulty_breathing":  "respiratory_failure",
    "sudden_vision_loss":    "neurological_emergency",
    "severe_headache":       "possible_haemorrhagic_stroke",
    "unconsciousness":       "neurological_emergency",
    "coughing_blood":        "pulmonary_emergency",
}

# Singleton classifier instance
_classifier = SymptomClassifier()
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_MODEL_PATH = os.path.join(_DATA_DIR, "symptom_model.pkl")

# Attempt to load existing model
if os.path.exists(_MODEL_PATH):
    _classifier.load(_MODEL_PATH)
else:
    logger.warning("Symptom model not found at %s. Agent will use default/mock logic.", _MODEL_PATH)

async def run(state: PipelineState) -> PipelineState:
    """
    Analyzes symptoms using a Naive Bayes classifier and cross-references with 
    hardcoded clinical red flags.
    """
    state.step_logs.append("SymptomAnalysis: Starting clinical symptom assessment...")
    try:
        symptoms = state.symptoms
        # Normalise inputs
        symptoms_lower = [s.lower().replace(" ", "_") for s in symptoms]
        state.step_logs.append(f"SymptomAnalysis: Normalised {len(symptoms)} symptoms for processing.")

        # 1. Model Prediction
        state.step_logs.append("SymptomAnalysis: Running Multinomial Naive Bayes classifier...")
        cluster, urgency = _classifier.predict(symptoms_lower)
        state.step_logs.append(f"SymptomAnalysis: Model predicted cluster '{cluster[0]}' with baseline urgency '{urgency}'.")
        
        # 2. Red-flag override
        state.step_logs.append("SymptomAnalysis: Cross-referencing against clinical red-flag dictionary...")
        flags = []
        for symptom in symptoms_lower:
            if symptom in RED_FLAGS:
                flags.append(RED_FLAGS[symptom])
                urgency = "CRITICAL"
                state.step_logs.append(f"SymptomAnalysis: WHITE-BOX ALERT: Detected red-flag '{symptom}'. Escalating urgency to CRITICAL.")

        # 3. Reasoning Generation
        reasoning = f"Analysis of {len(symptoms)} symptoms identified a {cluster[0]} pattern."
        if flags:
            reasoning += f" CRITICAL ESCALATION: Detected red-flag indicators: {', '.join(flags)}."
        else:
            reasoning += f" Urgency level set to {urgency} based on statistical symptom clustering."

        # Update state
        state.agent_1_output = {
            "urgency_level": urgency,
            "key_findings": cluster,
            "red_flags": flags,
            "reasoning": reasoning,
            "methodology": "Naive Bayes + Clinical Rule Override"
        }
        
        state.step_logs.append(f"SymptomAnalysis: Complete. Final Urgency: {urgency}.")
        logger.info("Agent: Symptom Analysis complete. Urgency: %s", urgency)
        
    except Exception as e:
        state.step_logs.append(f"SymptomAnalysis: CRITICAL ERROR: {str(e)}")
        logger.error("Symptom Analysis Agent failed: %s", e)
        state.agent_1_output = {
            "error": str(e),
            "urgency_level": "medium",
            "reasoning": f"Agent encountered an internal error during analysis: {str(e)}"
        }
        
    return state
