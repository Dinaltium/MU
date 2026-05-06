"""app/agents/agent_2_diagnosis.py — Differential diagnosis with ICD-10."""
from __future__ import annotations
import logging
from app.agents.pipeline_state import PipelineState
from app.services import gemini_service
logger = logging.getLogger(__name__)

async def run(state: PipelineState) -> PipelineState:
    try:
        prompt_context = {
            "disease": state.disease_name,
            "symptoms": state.symptoms,
            "severity": state.severity,
            "stage": state.stage,
            "age": state.patient_age,
            "gender": state.patient_gender,
            "lab_results": state.lab_results,
            "imaging": state.imaging_results,
            "agent_1": state.agent_1_output,
        }
        import json, google.generativeai as genai
        from app.core.config import settings
        from app.services.gemini_service import SYSTEM_PROMPT
        model = genai.GenerativeModel(settings.GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
        prompt = f"""Differential diagnosis analysis:
Context: {json.dumps(prompt_context, default=str)}
Urgency findings: {state.agent_1_output}

Return JSON: {{
  "differentials": [{{"name": str, "icd_10": str, "probability": <0-1 float>, "reasoning": str}}],
  "primary_diagnosis": str,
  "primary_icd_10": str,
  "confidence": <0-1 float>,
  "additional_tests_needed": [str]
}}"""
        resp = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.2, max_output_tokens=2048))
        import json as j
        cleaned = resp.text.strip().replace("```json","").replace("```","").strip()
        state.agent_2_output = j.loads(cleaned)
        logger.info("Agent 2 (Diagnosis) done. Primary: %s", state.agent_2_output.get("primary_diagnosis"))
    except Exception as e:
        logger.error("Agent 2 failed: %s", e)
        state.agent_2_output = {"error": str(e), "differentials": [], "primary_diagnosis": state.disease_name, "confidence": 0.5}
    return state
