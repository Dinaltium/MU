"""
app/agents/agent_7_report.py
Report Generation Agent — Finalizes the treatment plan and report structure.
"""
from __future__ import annotations

import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service

logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    # If HITL pause is active and not approved, this agent is blocked
    if state.hitl_pause and state.pipeline_status != "complete":
        logger.info("Agent 7 (Report) blocked by HITL pause.")
        return state

    try:
        result = await gemini_service.generate_consultation_report(state.to_dict())
        state.agent_7_output = result
        logger.info("Agent 7 (Report) completed.")
    except Exception as e:
        logger.error("Agent 7 (Report) failed: %s", e)
        state.agent_7_output = {
            "report_title": "Consultation Report (Incomplete)",
            "report_content": "Error generating full report content.",
            "error": str(e)
        }
    return state
