"""
app/agents/pipeline_state.py
PipelineState dataclass — shared state across all 9 agents.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineState:
    # ── Inputs ────────────────────────────────────────────────────────────────
    patient_id: str
    doctor_id: str
    disease_name: str
    severity: str
    symptoms: list[str]
    lab_results: list[dict] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    chronic_conditions: list[str] = field(default_factory=list)
    patient_age: int | None = None
    patient_gender: str | None = None
    region: str = "global"
    diagnosis_id: str | None = None
    stage: str | None = None
    imaging_results: dict | None = None  # Pre-populated by Agent 9

    # ── Agent outputs ─────────────────────────────────────────────────────────
    agent_1_output: dict | None = None   # Symptom analysis
    agent_2_output: dict | None = None   # Diagnosis
    agent_3_output: dict | None = None   # Drug recommendation
    agent_4_output: dict | None = None   # Resistance check
    agent_5_output: dict | None = None   # Patient safety
    agent_6_output: dict | None = None   # Explainability
    agent_7_output: dict | None = None   # Report generation
    agent_8_output: dict | None = None   # CUSUM monitoring
    agent_9_output: dict | None = None   # Vision (pre-pipeline)

    # ── HITL control ──────────────────────────────────────────────────────────
    hitl_pause: bool = False
    hitl_reason: str | None = None
    pipeline_run_id: str | None = None
    pipeline_status: str = "running"

    def to_dict(self) -> dict:
        """Serialize for storage / Gemini context."""
        return {
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "disease_name": self.disease_name,
            "severity": self.severity,
            "stage": self.stage,
            "symptoms": self.symptoms,
            "lab_results": self.lab_results,
            "current_medications": self.current_medications,
            "allergies": self.allergies,
            "chronic_conditions": self.chronic_conditions,
            "patient_age": self.patient_age,
            "patient_gender": self.patient_gender,
            "region": self.region,
            "imaging_results": self.imaging_results,
            "agent_1_output": self.agent_1_output,
            "agent_2_output": self.agent_2_output,
            "agent_3_output": self.agent_3_output,
            "agent_4_output": self.agent_4_output,
            "agent_5_output": self.agent_5_output,
            "agent_6_output": self.agent_6_output,
            "agent_7_output": self.agent_7_output,
            "agent_8_output": self.agent_8_output,
            "agent_9_output": self.agent_9_output,
            "hitl_pause": self.hitl_pause,
            "hitl_reason": self.hitl_reason,
            "pipeline_status": self.pipeline_status,
        }
