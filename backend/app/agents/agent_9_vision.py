"""
app/agents/agent_9_vision.py
Vision Agent — runs BEFORE sequential pipeline if image provided.
Auto-detects: X-ray | MRI | skin | lab-slide | other.
"""
from __future__ import annotations

import logging

from app.agents.pipeline_state import PipelineState
from app.services import gemini_service

logger = logging.getLogger(__name__)


async def run(state: PipelineState, image_b64: str) -> PipelineState:
    """Analyze medical image and populate state.imaging_results."""
    try:
        hint = f"{state.disease_name} — {state.severity} — {state.stage or 'stage unknown'}"
        result = await gemini_service.analyze_medical_image(image_b64, hint)
        state.agent_9_output = result
        state.imaging_results = result
        logger.info("Agent 9 (Vision) completed. Modality: %s", result.get("modality"))
    except Exception as e:
        logger.error("Agent 9 (Vision) failed: %s", e)
        state.agent_9_output = {"error": str(e), "modality": "unknown", "findings": []}
        state.imaging_results = state.agent_9_output
    return state
