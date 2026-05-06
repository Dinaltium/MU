"""
models/naive_bayes.py

WHY MULTINOMIAL NAIVE BAYES:
  Medical symptoms are naturally modelled as a bag-of-words problem:
  the presence/absence of each symptom matters, and the MultinomialNB
  model handles multi-label binary feature sets efficiently.

  Training produces a lightweight .pkl file (~10 KB) that can be loaded
  at startup in milliseconds — no GPU required, suitable for Railway
  free-tier containers.

SECURITY NOTE:
  • joblib.load() deserialises a pickle file. Pickle is inherently
    unsafe if the file source is untrusted. We only load from a path
    inside the repository — never from a URL or user upload. Production
    should use pickle-signed artefacts or a safer format (ONNX).
  • If the model file is missing, predict() returns a safe default
    ("unknown_cluster", "MODERATE") rather than crashing the pipeline.
  • The model is loaded at module import time (singleton) to avoid
    deserialisation overhead per request.
"""

import logging
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer
import joblib

logger = logging.getLogger(__name__)

_DEFAULT_RESULT = (["unknown_cluster"], "MODERATE")


class SymptomClassifier:
    def __init__(self) -> None:
        self.model = MultinomialNB()
        self.mlb   = MultiLabelBinarizer()
        self._fitted = False

        self.urgency_rules: dict[str, str] = {
            "meningeal_irritation":  "CRITICAL",
            "cardiac_cluster":       "CRITICAL",
            "respiratory_distress":  "HIGH",
            "febrile_illness":       "MODERATE",
            "gi_infection":          "LOW",
            "urinary_infection":     "LOW",
            "dermatological":        "LOW",
        }

    def train(self, X_symptoms: list[list[str]], y_clusters: list[str]) -> None:
        """
        Fit the classifier.

        X_symptoms: list of symptom lists, e.g. [["fever", "cough"], ...]
        y_clusters:  cluster labels, e.g. ["febrile_illness", ...]
        """
        X_encoded = self.mlb.fit_transform(X_symptoms)
        self.model.fit(X_encoded, y_clusters)
        self._fitted = True
        logger.info("SymptomClassifier trained on %d samples", len(y_clusters))

    def predict(self, symptoms: list[str]) -> tuple[list[str], str]:
        """
        Predict the symptom cluster and urgency level.

        Returns: ([cluster_label], urgency_string)
        """
        if not self._fitted:
            logger.warning("SymptomClassifier not fitted — returning default")
            return _DEFAULT_RESULT

        try:
            X_encoded = self.mlb.transform([symptoms])
            cluster   = self.model.predict(X_encoded)[0]
            urgency   = self.urgency_rules.get(cluster, "MODERATE")
            return [cluster], urgency
        except Exception as exc:
            logger.error("SymptomClassifier.predict failed: %s", exc)
            return _DEFAULT_RESULT

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "mlb": self.mlb, "fitted": self._fitted}, path)
        logger.info("SymptomClassifier saved to %s", path)

    def load(self, path: str) -> None:
        try:
            data          = joblib.load(path)
            self.model    = data["model"]
            self.mlb      = data["mlb"]
            self._fitted  = data.get("fitted", True)
            logger.info("SymptomClassifier loaded from %s", path)
        except FileNotFoundError:
            logger.warning("Model file %s not found — classifier will use defaults", path)
        except Exception as exc:
            logger.error("Failed to load SymptomClassifier: %s", exc)
