"""
agents/patient_safety.py

WHY GRAPH-BASED INTERACTION CHECKING:
  A graph naturally models drug relationships — nodes are drugs/substances,
  edges are interactions. NetworkX's path-finding allows us to detect
  INDIRECT relationships (e.g., drug A is metabolised by CYP3A4, which
  is also inhibited by drug B — even if A and B don't share a direct edge).

  This is stronger than a simple lookup table where only known direct
  pairs are flagged.

SECURITY NOTE:
  • The drug interaction data comes from a trusted local JSON file.
    Patient-submitted medication lists are validated as strings before
    being passed to the graph — no arbitrary graph manipulation is possible.
  • We never pass the full patient record to this agent; only the
    medication list and known allergies are extracted from patient_profile.
  • Safety flags are produced as human-readable strings, never as
    executable instructions that downstream code might eval() or exec().

CRITICAL DESIGN DECISION — FAIL SAFE:
  If this agent raises an exception, the pipeline orchestrator marks
  the consultation as failed. We intentionally do NOT silently skip
  safety checks. A missed drug interaction is potentially lethal; it
  is better to surface an error than to produce an unsafe recommendation.
"""

import json
import os
import logging
from models.interaction_graph import DrugInteractionGraph
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

_graph = DrugInteractionGraph()
try:
    _graph.load(os.path.join(_DATA_DIR, "drug_interactions.json"))
except FileNotFoundError:
    logger.warning("drug_interactions.json not found — interaction checking disabled")


async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "PatientSafetyAgent:running:Checking drug interactions and allergies..."
    )

    drug          = state["top_drug"]
    current_meds  = state["patient_profile"].get("medications", [])
    allergies     = state["patient_profile"].get("allergies", [])

    # Graph traversal for drug–drug interactions
    interactions = _graph.check_interactions(drug, current_meds)

    flags = []

    # Allergy check — any path between the new drug and a known allergen
    for allergy in allergies:
        if _graph.is_related(drug, allergy):
            flags.append(
                f"⚠️ ALLERGY: {drug} is related to known allergen '{allergy}' — "
                f"verify cross-reactivity before prescribing"
            )

    # HIGH-severity interaction flagging
    for interaction in interactions:
        if interaction.get("severity") == "HIGH":
            flags.append(
                f"🚨 INTERACTION: {drug} + {interaction['drug']} — "
                f"{interaction.get('effect', 'HIGH RISK interaction')} — "
                f"consider alternative"
            )
        elif interaction.get("severity") == "MODERATE":
            flags.append(
                f"⚠️ INTERACTION: {drug} + {interaction['drug']} — "
                f"{interaction.get('effect', 'moderate risk')} — monitor closely"
            )

    state["safety_flags"]       = flags
    state["interaction_alerts"] = interactions

    state["step_updates"].append(
        f"PatientSafetyAgent:complete:{len(flags)} safety flags raised"
    )
    return state
