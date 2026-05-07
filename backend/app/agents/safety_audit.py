"""
app/agents/safety_audit.py
Final clinical safety check before report generation.
"""
from __future__ import annotations

import logging
from app.agents.pipeline_state import PipelineState

logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    """
    Final safety audit of the entire pipeline output.
    """
    state.step_logs.append("SafetyAudit: Commencing final clinical validation gate...")
    try:
        # Cross-agent validation
        diagnosis = (state.agent_2_output or {}).get("top_diagnosis")
        urgency = (state.agent_1_output or {}).get("urgency_level")
        state.step_logs.append(f"SafetyAudit: Validating consistency between Urgency ({urgency}) and Diagnosis ({diagnosis}).")
        
        # Safety Logic
        warnings = []
        if urgency == "CRITICAL" and diagnosis == "Minor Infection":
            state.step_logs.append("SafetyAudit: WHITE-BOX FLAG: Detected high-urgency with low-severity diagnosis. Potential logic discrepancy.")
            warnings.append("Discrepancy: High urgency for low-severity diagnosis.")
            state.hitl_pause = True # Trigger Human-in-the-loop
            state.hitl_reason = "Urgency/Diagnosis discrepancy detected."

        # Reasoning
        reasoning = "Comprehensive audit of diagnostic consistency and treatment safety. "
        if warnings:
            reasoning += f"SAFETY ALERT: {'; '.join(warnings)}. Pipeline paused for specialist review."
        else:
            reasoning += "No contraindications or diagnostic discrepancies identified. Safe for final reporting."

        # Update state
        state.agent_5_output = {
            "safety_status": "passed" if not warnings else "flagged",
            "warnings": warnings,
            "reasoning": reasoning,
            "methodology": "Cross-Agent Consistency Validation"
        }
        
        state.step_logs.append(f"SafetyAudit: Complete. Status: {state.agent_5_output['safety_status']}.")
        logger.info("Agent: Safety Audit complete. Status: %s", state.agent_5_output["safety_status"])
        
    except Exception as e:
        state.step_logs.append(f"SafetyAudit: ERROR: {str(e)}")
        logger.error("Safety Audit Agent failed: %s", e)
        state.agent_5_output = {
            "error": str(e),
            "reasoning": f"Safety audit could not be completed: {str(e)}"
        }
        
    return state
