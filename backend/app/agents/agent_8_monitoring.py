"""
app/agents/agent_8_monitoring.py
CUSUM Monitoring Agent — Detects statistical deterioration using last 30 days of scores.
"""
from __future__ import annotations

import logging
from sqlalchemy import select, and_
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service
from app.models.recovery import RecoveryScore

logger = logging.getLogger(__name__)

async def run(state: PipelineState, db) -> PipelineState:
    try:
        # Fetch last 30 days of recovery scores for this patient
        stmt = select(RecoveryScore.score).where(
            RecoveryScore.patient_id == state.patient_id
        ).order_by(RecoveryScore.score_date.desc()).limit(30)
        
        result = await db.execute(stmt)
        scores = [row[0] for row in result.all()]
        
        # Reverse to get chronological order for CUSUM
        scores.reverse()
        
        if len(scores) < 3:
            state.agent_8_output = {
                "cusum_signal": False,
                "trend": "stable",
                "alert_level": "low",
                "message": "Insufficient data for trend analysis"
            }
            return state

        analysis = await gemini_service.run_cusum_analysis(scores)
        state.agent_8_output = analysis
        
        logger.info("Agent 8 (Monitoring) completed. Alert Level: %s", analysis.get("alert_level"))
        
        # If alert level is high, notify doctors (handled in orchestrator or specific service)
    except Exception as e:
        logger.error("Agent 8 (Monitoring) failed: %s", e)
        state.agent_8_output = {"error": str(e), "cusum_signal": False, "alert_level": "low"}
        
    return state
