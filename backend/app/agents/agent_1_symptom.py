"""app/agents/agent_1_symptom.py — Bayesian urgency scoring."""
from __future__ import annotations
import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service
logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        vitals = {}
        if state.imaging_results:
            vitals["imaging"] = state.imaging_results.get("findings", [])
        result = await gemini_service.analyze_symptoms_bayesian(
            symptoms=state.symptoms,
            severity=state.severity,
            vitals=vitals,
            disease=state.disease_name,
            imaging=state.imaging_results,
        )
        state.agent_1_output = result
        logger.info("Agent 1 (Symptom) done. Urgency: %s", result.get("urgency_level"))
    except Exception as e:
        logger.error("Agent 1 failed: %s", e)
        state.agent_1_output = {"error": str(e), "urgency_level": "medium", "urgency_score": 5.0, "key_findings": [], "red_flags": []}
    return state
