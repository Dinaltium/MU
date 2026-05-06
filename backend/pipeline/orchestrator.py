"""
pipeline/orchestrator.py

WHY THIS DESIGN:
  Sequential pipeline where each agent enriches a shared state object.
  This pattern (similar to LangGraph's linear graph) gives us:
    1. Determinism — agents always run in the same order
    2. Traceability — step_updates captures every transition
    3. Fail-fast — a broken agent raises immediately rather than
       silently producing a corrupt recommendation

SECURITY NOTES:
  • The state object passed into this function is validated at the router
    level before it arrives here (consultation router creates it from
    authenticated request data only).
  • agent outputs are NEVER forwarded to the user raw; only the curated
    fields written by the report agent reach the database, and only the
    doctor_summary / patient_explanation written by explainability are
    sent to the client.
  • Exceptions bubble up to FastAPI's exception handler which returns
    a 500 without leaking internal state detail.
"""

import logging
from agents import (
    symptom_analysis,
    diagnosis,
    drug_recommendation,
    resistance_check,
    patient_safety,
    explainability,
    report,
)
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)


async def run_pipeline(state: PipelineState) -> PipelineState:
    """
    Run all 7 agents in sequence.
    Each agent receives the full state, enriches it, and returns it.
    On failure the agent name and error are recorded in step_updates,
    the exception is re-raised so the caller can mark the consultation
    as 'failed' in the database.
    """
    steps = [
        symptom_analysis.run,
        diagnosis.run,
        drug_recommendation.run,
        resistance_check.run,
        patient_safety.run,
        explainability.run,
        report.run,
    ]

    for step in steps:
        agent_name = step.__module__.split(".")[-1]
        try:
            state = await step(state)
        except Exception as exc:
            # Record failure without exposing internal Python stack traces
            # to downstream consumers.
            state["step_updates"].append(
                f"{agent_name}:failed:{type(exc).__name__}"
            )
            logger.exception(
                "Pipeline agent %s raised an exception", agent_name
            )
            raise  # let the router handle cleanup

    return state
