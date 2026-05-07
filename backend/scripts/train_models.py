# ── Windows DLL Fix ──
import sys
if sys.platform == "win32":
    import types
    mock_torch = types.ModuleType("torch")
    mock_torch.__version__ = "2.0.0"
    mock_torch.nn = types.ModuleType("torch.nn")
    mock_torch.optim = types.ModuleType("torch.optim")
    mock_torch.Tensor = type("Tensor", (), {})
    mock_torch.float32 = "float32"
    sys.modules["torch"] = mock_torch
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.agents.models.naive_bayes import SymptomClassifier
from app.agents.models.bayesian_network import DiagnosisNetwork

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def train_symptom_classifier():
    logger.info("Training Symptom Classifier (Naive Bayes)...")
    classifier = SymptomClassifier()
    
    # Sample training data
    X = [
        ["fever", "cough", "fatigue"], ["fever", "cough", "shortness_of_breath"], # Respiratory
        ["nausea", "vomiting", "diarrhea"], ["stomach_pain", "nausea"], # GI
        ["headache", "neck_stiffness", "sensitivity_to_light"], # Meningeal
        ["chest_pain", "shortness_of_breath", "sweating"], # Cardiac
        ["skin_rash", "itching"], # Dermatological
        ["frequent_urination", "burning_sensation"], # Urinary
        ["fever", "chills", "muscle_ache"] # Febrile
    ]
    y = [
        "respiratory_distress", "respiratory_distress",
        "gi_infection", "gi_infection",
        "meningeal_irritation",
        "cardiac_cluster",
        "dermatological",
        "urinary_infection",
        "febrile_illness"
    ]
    
    classifier.train(X, y)
    classifier.save(os.path.join(DATA_DIR, "symptom_model.pkl"))

def build_diagnosis_network():
    logger.info("Building Diagnosis Network (Bayesian)...")
    network = DiagnosisNetwork()
    network.build()
    network.save(os.path.join(DATA_DIR, "diagnosis_network.pkl"))

if __name__ == "__main__":
    train_symptom_classifier()
    build_diagnosis_network()
    logger.info("All clinical models generated successfully in backend/data/")
