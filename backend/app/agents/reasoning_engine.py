"""
app/agents/reasoning_engine.py
Synthesizes all agent outputs into a coherent clinical reasoning narrative.
"""
from __future__ import annotations

import logging
from app.agents.pipeline_state import PipelineState
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    """
    Uses Gemini to explain the logical flow from symptoms to treatment.
    """
    state.step_logs.append("ReasoningEngine: Synthesizing multi-agent trace for final clinical narrative...")
    try:
        # Collect all previous agent reasoning
        summaries = [
            f"Symptom Analysis: {getattr(state, 'agent_1_output', {}).get('reasoning')}",
            f"Diagnosis: {getattr(state, 'agent_2_output', {}).get('reasoning')}",
            f"Treatment: {getattr(state, 'agent_3_output', {}).get('reasoning')}",
            f"Safety: {getattr(state, 'agent_5_output', {}).get('reasoning')}",
        ]
        
        state.step_logs.append(f"ReasoningEngine: Consolidated {len(summaries)} agent reasonings for LLM synthesis.")
        context = "\n".join(summaries)
        
        # Call Gemini for a unified synthesis
        state.step_logs.append("ReasoningEngine: Invoking Gemini-1.5-Pro for professional clinical synthesis...")
        prompt = f"Synthesize the following clinical agent outputs into a professional medical reasoning summary for a doctor:\n\n{context}"
        synthesis = await gemini_service.generate_text(prompt)
        state.step_logs.append("ReasoningEngine: Narrative synthesis complete.")

        # Update state
        state.agent_6_output = {
            "clinical_synthesis": synthesis,
            "reasoning": "Consolidated pipeline logic into a unified clinical narrative using Gemini reasoning models.",
            "methodology": "AI-Orchestrated Synthesis"
        }
        
        state.step_logs.append("ReasoningEngine: Complete.")
        logger.info("Agent: Reasoning Engine complete.")
        
    except Exception as e:
        state.step_logs.append(f"ReasoningEngine: ERROR: {str(e)}")
        logger.error("Reasoning Engine Agent failed: %s", e)
        state.agent_6_output = {
            "error": str(e),
            "reasoning": f"Failed to synthesize clinical reasoning: {str(e)}"
        }
        
    return state
