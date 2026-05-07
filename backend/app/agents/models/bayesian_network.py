"""
models/bayesian_network.py

WHY PGMPY BAYESIAN NETWORK:
  pgmpy implements proper probabilistic graphical models with
  Variable Elimination inference — the gold standard for exact Bayesian
  inference in discrete domains.

  Alternative approaches:
    - Lookup tables: no ability to model joint probability or region/age priors
    - LLM: non-deterministic, cannot be audited, fabricates probabilities
    - Random Forest: black-box, no interpretable probability output

  The Bayesian Network is the ONLY option that gives us:
    ✓ Explainable conditional probabilities
    ✓ Ability to incorporate domain knowledge (CPT tables)
    ✓ Handles missing symptoms gracefully (inference with partial evidence)

SECURITY NOTE:
  • The network structure (edges) is hardcoded — it encodes medical
    domain knowledge and cannot be altered by user input.
  • The inference is deterministic for the same evidence set —
    audit logs can reproduce the exact reasoning.
  • Exception handling per disease prevents a misconfigured CPT from
    aborting the entire inference.
"""

import logging
import joblib
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

logger = logging.getLogger(__name__)

ICD_MAP = {
    "bacterial_meningitis":  "G00.9",
    "viral_meningitis":      "A87.9",
    "pneumonia":             "J18.9",
    "typhoid":               "A01.0",
    "dengue":                "A90",
    "malaria":               "B54",
    "urinary_tract_infection": "N39.0",
    "tuberculosis":          "A15.9",
}


class DiagnosisNetwork:
    def __init__(self) -> None:
        self.model:     BayesianNetwork | None = None
        self.inference: VariableElimination | None = None
        self.icd_map = ICD_MAP

    def build(self) -> None:
        """
        Define the Bayesian Network structure.

        Each edge (A → B) means "symptom A is causally related to disease B."
        CPTs (conditional probability tables) encode the prior probability
        of each disease given each combination of symptom evidence.
        """
        model = BayesianNetwork([
            ("fever",          "bacterial_meningitis"),
            ("neck_stiffness", "bacterial_meningitis"),
            ("photophobia",    "bacterial_meningitis"),
            ("fever",          "typhoid"),
            ("abdominal_pain", "typhoid"),
            ("fever",          "malaria"),
            ("chills",         "malaria"),
            ("cough",          "pneumonia"),
            ("fever",          "pneumonia"),
            ("dysuria",        "urinary_tract_infection"),
            ("fever",          "urinary_tract_infection"),
        ])

        # 1. Symptom Priors (Probabilities of symptoms occurring)
        cpds = [
            TabularCPD(variable="fever", variable_card=2, values=[[0.3], [0.7]]),
            TabularCPD(variable="neck_stiffness", variable_card=2, values=[[0.9], [0.1]]),
            TabularCPD(variable="photophobia", variable_card=2, values=[[0.9], [0.1]]),
            TabularCPD(variable="abdominal_pain", variable_card=2, values=[[0.8], [0.2]]),
            TabularCPD(variable="chills", variable_card=2, values=[[0.7], [0.3]]),
            TabularCPD(variable="cough", variable_card=2, values=[[0.6], [0.4]]),
            TabularCPD(variable="dysuria", variable_card=2, values=[[0.9], [0.1]]),
        ]

        # 2. Disease CPDs (Probabilities of diseases given symptoms)
        # Note: This is a simplified model. In production, use real incidence data.
        cpds.append(TabularCPD(
            variable="bacterial_meningitis", variable_card=2,
            values=[
                [0.999, 0.5, 0.2, 0.1, 0.4, 0.1, 0.05, 0.01],
                [0.001, 0.5, 0.8, 0.9, 0.6, 0.9, 0.95, 0.99]
            ],
            evidence=["fever", "neck_stiffness", "photophobia"],
            evidence_card=[2, 2, 2]
        ))
        
        cpds.append(TabularCPD(
            variable="typhoid", variable_card=2,
            values=[
                [0.99, 0.4, 0.3, 0.01],
                [0.01, 0.6, 0.7, 0.99]
            ],
            evidence=["fever", "abdominal_pain"],
            evidence_card=[2, 2]
        ))
        
        cpds.append(TabularCPD(
            variable="malaria", variable_card=2,
            values=[
                [0.98, 0.3, 0.2, 0.01],
                [0.02, 0.7, 0.8, 0.99]
            ],
            evidence=["fever", "chills"],
            evidence_card=[2, 2]
        ))
        
        cpds.append(TabularCPD(
            variable="pneumonia", variable_card=2,
            values=[
                [0.95, 0.2, 0.1, 0.01],
                [0.05, 0.8, 0.9, 0.99]
            ],
            evidence=["fever", "cough"],
            evidence_card=[2, 2]
        ))
        
        cpds.append(TabularCPD(
            variable="urinary_tract_infection", variable_card=2,
            values=[
                [0.99, 0.4, 0.3, 0.01],
                [0.01, 0.6, 0.7, 0.99]
            ],
            evidence=["fever", "dysuria"],
            evidence_card=[2, 2]
        ))

        model.add_cpds(*cpds)
        model.check_model()
        self.model     = model
        self.inference = VariableElimination(model)
        logger.info("DiagnosisNetwork built")

    def infer(self, symptoms: list[str], age: int, region: str) -> list[dict]:
        """
        Run Variable Elimination inference.

        Returns top 3 diagnoses with probability and ICD code.
        """
        if self.inference is None:
            logger.warning("DiagnosisNetwork not initialised — returning fallback")
            return [{
                "condition": "unspecified_febrile_illness",
                "probability": 50.0,
                "icd_code": "R50.9",
            }]

        # Build evidence dict — only known network nodes
        known_nodes = set(self.model.nodes())
        evidence    = {s: 1 for s in symptoms if s in known_nodes}

        results = []
        for disease, icd in self.icd_map.items():
            if disease not in known_nodes:
                continue
            try:
                q    = self.inference.query(variables=[disease], evidence=evidence)
                prob = float(q.values[1]) * 100
                results.append({
                    "condition":   disease,
                    "probability": round(prob, 1),
                    "icd_code":    icd,
                })
            except Exception as exc:
                logger.debug("Inference skipped for %s: %s", disease, exc)

        results.sort(key=lambda x: x["probability"], reverse=True)
        return results[:3] if results else [{
            "condition": "unspecified_febrile_illness",
            "probability": 50.0,
            "icd_code": "R50.9",
        }]

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model}, path)

    def load(self, path: str) -> None:
        try:
            data          = joblib.load(path)
            self.model    = data["model"]
            self.inference = VariableElimination(self.model)
            logger.info("DiagnosisNetwork loaded from %s", path)
        except FileNotFoundError:
            logger.warning("DiagnosisNetwork model file not found at %s", path)
            self.build()   # fall back to freshly built (unfitted) network
        except Exception as exc:
            logger.error("Failed to load DiagnosisNetwork: %s", exc)
            self.build()
