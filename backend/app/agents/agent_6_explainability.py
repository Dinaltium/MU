"""
app/agents/agent_6_explainability.py
Explainability Agent — Generates clinical summary for doctor and plain-language for patient.
"""
from __future__ import annotations

import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service

logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        # Generate explainability content from the current state
        result = await gemini_service.generate_explainability(state.to_dict())
        state.agent_6_output = result
        logger.info("Agent 6 (Explainability) completed.")
    except Exception as e:
        logger.error("Agent 6 (Explainability) failed: %s", e)
        state.agent_6_output = {
            "doctor_summary": "Error generating clinical summary.",
            "patient_explanation": "Error generating patient explanation.",
            "error": str(e)
        }
    return state
