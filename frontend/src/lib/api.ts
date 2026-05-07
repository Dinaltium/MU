// lib/api.ts — Axios instance pointing to FastAPI backend
// All requests include the JWT from cookies automatically.

import axios from "axios";
import Cookies from "js-cookie";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

const api = axios.create({
  baseURL: API_V1,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Attach JWT Bearer token on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("rxbridge_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear token and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove("rxbridge_token");
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Auth ─────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data).then((r) => r.data),

  logout: () => api.post("/auth/logout").then((r) => r.data),

  me: () => api.get("/auth/me").then((r) => r.data),
};

// ─── Patients ─────────────────────────────────────────────────────────
export const patientsApi = {
  list: (limit = 20, offset = 0) =>
    api.get(`/patients/?limit=${limit}&offset=${offset}`).then((r) => r.data),

  get: (id: string) => api.get(`/patients/${id}`).then((r) => r.data),

  create: (data: PatientCreatePayload) =>
    api.post("/patients/", data).then((r) => r.data),
};

// ─── AI Assist & Consultations ────────────────────────────────────────
export const aiAssistApi = {
  // Triggers the 9-agent pipeline
  runPipeline: (diagnosisId: string, data: { image_base64?: string } = {}) =>
    api.post(`/ai/run-pipeline/${diagnosisId}`, data).then((r) => r.data),

  // Search for medications using Gemini/RxTerms
  searchMedications: (query: string) =>
    api.get(`/ai/medication-search?query=${encodeURIComponent(query)}`).then((r) => r.data),

  // Get common diseases
  getDiseaseList: () =>
    api.get("/ai/disease-list").then((r) => r.data),

  // Get a specific pipeline run status
  getRun: (runId: string) =>
    api.get(`/ai/run/${runId}`).then((r) => r.data),
};

// ─── Diagnoses ────────────────────────────────────────────────────────
export const diagnosesApi = {
  create: (data: DiagnosisCreatePayload) =>
    api.post("/diagnoses/", data).then((r) => r.data),

  listByPatient: (patientId: string) =>
    api.get(`/diagnoses/patient/${patientId}`).then((r) => r.data),
};

/**
 * NIH Clinical Tables API (Free, no key required)
 * Used as a fallback for high-speed autocomplete
 */
export const medicalSearchApi = {
  searchConditions: async (term: string) => {
    if (!term || term.length < 2) return [];
    const url = `https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?terms=${encodeURIComponent(term)}&sf=code,name&df=name&maxList=50`;
    const res = await axios.get(url);
    return (res.data[3] || []).map((row: any) => row[0]) as string[];
  },
};

// ─── Alerts ───────────────────────────────────────────────────────────
export const alertsApi = {
  list: (unreadOnly = false, limit = 20) =>
    api.get(`/notifications/?unread_only=${unreadOnly}&limit=${limit}`).then((r) => r.data),

  markRead: (alertId: string) =>
    api.post(`/notifications/${alertId}/read`).then((r) => r.data),
};

// ─── Monitoring ───────────────────────────────────────────────────────
export const monitoringApi = {
  checkin: (data: any) => 
    api.post("/recovery/checkin", data).then((r) => r.data),
    
  getScores: (patientId: string) =>
    api.get(`/recovery/scores/${patientId}`).then((r) => r.data),
};

// ─── Types ────────────────────────────────────────────────────────────
export interface PatientCreatePayload {
  name: string;
  age: number;
  gender?: string;
  location?: string;
  weight_kg?: number;
  renal_function?: number;
  conditions?: string[];
  allergies?: string[];
  medications?: string[];
}

export interface DiagnosisCreatePayload {
  patient_id: string;
  disease_name: string;
  severity: string;
  stage?: string;
  doctor_notes?: string;
}

export interface PipelineRun {
  id: string;
  pipeline_status: "running" | "complete" | "failed" | "hitl_pending";
  agent_outputs: any[];
  final_recommendation?: {
    top_diagnosis?: string;
    icd_code?: string;
    top_drug?: string;
    resistance_risk?: string;
    pkpd_ratio?: number;
    safety_flags?: string[];
    doctor_summary?: string;
    patient_explanation?: string;
    diagnoses?: Array<{ condition: string; probability: number; icd_code: string }>;
  };
  step_logs: string[];
  run_at: string;
  completed_at?: string;
}

