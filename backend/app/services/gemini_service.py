"""
app/services/gemini_service.py
All Gemini AI calls. Returns typed dicts. Never hardcodes clinical data.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """You are RxBridge Assist — a clinical decision support AI integrated into a medical platform.
You assist LICENSED HEALTHCARE PROFESSIONALS ONLY.
You are NOT a replacement for clinical judgment.
All AI suggestions require doctor review and approval before acting.
Patient-facing content: be warm, clear, honest, hopeful — no jargon.
Always flag uncertainty. Never fabricate drug names, dosages, or lab values.
Return ONLY valid JSON when instructed. No markdown fences. No preamble. No explanation outside JSON."""

# In-memory cache for disease list (TTL managed by caller)
_disease_cache: dict | None = None


async def _call_gemini(prompt: str, as_json: bool = False) -> str | dict | list:
    """Core Gemini call wrapper with JSON stripping and error handling."""
    try:
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
            ),
        )
        text = response.text
        if as_json:
            cleaned = text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        return text
    except json.JSONDecodeError as e:
        logger.error("Gemini JSON parse error: %s", e)
        return {} if as_json else ""
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return {} if as_json else ""


async def get_disease_list() -> list[dict]:
    """Return common diseases for dropdown. Cached 24h."""
    global _disease_cache
    if _disease_cache:
        return _disease_cache
    prompt = """Return a JSON array of 50 common diseases treated in hospitals.
Each item: {"name": str, "category": str, "icd_10_prefix": str}
Categories: Infectious, Cardiovascular, Respiratory, Neurological, Gastrointestinal, Endocrine, Oncology, Musculoskeletal, Dermatological, Psychiatric"""
    result = await _call_gemini(prompt, as_json=True)
    _disease_cache = result if isinstance(result, list) else []
    return _disease_cache


async def get_tests_for_disease(disease_name: str) -> list[dict]:
    prompt = f"""For the disease "{disease_name}", return a JSON array of recommended diagnostic tests.
Each item: {{"test_name": str, "purpose": str, "urgency": "routine|urgent|stat", "type": "blood|imaging|culture|biopsy|other"}}
Return 5-10 most clinically relevant tests."""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, list) else []


async def get_symptoms_for_disease(disease_name: str) -> list[str]:
    prompt = f"""For the disease "{disease_name}", return a JSON array of 10-15 common symptoms.
Format: ["symptom_1", "symptom_2", ...]"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, list) else []


async def get_treatment_recommendations(
    disease: str,
    stage: str | None,
    patient_context: dict,
) -> dict:
    prompt = f"""Clinical decision support for:
Disease: {disease}
Stage: {stage or "not specified"}
Patient: Age {patient_context.get('age')}, Gender {patient_context.get('gender')}
Allergies: {patient_context.get('allergies', [])}
Chronic conditions: {patient_context.get('chronic_conditions', [])}
Current medications: {patient_context.get('current_medications', [])}

Return JSON: {{
  "first_line_treatment": str,
  "alternative_treatments": [str],
  "drug_recommendations": [{{"name": str, "dosage": str, "frequency": str, "duration": str, "evidence_level": str}}],
  "monitoring_parameters": [str],
  "red_flags": [str],
  "lifestyle_modifications": [str],
  "follow_up_timeline": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def analyze_symptoms_bayesian(
    symptoms: list[str],
    severity: str,
    vitals: dict,
    disease: str,
    imaging: dict | None = None,
) -> dict:
    prompt = f"""Bayesian symptom analysis for clinical decision support:
Known disease: {disease}
Severity: {severity}
Symptoms present: {symptoms}
Vitals: {vitals}
Imaging findings: {imaging or "none"}

Return JSON: {{
  "urgency_score": <0-10 float>,
  "urgency_level": "low|medium|high|critical",
  "key_findings": [str],
  "red_flags": [str],
  "confidence": <0-1 float>,
  "differential_alert": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def check_drug_resistance(
    candidates: list[dict],
    disease: str,
    region: str,
) -> dict:
    prompt = f"""Antimicrobial resistance assessment (EUCAST/CLSI guidelines):
Disease: {disease}
Region: {region}
Drug candidates: {json.dumps(candidates)}

Return JSON: {{
  "resistance_map": [{{"drug": str, "status": "sensitive|intermediate|resistant", "confidence": <0-1 float>, "mic_notes": str}}],
  "safe_candidates": [str],
  "high_risk_candidates": [str],
  "regional_resistance_note": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def check_drug_safety(
    candidates: list[dict],
    allergies: list[str],
    current_meds: list[str],
    conditions: list[str],
) -> dict:
    prompt = f"""Drug safety screening:
Candidates: {json.dumps(candidates)}
Patient allergies: {allergies}
Current medications: {current_meds}
Chronic conditions: {conditions}

Return JSON: {{
  "safety_flags": [str],
  "interaction_warnings": [{{"drugs": [str], "severity": "mild|moderate|severe", "description": str}}],
  "contraindications": [str],
  "cleared_candidates": [str],
  "safe_to_proceed": <bool>,
  "recommendation": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {"safe_to_proceed": False}


async def generate_explainability(state_dict: dict) -> dict:
    prompt = f"""Generate clinical explanation from pipeline state:
{json.dumps(state_dict, default=str)}

Return JSON: {{
  "doctor_summary": "Detailed clinical summary for physician (2-3 paragraphs)",
  "patient_explanation": "Simple patient-friendly explanation (1 paragraph, no jargon)",
  "confidence_note": str,
  "evidence_sources": [str],
  "uncertainty_flags": [str]
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def generate_consultation_report(state_dict: dict) -> dict:
    prompt = f"""Generate a structured clinical consultation report:
{json.dumps(state_dict, default=str)}

Return JSON: {{
  "report_title": str,
  "report_content": "Full clinical report text",
  "treatment_plan": {{
    "phases": [{{"phase": str, "duration": str, "actions": [str]}}],
    "expected_recovery": str,
    "lifestyle_changes": [str],
    "medications": [str]
  }},
  "follow_up_in_days": <int>,
  "patient_friendly_summary": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def run_cusum_analysis(scores_list: list[float]) -> dict:
    prompt = f"""CUSUM statistical analysis for patient recovery monitoring:
Recovery scores (chronological, last 30 days): {scores_list}

Return JSON: {{
  "cusum_signal": <bool — true if deterioration detected>,
  "trend": "improving|stable|declining",
  "alert_level": "low|medium|high",
  "consecutive_decline_days": <int>,
  "recommended_action": str,
  "statistical_note": str
}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def analyze_medical_image(image_b64: str, hint: str = "") -> dict:
    """Agent 9 — Vision analysis. Auto-detects modality."""
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL, system_instruction=SYSTEM_PROMPT)
        import base64
        image_data = base64.b64decode(image_b64)
        response = model.generate_content([
            f"Analyze this medical image. Clinical hint: {hint or 'None'}. Return JSON only: "
            '{"modality": str, "findings": [str], "abnormalities": [str], '
            '"visual_confidence": <0-1 float>, "clinical_relevance": str, "recommendation": str}',
            {"mime_type": "image/jpeg", "data": image_data},
        ])
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        logger.error("Image analysis error: %s", e)
        return {"modality": "unknown", "findings": [], "abnormalities": [], "visual_confidence": 0.0,
                "clinical_relevance": "Analysis failed", "recommendation": "Manual review required"}


async def generate_patient_explanation(
    disease: str,
    stage: str | None,
    test_results: list[dict],
    meds: list[str],
    patient_name: str,
) -> str:
    prompt = f"""Write a warm, encouraging health update for {patient_name}:
Condition: {disease} (Stage: {stage or 'not specified'})
Key test results: {test_results}
Medications: {meds}
Keep it simple, hopeful, and under 200 words. No medical jargon."""
    return await _call_gemini(prompt, as_json=False)


async def generate_patient_friendly_report(report_content: str, patient_name: str) -> str:
    prompt = f"""Convert this clinical report to a patient-friendly version for {patient_name}:
{report_content}
Make it warm, clear, simple (no medical jargon). Under 300 words."""
    return await _call_gemini(prompt, as_json=False)


async def generate_diet_plan(
    disease: str,
    stage: str | None,
    allergies: list[str],
    conditions: list[str],
) -> list[dict]:
    prompt = f"""Create a 7-day diet plan for a patient with:
Disease: {disease} (Stage: {stage or 'not specified'})
Allergies: {allergies}
Chronic conditions: {conditions}

Return JSON array: [{{
  "meal": "Breakfast|Lunch|Dinner|Snack",
  "items": [str],
  "notes": str,
  "foods_to_avoid": [str]
}}]
Include 3 meals + 1 snack per day = 28 items."""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, list) else []


async def predict_follow_up(
    disease: str,
    score: float,
    trend: str,
    days_since_diagnosis: int,
) -> dict:
    prompt = f"""Predict follow-up schedule for:
Disease: {disease}
Recovery score: {score}/100
Trend: {trend}
Days since diagnosis: {days_since_diagnosis}

Return JSON: {{"follow_up_in_days": <int>, "reason": str, "urgency": "routine|soon|urgent"}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {"follow_up_in_days": 7, "reason": "Routine check", "urgency": "routine"}


async def analyze_missed_doses(
    missed_count: int,
    consecutive_days: int,
    disease: str,
    score: float,
) -> dict:
    prompt = f"""Patient medication adherence alert:
Missed doses today: {missed_count}
Consecutive missed days: {consecutive_days}
Disease: {disease}
Recovery score: {score}/100

Return JSON: {{"alert_message": str, "risk_level": "low|medium|high", "doctor_notification": bool, "patient_guidance": str}}"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, dict) else {}


async def patient_chatbot(message: str, patient_context: dict) -> str:
    prompt = f"""Patient context: {json.dumps(patient_context, default=str)}
Patient message: "{message}"
Respond helpfully and empathetically. Do not give specific medical advice beyond what's in their record.
Keep response under 150 words. If urgent symptoms, suggest contacting doctor immediately."""
    return await _call_gemini(prompt, as_json=False)


async def doctor_chatbot(
    message: str,
    patient_context: dict,
    pipeline_context: dict,
) -> str:
    prompt = f"""Clinical context: {json.dumps(patient_context, default=str)}
Pipeline outputs: {json.dumps(pipeline_context, default=str)}
Doctor query: "{message}"
Provide evidence-based clinical decision support. Be concise and precise.
Remind that all recommendations require physician judgment."""
    return await _call_gemini(prompt, as_json=False)


async def search_medications(query: str) -> list[dict]:
    prompt = f"""Search for medications matching "{query}".
Return JSON array of top 10 matches: [{{"name": str, "generic_name": str, "class": str, "common_dosages": [str]}}]"""
    result = await _call_gemini(prompt, as_json=True)
    return result if isinstance(result, list) else []
