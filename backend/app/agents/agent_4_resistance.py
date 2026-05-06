"""app/agents/agent_4_resistance.py — EUCAST/CLSI AMR assessment. HITL trigger."""
from __future__ import annotations
import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service
logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        candidates = state.agent_3_output.get("candidates", []) if state.agent_3_output else []
        result = await gemini_service.check_drug_resistance(
            candidates=candidates,
            disease=state.disease_name,
            region=state.region,
        )
        state.agent_4_output = result

        # HITL trigger: resistant candidate with confidence > 0.7
        resistance_map = result.get("resistance_map", [])
        for drug in resistance_map:
            if drug.get("status") == "resistant" and float(drug.get("confidence", 0)) > 0.7:
                state.hitl_pause = True
                state.hitl_reason = f"High-confidence resistance detected for {drug.get('drug', 'unknown drug')} (confidence: {drug.get('confidence')}). Doctor review required before proceeding."
                logger.warning("Agent 4 triggered HITL: %s", state.hitl_reason)
                break

        logger.info("Agent 4 (Resistance) done. HITL=%s", state.hitl_pause)
    except Exception as e:
        logger.error("Agent 4 failed: %s", e)
        state.agent_4_output = {"error": str(e), "resistance_map": [], "safe_candidates": []}
    return state
