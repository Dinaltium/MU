// lib/api.ts — Axios instance pointing to FastAPI backend
// All requests include the JWT from cookies automatically.

import axios from "axios";
import Cookies from "js-cookie";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
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
  register: (data: { email: string; password: string; name: string; role: string }) =>
    api.post("/api/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data).then((r) => r.data),

  logout: () => api.post("/api/auth/logout").then((r) => r.data),

  me: () => api.get("/api/auth/me").then((r) => r.data),
};

// ─── Patients ─────────────────────────────────────────────────────────
export const patientsApi = {
  list: (limit = 20, offset = 0) =>
    api.get(`/api/patients/?limit=${limit}&offset=${offset}`).then((r) => r.data),

  get: (id: string) => api.get(`/api/patients/${id}`).then((r) => r.data),

  create: (data: PatientCreatePayload) =>
    api.post("/api/patients/", data).then((r) => r.data),
};

// ─── Consultations ────────────────────────────────────────────────────
export const consultationsApi = {
  start: (data: { patient_id: string; symptoms: string[]; region: string }) =>
    api.post("/api/consultations/", data).then((r) => r.data),

  get: (id: string) => api.get<Consultation>(`/api/consultations/${id}`).then(r => r.data),
};

/**
 * NIH Clinical Tables API (Free, no key required)
 * Used for standardized medical autocomplete
 */
export const medicalSearchApi = {
  // Search ICD-10-CM (Diseases/Conditions)
  searchConditions: async (term: string) => {
    if (!term || term.length < 2) return [];
    // sf=code,name: search in both codes and names; df=name: return names at index 3
    const url = `https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?terms=${encodeURIComponent(term)}&sf=code,name&df=name&maxList=50`;
    const res = await axios.get(url);
    // res.data[3] is [[name1], [name2], ...]
    return (res.data[3] || []).map((row: any) => row[0]) as string[];
  },

  // Search RxTerms (User-friendly Medications)
  searchMedications: async (term: string) => {
    if (!term || term.length < 2) return [];
    // sf=DISPLAY_NAME,DISPLAY_NAME_SYNONYM: search in names and synonyms; df=DISPLAY_NAME: return names at index 3
    const url = `https://clinicaltables.nlm.nih.gov/api/rxterms/v1/search?terms=${encodeURIComponent(term)}&sf=DISPLAY_NAME,DISPLAY_NAME_SYNONYM&df=DISPLAY_NAME&maxList=50`;
    const res = await axios.get(url);
    // res.data[3] is [[name1], [name2], ...]
    return (res.data[3] || []).map((row: any) => row[0]) as string[];
  },
};

// ─── Alerts ───────────────────────────────────────────────────────────
export const alertsApi = {
  list: (unreadOnly = false, limit = 20) =>
    api.get(`/api/alerts/?unread_only=${unreadOnly}&limit=${limit}`).then((r) => r.data),

  markRead: (alertId: string) =>
    api.post(`/api/alerts/${alertId}/read`).then((r) => r.data),
};

// ─── Monitoring ───────────────────────────────────────────────────────
export const monitoringApi = {
  checkin: (data: {
    consultation_id: string;
    feel_status: "better" | "same" | "worse";
    symptom_severity: number;
  }) => api.post("/api/monitoring/checkin", data).then((r) => r.data),
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

export interface Patient {
  id: string;
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

export interface Alert {
  id: string;
  alert_type: string;
  severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  message: string;
  read: boolean;
  created_at: string;
}

export interface Consultation {
  id: string;
  status: "running" | "complete" | "failed";
  pipeline_output?: {
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
  patient_explanation?: string;
  created_at: string;
}
