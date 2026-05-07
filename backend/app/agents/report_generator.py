"""
app/agents/report_generator.py
Generates the final structured report for the clinician.
"""
from __future__ import annotations

import logging
from app.agents.pipeline_state import PipelineState

logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    """
    Assembles all agent outputs into the final Report schema.
    """
    state.step_logs.append("ReportGenerator: Assembling clinical dossier...")
    try:
        # Assembling the final structured data
        report_data = {
            "diagnosis": state.disease_name,
            "confidence": (state.agent_2_output or {}).get("confidence"),
            "urgency": (state.agent_1_output or {}).get("urgency_level"),
            "treatment_plan": (state.agent_3_output or {}).get("dosage_plan"),
            "clinical_reasoning": (state.agent_6_output or {}).get("clinical_synthesis")
        }
        state.step_logs.append(f"ReportGenerator: Compiled results for {state.disease_name}.")

        # Reasoning
        reasoning = f"Generated final clinical dossier for {state.disease_name}. Report incorporates Bayesian confidence intervals and LLM-synthesized reasoning."

        # Update state
        state.agent_7_output = {
            "final_report": report_data,
            "status": "ready_for_review",
            "reasoning": reasoning,
            "methodology": "Structured Data Assembly"
        }
        
        state.step_logs.append("ReportGenerator: Complete. Final report ready.")
        logger.info("Agent: Report Generator complete.")
        
    except Exception as e:
        state.step_logs.append(f"ReportGenerator: ERROR: {str(e)}")
        logger.error("Report Generator Agent failed: %s", e)
        state.agent_7_output = {
            "error": str(e),
            "reasoning": f"Report generation failed: {str(e)}"
        }
        
    return state
