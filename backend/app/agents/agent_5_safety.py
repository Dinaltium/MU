"""app/agents/agent_5_safety.py — Drug-drug interactions + allergy check. HITL trigger."""
from __future__ import annotations
import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service
logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        safe_candidates = state.agent_4_output.get("safe_candidates", []) if state.agent_4_output else []
        all_candidates = state.agent_3_output.get("candidates", []) if state.agent_3_output else []
        # Use only safe candidates from agent 4
        filtered = [c for c in all_candidates if c.get("name") in safe_candidates] if safe_candidates else all_candidates

        result = await gemini_service.check_drug_safety(
            candidates=filtered,
            allergies=state.allergies,
            current_meds=state.current_medications,
            conditions=state.chronic_conditions,
        )
        state.agent_5_output = result

        # HITL trigger: unsafe to proceed
        if not result.get("safe_to_proceed", True):
            state.hitl_pause = True
            flags = result.get("safety_flags", [])
            state.hitl_reason = f"Safety concern detected: {'; '.join(flags[:3])}. Doctor approval required."
            logger.warning("Agent 5 triggered HITL: %s", state.hitl_reason)

        logger.info("Agent 5 (Safety) done. Safe=%s", result.get("safe_to_proceed"))
    except Exception as e:
        logger.error("Agent 5 failed: %s", e)
        state.agent_5_output = {"error": str(e), "safe_to_proceed": False, "safety_flags": [str(e)],
                                 "cleared_candidates": [], "interaction_warnings": [], "contraindications": []}
        state.hitl_pause = True
        state.hitl_reason = f"Safety check error — manual review required: {e}"
    return state
