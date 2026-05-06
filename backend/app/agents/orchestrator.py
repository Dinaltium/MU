"""
app/agents/orchestrator.py
Orchestrates the 9-agent pipeline flow.
"""
from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.pipeline_state import PipelineState
from app.agents import (
    agent_1_symptom, agent_2_diagnosis, agent_3_drug,
    agent_4_resistance, agent_5_safety, agent_6_explainability,
    agent_7_report, agent_8_monitoring, agent_9_vision
)
from app.models.pipeline_run import PipelineRun
from app.services.notification_service import notify_hitl_required

logger = logging.getLogger(__name__)

async def save_pipeline_run(state: PipelineState, db: AsyncSession):
    """Saves or updates the pipeline run state in the DB."""
    run_id = state.pipeline_run_id
    agent_outputs = [
        state.agent_1_output, state.agent_2_output, state.agent_3_output,
        state.agent_4_output, state.agent_5_output, state.agent_6_output,
        state.agent_7_output, state.agent_8_output, state.agent_9_output
    ]
    
    if run_id:
        from sqlalchemy import update
        stmt = update(PipelineRun).where(PipelineRun.id == run_id).values(
            agent_outputs=agent_outputs,
            pipeline_status=state.pipeline_status,
            hitl_required=state.hitl_pause,
            hitl_reason=state.hitl_reason,
            final_recommendation=state.agent_7_output,
            completed_at=datetime.utcnow() if state.pipeline_status == "complete" else None
        )
        await db.execute(stmt)
    else:
        run = PipelineRun(
            doctor_id=state.doctor_id,
            patient_id=state.patient_id,
            diagnosis_id=state.diagnosis_id,
            trigger_reason="consultation",
            input_payload=state.to_dict(),
            agent_outputs=agent_outputs,
            pipeline_status=state.pipeline_status,
            hitl_required=state.hitl_pause,
            hitl_reason=state.hitl_reason,
            run_at=datetime.utcnow()
        )
        db.add(run)
        await db.flush()
        state.pipeline_run_id = run.id

async def run_pipeline(state: PipelineState, image_data: str | None, db: AsyncSession) -> PipelineState:
    start_time = datetime.utcnow()
    
    # Phase 0: Vision (Agent 9) - Parallel if image provided
    if image_data:
        await agent_9_vision.run(state, image_data)

    # Phase 1: Clinical Assessment (Sequential Agents 1-4)
    state = await agent_1_symptom.run(state)
    state = await agent_2_diagnosis.run(state)
    state = await agent_3_drug.run(state)
    state = await agent_4_resistance.run(state)

    # Check for HITL Pause after Agent 4
    if state.hitl_pause:
        state.pipeline_status = "hitl_pending"
        await save_pipeline_run(state, db)
        await notify_hitl_required(db, state.doctor_id, state.pipeline_run_id, state.hitl_reason or "Resistance check failed")
        return state

    # Phase 2: Safety Check (Agent 5)
    state = await agent_5_safety.run(state)

    # Check for HITL Pause after Agent 5
    if state.hitl_pause:
        state.pipeline_status = "hitl_pending"
        await save_pipeline_run(state, db)
        await notify_hitl_required(db, state.doctor_id, state.pipeline_run_id, state.hitl_reason or "Safety check failed")
        return state

    # Phase 3: Finalization (Agents 6-8)
    state = await agent_6_explainability.run(state)
    state = await agent_7_report.run(state)
    state = await agent_8_monitoring.run(state, db)

    state.pipeline_status = "complete"
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
    # In a real app we'd save the duration to the PipelineRun
    
    await save_pipeline_run(state, db)
    return state
