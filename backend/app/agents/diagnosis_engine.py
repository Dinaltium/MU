"""
app/agents/diagnosis_engine.py
Probabilistic diagnosis using Bayesian Networks.
"""
from __future__ import annotations

import os
import logging
from app.agents.pipeline_state import PipelineState
from app.agents.models.bayesian_network import DiagnosisNetwork

logger = logging.getLogger(__name__)

# Singleton network instance
_network = DiagnosisNetwork()
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_MODEL_PATH = os.path.join(_DATA_DIR, "diagnosis_network.pkl")

# Attempt to load existing model
if os.path.exists(_MODEL_PATH):
    _network.load(_MODEL_PATH)
else:
    logger.warning("Diagnosis network model not found at %s. Agent will use default/mock logic.", _MODEL_PATH)

async def run(state: PipelineState) -> PipelineState:
    """
    Performs Bayesian inference to determine the most likely diagnosis 
    based on symptom clusters, patient age, and region.
    """
    state.step_logs.append("DiagnosisEngine: Starting Bayesian inference...")
    try:
        # Get findings from previous agent
        symptom_data = state.agent_1_output or {}
        findings = symptom_data.get("key_findings", [])
        state.step_logs.append(f"DiagnosisEngine: Input findings for inference: {findings}")
        
        # Bayesian Inference
        state.step_logs.append("DiagnosisEngine: Running Variable Elimination on Bayesian Network...")
        results = _network.infer(
            symptoms=findings,
            age=30, 
            region="Global", 
        )
        
        if not results:
            state.step_logs.append("DiagnosisEngine: WHITE-BOX WARNING: Inference returned empty results.")
            raise ValueError("Bayesian inference returned no results for the given findings.")

        # Reasoning
        top = results[0]
        state.step_logs.append(f"DiagnosisEngine: Inference complete. Top condition: {top['condition']} ({top['probability']}% confidence).")
        
        reasoning = f"Bayesian inference suggests {top['condition']} as the primary diagnosis with {top['probability']}% confidence."
        if len(results) > 1:
            alternatives = [r['condition'] for r in results[1:3]]
            reasoning += f" Differential considerations include: {', '.join(alternatives)}."
            state.step_logs.append(f"DiagnosisEngine: Identified {len(results)-1} alternative differential diagnoses.")

        # Update state
        state.agent_2_output = {
            "diagnoses": results,
            "top_diagnosis": top["condition"],
            "icd_code": top.get("icd_code", "N/A"),
            "confidence": top["probability"],
            "reasoning": reasoning,
            "methodology": "Bayesian Network Inference"
        }
        
        # Explicitly set top diagnosis on state for next agents
        state.disease_name = top["condition"]
        
        state.step_logs.append(f"DiagnosisEngine: Complete. Propagating '{top['condition']}' to pipeline state.")
        logger.info("Agent: Diagnosis Engine complete. Top diagnosis: %s", top["condition"])
        
    except Exception as e:
        state.step_logs.append(f"DiagnosisEngine: CRITICAL ERROR: {str(e)}")
        logger.error("Diagnosis Engine Agent failed: %s", e)
        state.agent_2_output = {
            "error": str(e),
            "top_diagnosis": "Inconclusive",
            "reasoning": f"Diagnosis engine failed to reach a conclusion: {str(e)}"
        }
        
    return state
