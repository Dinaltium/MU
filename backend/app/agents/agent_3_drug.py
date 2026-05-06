"""app/agents/agent_3_drug.py — Evidence-ranked drug candidates."""
from __future__ import annotations
import json, logging
import google.generativeai as genai
from app.agents.pipeline_state import PipelineState
from app.core.config import settings
from app.services.gemini_service import SYSTEM_PROMPT
logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
        prompt = f"""Drug recommendation for clinical decision support:
Disease: {state.disease_name} (Stage: {state.stage}, Severity: {state.severity})
Primary diagnosis: {state.agent_2_output.get("primary_diagnosis") if state.agent_2_output else state.disease_name}
Patient: Age {state.patient_age}, Gender {state.patient_gender}
Allergies: {state.allergies}
Current medications: {state.current_medications}
Chronic conditions: {state.chronic_conditions}
Lab results: {json.dumps(state.lab_results, default=str)}

Return JSON: {{
  "candidates": [{{
    "name": str, "class": str, "dosage": str, "frequency": str, "route": str,
    "evidence_level": "A|B|C", "efficacy_score": <0-1>, "safety_score": <0-1>,
    "availability": "essential|common|specialist"
  }}],
  "first_line": str,
  "rationale": str,
  "monitoring_required": [str]
}}"""
        resp = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.2, max_output_tokens=2048))
        cleaned = resp.text.strip().replace("```json","").replace("```","").strip()
        state.agent_3_output = json.loads(cleaned)
        logger.info("Agent 3 (Drug) done. First line: %s", state.agent_3_output.get("first_line"))
    except Exception as e:
        logger.error("Agent 3 failed: %s", e)
        state.agent_3_output = {"error": str(e), "candidates": [], "first_line": "", "rationale": ""}
    return state
