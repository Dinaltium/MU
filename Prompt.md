Yes, this is the final architecture. Let me break down everything you need to actually build this.

---

## Project Structure

```
rxbridge/
├── backend/
│   ├── agents/
│   │   ├── symptom_analysis.py
│   │   ├── diagnosis.py
│   │   ├── drug_recommendation.py
│   │   ├── resistance_check.py
│   │   ├── patient_safety.py
│   │   ├── explainability.py
│   │   ├── report.py
│   │   └── monitoring.py
│   ├── models/
│   │   ├── bayesian_network.py
│   │   ├── naive_bayes.py
│   │   ├── pkpd_model.py
│   │   ├── cusum.py
│   │   └── interaction_graph.py
│   ├── data/
│   │   ├── mic_database.json
│   │   ├── resistance_patterns.json
│   │   ├── drug_interactions.json
│   │   ├── drug_formulary.json
│   │   └── symptom_disease_map.json
│   ├── routers/
│   │   ├── auth.py
│   │   ├── consultations.py
│   │   ├── patients.py
│   │   ├── monitoring.py
│   │   └── alerts.py
│   ├── utils/
│   │   ├── db.py
│   │   ├── cache.py
│   │   ├── llm.py
│   │   └── telegram.py
│   ├── pipeline/
│   │   ├── orchestrator.py
│   │   └── state.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── doctor/
│   │   │   ├── dashboard/
│   │   │   ├── consultation/
│   │   │   ├── patients/
│   │   │   └── alerts/
│   │   ├── patient/
│   │   │   ├── dashboard/
│   │   │   ├── medications/
│   │   │   └── checkin/
│   │   └── auth/
│   └── components/
├── docker-compose.yml
└── .env
```

---

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL, -- 'doctor' or 'patient'
    telegram_handle VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    doctor_id UUID REFERENCES users(id),
    name VARCHAR NOT NULL,
    age INTEGER,
    gender VARCHAR,
    location VARCHAR,
    weight_kg FLOAT,
    renal_function FLOAT DEFAULT 1.0, -- GFR score
    conditions JSONB DEFAULT '[]',
    allergies JSONB DEFAULT '[]',
    medications JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consultations table
CREATE TABLE consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES patients(id),
    symptoms JSONB NOT NULL,
    pipeline_output JSONB,
    status VARCHAR DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recommendations table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID REFERENCES consultations(id),
    drug_name VARCHAR NOT NULL,
    diagnosis VARCHAR NOT NULL,
    resistance_risk VARCHAR, -- low/moderate/high
    efficacy_score FLOAT,
    safety_score FLOAT,
    doctor_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Monitoring checkins table
CREATE TABLE monitoring_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    consultation_id UUID REFERENCES consultations(id),
    feel_status VARCHAR NOT NULL, -- better/same/worse
    symptom_severity INTEGER, -- 1-10
    recovery_score FLOAT,
    cusum_value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL,
    target_type VARCHAR NOT NULL, -- doctor/patient
    alert_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL, -- low/moderate/critical
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resistance patterns table
CREATE TABLE resistance_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region VARCHAR NOT NULL,
    pathogen VARCHAR NOT NULL,
    drug_class VARCHAR NOT NULL,
    resistance_rate FLOAT NOT NULL,
    source VARCHAR NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Pipeline State

```python
# pipeline/state.py
from typing import TypedDict, List, Optional

class PipelineState(TypedDict):
    # Input
    patient_id: str
    doctor_id: str
    consultation_id: str
    symptoms: List[str]
    patient_profile: dict
    region: str

    # Agent outputs
    urgency_score: Optional[str]
    key_findings: Optional[List[str]]
    red_flags: Optional[List[str]]

    diagnoses: Optional[List[dict]]
    top_diagnosis: Optional[str]
    icd_code: Optional[str]

    drug_candidates: Optional[List[dict]]
    top_drug: Optional[str]

    resistance_risk: Optional[str]
    pkpd_ratio: Optional[float]
    mic_value: Optional[float]

    safety_flags: Optional[List[str]]
    interaction_alerts: Optional[List[str]]

    doctor_summary: Optional[str]
    patient_explanation: Optional[str]

    report_id: Optional[str]
    step_updates: List[str]
```

---

## Pipeline Orchestrator

```python
# pipeline/orchestrator.py
from agents import (
    symptom_analysis,
    diagnosis,
    drug_recommendation,
    resistance_check,
    patient_safety,
    explainability,
    report
)

async def run_pipeline(state: PipelineState) -> PipelineState:
    steps = [
        symptom_analysis.run,
        diagnosis.run,
        drug_recommendation.run,
        resistance_check.run,
        patient_safety.run,
        explainability.run,
        report.run
    ]

    for step in steps:
        try:
            state = await step(state)
        except Exception as e:
            state["step_updates"].append(
                f"{step.__module__}:failed:{str(e)}"
            )
            raise

    return state
```

---

## The 8 Agents

```python
# agents/symptom_analysis.py
from models.naive_bayes import SymptomClassifier
from pipeline.state import PipelineState

RED_FLAGS = {
    "neck_stiffness": "meningeal_irritation",
    "chest_pain": "cardiac_event",
    "difficulty_breathing": "respiratory_failure",
    "sudden_vision_loss": "neurological_emergency"
}

classifier = SymptomClassifier()
classifier.load("data/symptom_model.pkl")

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "SymptomAnalysisAgent:running:Analyzing symptoms..."
    )

    symptoms = state["symptoms"]
    cluster, urgency = classifier.predict(symptoms)

    # Red flag detection
    flags = []
    for symptom in symptoms:
        if symptom.lower() in RED_FLAGS:
            flags.append(RED_FLAGS[symptom.lower()])
            urgency = "CRITICAL"

    state["urgency_score"] = urgency
    state["key_findings"] = cluster
    state["red_flags"] = flags

    state["step_updates"].append(
        f"SymptomAnalysisAgent:complete:Urgency {urgency}, "
        f"{len(flags)} red flags detected"
    )
    return state
```

```python
# agents/diagnosis.py
from models.bayesian_network import DiagnosisNetwork
from pipeline.state import PipelineState

network = DiagnosisNetwork()
network.load("data/diagnosis_network.pkl")

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "DiagnosisAgent:running:Running Bayesian inference..."
    )

    results = network.infer(
        symptoms=state["key_findings"],
        age=state["patient_profile"]["age"],
        region=state["region"]
    )

    # Results come back as ranked list with probabilities
    state["diagnoses"] = results
    state["top_diagnosis"] = results[0]["condition"]
    state["icd_code"] = results[0]["icd_code"]

    state["step_updates"].append(
        f"DiagnosisAgent:complete:Top diagnosis "
        f"{results[0]['condition']} at "
        f"{results[0]['probability']}% confidence"
    )
    return state
```

```python
# agents/drug_recommendation.py
import json
from pipeline.state import PipelineState

with open("data/drug_formulary.json") as f:
    FORMULARY = json.load(f)

with open("data/resistance_patterns.json") as f:
    RESISTANCE = json.load(f)

def score_drug(drug, diagnosis, region, patient_profile):
    # Five axis scoring
    efficacy = drug.get("efficacy_rates", {}).get(diagnosis, 0.5)

    resistance_rate = RESISTANCE.get(region, {}).get(
        drug["class"], 0.1
    )
    resistance_score = 1 - resistance_rate

    safety_score = 1.0
    for condition in patient_profile.get("conditions", []):
        if condition in drug.get("contraindications", []):
            safety_score -= 0.5

    prior_response = patient_profile.get(
        "drug_responses", {}
    ).get(drug["name"], 0.5)

    availability = drug.get("availability_india", 1.0)

    # Weighted sum
    total = (
        efficacy * 0.35 +
        resistance_score * 0.30 +
        safety_score * 0.20 +
        prior_response * 0.10 +
        availability * 0.05
    )

    return round(total, 4)

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "DrugRecommendationAgent:running:Scoring drug candidates..."
    )

    diagnosis = state["top_diagnosis"]
    candidates = FORMULARY.get(diagnosis, [])

    scored = []
    for drug in candidates:
        score = score_drug(
            drug,
            diagnosis,
            state["region"],
            state["patient_profile"]
        )
        scored.append({**drug, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)

    state["drug_candidates"] = scored
    state["top_drug"] = scored[0]["name"]

    state["step_updates"].append(
        f"DrugRecommendationAgent:complete:"
        f"Top drug {scored[0]['name']} "
        f"with score {scored[0]['score']}"
    )
    return state
```

```python
# agents/resistance_check.py
import json
from models.pkpd_model import PKPDModel
from pipeline.state import PipelineState

with open("data/mic_database.json") as f:
    MIC_DB = json.load(f)

pkpd = PKPDModel()

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "ResistanceCheckAgent:running:Running PK/PD model..."
    )

    drug = state["top_drug"]
    diagnosis = state["top_diagnosis"]
    patient = state["patient_profile"]

    mic = MIC_DB.get(drug, {}).get(diagnosis, 1.0)

    achievable = pkpd.calculate_concentration(
        drug=drug,
        weight=patient.get("weight_kg", 70),
        renal_function=patient.get("renal_function", 1.0)
    )

    ratio = achievable / mic

    if ratio < 1:
        risk = "HIGH"
    elif ratio < 4:
        risk = "MODERATE"
    else:
        risk = "LOW"

    state["resistance_risk"] = risk
    state["pkpd_ratio"] = round(ratio, 2)
    state["mic_value"] = mic

    state["step_updates"].append(
        f"ResistanceCheckAgent:complete:"
        f"Resistance risk {risk}, PK/PD ratio {ratio:.2f}"
    )
    return state
```

```python
# agents/patient_safety.py
from models.interaction_graph import DrugInteractionGraph
from pipeline.state import PipelineState

graph = DrugInteractionGraph()
graph.load("data/drug_interactions.json")

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "PatientSafetyAgent:running:Checking interactions..."
    )

    drug = state["top_drug"]
    current_meds = state["patient_profile"].get("medications", [])
    allergies = state["patient_profile"].get("allergies", [])

    # Graph traversal for interactions
    interactions = graph.check_interactions(drug, current_meds)

    # Allergy check
    flags = []
    for allergy in allergies:
        if graph.is_related(drug, allergy):
            flags.append(
                f"ALLERGY: {drug} related to known allergy {allergy}"
            )

    for interaction in interactions:
        if interaction["severity"] == "HIGH":
            flags.append(
                f"INTERACTION: {drug} + "
                f"{interaction['drug']} = HIGH RISK"
            )

    state["safety_flags"] = flags
    state["interaction_alerts"] = interactions

    state["step_updates"].append(
        f"PatientSafetyAgent:complete:"
        f"{len(flags)} safety flags raised"
    )
    return state
```

```python
# agents/explainability.py
from utils.llm import get_llm
from pipeline.state import PipelineState

llm = get_llm()

DOCTOR_PROMPT = """
You are a clinical decision support system.
Generate a concise clinical summary for the doctor.

Diagnosis: {diagnosis} ({icd_code})
Recommended Drug: {drug}
Resistance Risk: {resistance_risk} (PK/PD ratio: {pkpd_ratio})
Safety Flags: {safety_flags}

Return a 3-4 sentence clinical summary covering
diagnosis confidence, drug rationale, resistance
risk, and recommended follow-up timeline.
"""

PATIENT_PROMPT = """
You are a friendly health assistant explaining
a diagnosis to a patient in simple language.

Diagnosis: {diagnosis}
Drug: {drug}
Region: {region}

Explain in 4-5 simple sentences:
1. What is wrong
2. What the medicine does
3. Why completing the course matters
4. What side effects to watch for
5. When to seek urgent help

Use warm, clear, non-scary language.
"""

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "ExplainabilityAgent:running:Generating explanations..."
    )

    doctor_summary = await llm.invoke(
        DOCTOR_PROMPT.format(
            diagnosis=state["top_diagnosis"],
            icd_code=state["icd_code"],
            drug=state["top_drug"],
            resistance_risk=state["resistance_risk"],
            pkpd_ratio=state["pkpd_ratio"],
            safety_flags=state["safety_flags"]
        )
    )

    patient_explanation = await llm.invoke(
        PATIENT_PROMPT.format(
            diagnosis=state["top_diagnosis"],
            drug=state["top_drug"],
            region=state["region"]
        )
    )

    state["doctor_summary"] = doctor_summary
    state["patient_explanation"] = patient_explanation

    state["step_updates"].append(
        "ExplainabilityAgent:complete:Explanations generated"
    )
    return state
```

```python
# agents/report.py
from utils.db import get_pool
from pipeline.state import PipelineState
import json

async def run(state: PipelineState) -> PipelineState:
    state["step_updates"].append(
        "ReportAgent:running:Writing consultation record..."
    )

    pool = await get_pool()
    async with pool.acquire() as conn:

        # Update consultation with full pipeline output
        await conn.execute(
            """
            UPDATE consultations
            SET pipeline_output = $1::jsonb,
                status = 'complete'
            WHERE id = $2::uuid
            """,
            json.dumps({
                "diagnoses": state["diagnoses"],
                "top_diagnosis": state["top_diagnosis"],
                "icd_code": state["icd_code"],
                "top_drug": state["top_drug"],
                "resistance_risk": state["resistance_risk"],
                "pkpd_ratio": state["pkpd_ratio"],
                "safety_flags": state["safety_flags"],
                "doctor_summary": state["doctor_summary"],
                "patient_explanation": state["patient_explanation"]
            }),
            state["consultation_id"]
        )

        # Write recommendation record
        row = await conn.fetchrow(
            """
            INSERT INTO recommendations
            (consultation_id, drug_name, diagnosis,
             resistance_risk, doctor_approved)
            VALUES ($1::uuid, $2, $3, $4, false)
            RETURNING id
            """,
            state["consultation_id"],
            state["top_drug"],
            state["top_diagnosis"],
            state["resistance_risk"]
        )

    state["report_id"] = str(row["id"])
    state["step_updates"].append(
        f"ReportAgent:complete:Report {state['report_id']} written"
    )
    return state
```

---

## The Scientific Models

```python
# models/naive_bayes.py
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer
import joblib
import numpy as np

class SymptomClassifier:
    def __init__(self):
        self.model = MultinomialNB()
        self.mlb = MultiLabelBinarizer()
        self.urgency_rules = {
            "meningeal_irritation": "CRITICAL",
            "cardiac_cluster": "CRITICAL",
            "respiratory_distress": "HIGH",
            "febrile_illness": "MODERATE",
            "gi_infection": "LOW"
        }

    def train(self, X_symptoms, y_clusters):
        X_encoded = self.mlb.fit_transform(X_symptoms)
        self.model.fit(X_encoded, y_clusters)

    def predict(self, symptoms):
        X_encoded = self.mlb.transform([symptoms])
        cluster = self.model.predict(X_encoded)[0]
        urgency = self.urgency_rules.get(cluster, "MODERATE")
        return cluster, urgency

    def save(self, path):
        joblib.dump(
            {"model": self.model, "mlb": self.mlb}, path
        )

    def load(self, path):
        data = joblib.load(path)
        self.model = data["model"]
        self.mlb = data["mlb"]
```

```python
# models/bayesian_network.py
from pgmpy.models import BayesianNetwork
from pgmpy.inference import VariableElimination
import joblib

class DiagnosisNetwork:
    def __init__(self):
        self.model = None
        self.inference = None

        # ICD-10 mapping
        self.icd_map = {
            "bacterial_meningitis": "G00.9",
            "viral_meningitis": "A87.9",
            "pneumonia": "J18.9",
            "typhoid": "A01.0",
            "dengue": "A90",
            "malaria": "B54",
            "urinary_tract_infection": "N39.0",
            "tuberculosis": "A15.9"
        }

    def build(self):
        # Define network structure
        # Edges represent causal relationships
        self.model = BayesianNetwork([
            ("fever", "bacterial_meningitis"),
            ("neck_stiffness", "bacterial_meningitis"),
            ("photophobia", "bacterial_meningitis"),
            ("fever", "typhoid"),
            ("abdominal_pain", "typhoid"),
            ("fever", "malaria"),
            ("chills", "malaria"),
            ("cough", "pneumonia"),
            ("fever", "pneumonia"),
            ("dysuria", "urinary_tract_infection"),
            ("fever", "urinary_tract_infection")
        ])

    def infer(self, symptoms, age, region):
        evidence = {s: 1 for s in symptoms}
        results = []

        for disease in self.icd_map.keys():
            try:
                query = self.inference.query(
                    variables=[disease],
                    evidence=evidence
                )
                prob = query.values[1]
                results.append({
                    "condition": disease,
                    "probability": round(prob * 100, 1),
                    "icd_code": self.icd_map[disease]
                })
            except Exception:
                continue

        results.sort(
            key=lambda x: x["probability"], reverse=True
        )
        return results[:3]

    def save(self, path):
        joblib.dump(self.model, path)

    def load(self, path):
        self.model = joblib.load(path)
        self.inference = VariableElimination(self.model)
```

```python
# models/pkpd_model.py
import json

# One compartment PK model constants
PK_PARAMS = {
    "amoxicillin": {
        "bioavailability": 0.90,
        "volume_distribution": 0.26,
        "half_life_hours": 1.3,
        "standard_dose_mg": 500,
        "dosing_interval_hours": 8
    },
    "azithromycin": {
        "bioavailability": 0.37,
        "volume_distribution": 31.1,
        "half_life_hours": 68,
        "standard_dose_mg": 500,
        "dosing_interval_hours": 24
    },
    "ciprofloxacin": {
        "bioavailability": 0.70,
        "volume_distribution": 2.5,
        "half_life_hours": 4,
        "standard_dose_mg": 500,
        "dosing_interval_hours": 12
    }
}

class PKPDModel:
    def calculate_concentration(
        self, drug, weight, renal_function=1.0
    ):
        params = PK_PARAMS.get(drug.lower())
        if not params:
            return 1.0  # Default fallback

        import math

        dose = params["standard_dose_mg"]
        F = params["bioavailability"]
        Vd = params["volume_distribution"] * weight
        t_half = params["half_life_hours"] / renal_function
        tau = params["dosing_interval_hours"]

        # Peak concentration at steady state
        ke = 0.693 / t_half
        C_max = (F * dose / Vd) * (
            1 / (1 - math.exp(-ke * tau))
        )

        # Average steady state concentration
        C_avg = (F * dose) / (Vd * ke * tau)

        return round(C_avg, 4)
```

```python
# models/cusum.py
import numpy as np

class CUSUMMonitor:
    def __init__(self, target=70, slack=5, threshold=10):
        # target: expected recovery score
        # slack: allowable deviation
        # threshold: alert threshold
        self.target = target
        self.slack = slack
        self.threshold = threshold

    def update(self, scores: list) -> dict:
        if len(scores) < 2:
            return {
                "cusum_value": 0,
                "alert": False,
                "trend": "stable"
            }

        cusum = 0
        for score in scores:
            deviation = self.target - score - self.slack
            cusum = max(0, cusum + deviation)

        alert = cusum > self.threshold

        recent = scores[-3:] if len(scores) >= 3 else scores
        delta = recent[-1] - recent[0]
        trend = (
            "improving" if delta > 5
            else "declining" if delta < -5
            else "stable"
        )

        return {
            "cusum_value": round(cusum, 2),
            "alert": alert,
            "trend": trend,
            "message": (
                "Recovery significantly below expected "
                "trajectory — consider reviewing treatment"
                if alert else "Recovery on track"
            )
        }
```

```python
# models/interaction_graph.py
import networkx as nx
import json

class DrugInteractionGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def load(self, path):
        with open(path) as f:
            data = json.load(f)

        for interaction in data:
            self.graph.add_edge(
                interaction["drug_a"],
                interaction["drug_b"],
                severity=interaction["severity"],
                effect=interaction["effect"]
            )

    def check_interactions(self, new_drug, current_meds):
        interactions = []
        for med in current_meds:
            if self.graph.has_edge(new_drug, med):
                edge = self.graph[new_drug][med]
                interactions.append({
                    "drug": med,
                    "severity": edge["severity"],
                    "effect": edge["effect"]
                })
        return interactions

    def is_related(self, drug, substance):
        return self.graph.has_node(substance) and \
               nx.has_path(self.graph, drug, substance)
```

---

## Monitoring Service

```python
# agents/monitoring.py
import asyncio
from models.cusum import CUSUMMonitor
from utils.db import get_pool
from utils.telegram import send_alert

monitor = CUSUMMonitor()

async def run_monitoring_cycle():
    pool = await get_pool()
    async with pool.acquire() as conn:

        # Get all active consultations
        active = await conn.fetch(
            """
            SELECT c.id, c.patient_id, c.doctor_id,
                   p.name as patient_name
            FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            WHERE c.status = 'complete'
            AND c.created_at > NOW() - INTERVAL '14 days'
            """
        )

        for consultation in active:
            # Get all checkins for this consultation
            checkins = await conn.fetch(
                """
                SELECT recovery_score, created_at
                FROM monitoring_checkins
                WHERE consultation_id = $1::uuid
                ORDER BY created_at ASC
                """,
                consultation["id"]
            )

            if len(checkins) < 2:
                continue

            scores = [c["recovery_score"] for c in checkins]
            result = monitor.update(scores)

            # Update latest checkin with cusum value
            await conn.execute(
                """
                UPDATE monitoring_checkins
                SET cusum_value = $1
                WHERE consultation_id = $2::uuid
                AND created_at = (
                    SELECT MAX(created_at)
                    FROM monitoring_checkins
                    WHERE consultation_id = $2::uuid
                )
                """,
                result["cusum_value"],
                consultation["id"]
            )

            # Fire alert if CUSUM threshold exceeded
            if result["alert"]:
                await conn.execute(
                    """
                    INSERT INTO alerts
                    (target_id, target_type, alert_type,
                     severity, message)
                    VALUES ($1::uuid, 'doctor', 'treatment_failure',
                            'HIGH', $2)
                    """,
                    consultation["doctor_id"],
                    f"Patient {consultation['patient_name']}: "
                    f"{result['message']}"
                )

                await send_alert(
                    consultation["doctor_id"],
                    consultation["patient_name"],
                    result["message"]
                )

# Run every 6 hours
async def start_monitoring():
    while True:
        await run_monitoring_cycle()
        await asyncio.sleep(21600)
```

---

## Main FastAPI App

```python
# main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, consultations, patients, alerts, monitoring
from utils.db import init_db
from agents.monitoring import start_monitoring

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(start_monitoring())
    yield

app = FastAPI(
    title="RxBridge API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(patients.router, prefix="/api/patients")
app.include_router(
    consultations.router, prefix="/api/consultations"
)
app.include_router(alerts.router, prefix="/api/alerts")
app.include_router(monitoring.router, prefix="/api/monitoring")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "RxBridge API"}
```

---

## Requirements

```txt
# requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.32.1
asyncpg==0.30.0
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
bcrypt==4.1.2
groq==0.13.0
scikit-learn==1.5.0
pgmpy==0.1.26
networkx==3.4.2
numpy==1.26.4
redis==5.0.1
httpx==0.28.1
sse-starlette==2.1.3
python-multipart==0.0.9
joblib==1.4.2
```

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@neon.tech/rxbridge
REDIS_URL=redis://localhost:6379
GROQ_API_KEY=your_groq_key
SECRET_KEY=your_jwt_secret
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_FAMILY_CHANNEL_ID=your_channel_id
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

---

## Deployment

```
Backend  →  Railway (free tier, Docker deploy)
Frontend →  Vercel (zero config Next.js)
Database →  Neon PostgreSQL (already familiar)
Cache    →  Upstash Redis (serverless, free tier)
```

Push to GitHub, connect Railway to your backend repo, connect Vercel to your frontend repo, set environment variables in both dashboards. Everything is live in under 20 minutes.

---

This is everything you need to start building. The scientific models are the priority — get the Naive Bayes classifier and Bayesian Network trained first on even a small synthetic dataset, because those are what judges will ask about. Everything else is infrastructure you already know how to build from Healynx.