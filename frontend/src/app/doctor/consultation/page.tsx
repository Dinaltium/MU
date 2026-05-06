"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { patientsApi, consultationsApi, type Consultation } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { PageSpinner, Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";
import { Stethoscope, CheckCircle, XCircle, Clock, ChevronRight, Activity, Search } from "lucide-react";
import { MedicalAutocomplete } from "@/components/ui/MedicalAutocomplete";

const SYMPTOM_OPTIONS = [
  "headache", "fever", "cough", "nausea", "vomiting", "diarrhoea",
  "chest_pain", "shortness_of_breath", "fatigue", "rash", "sore_throat",
  "neck_stiffness", "confusion", "abdominal_pain", "dysuria",
];
const REGIONS = ["south_india", "north_india", "default"];

function PipelineProgress({ updates }: { updates: string[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {updates.map((u, i) => {
        const [agent, status] = u.split(":");
        const cls = status === "complete" ? "done" : status === "error" ? "failed" : "running";
        return (
          <div key={i} className={`pipeline-step ${cls}`}>
            {cls === "done" && <CheckCircle size={12} />}
            {cls === "failed" && <XCircle size={12} />}
            {cls === "running" && <Spinner size={11} />}
            <span>{agent.replace(/([A-Z])/g, " $1").trim()}</span>
          </div>
        );
      })}
    </div>
  );
}

function ResultCard({ result }: { result: Consultation["pipeline_output"] }) {
  if (!result) return null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Diagnosis */}
      <div style={{ background: "var(--color-teal-light)", borderRadius: 12, padding: 12 }}>
        <p className="label-xs" style={{ color: "var(--color-teal-dark)", marginBottom: 4 }}>Primary Diagnosis</p>
        <p style={{ fontSize: 15, fontWeight: 700, color: "var(--color-teal-dark)" }}>
          {result.top_diagnosis?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
        </p>
        {result.icd_code && (
          <p style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-teal-dark)", opacity: 0.8, marginTop: 2 }}>ICD: {result.icd_code}</p>
        )}
      </div>

      {/* Differentials */}
      {result.diagnoses && result.diagnoses.length > 1 && (
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 8 }}>Differential Diagnoses</p>
          {result.diagnoses.map((d, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{d.condition.replace(/_/g, " ")}</span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>{(d.probability * 100).toFixed(0)}%</span>
                </div>
                <div style={{ height: 4, background: "var(--color-border)", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${d.probability * 100}%`, background: "var(--color-teal)", borderRadius: 4, transition: "width 0.6s ease" }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Drug */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 4 }}>Recommended Drug</p>
          <p style={{ fontSize: 14, fontWeight: 700 }}>{result.top_drug}</p>
        </div>
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 4 }}>Resistance Risk</p>
          <p style={{ fontSize: 14, fontWeight: 700, color: result.resistance_risk === "HIGH" ? "var(--color-rose)" : result.resistance_risk === "MODERATE" ? "var(--color-ember)" : "var(--color-teal)" }}>
            {result.resistance_risk}
          </p>
        </div>
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 4 }}>PK/PD Ratio</p>
          <p style={{ fontSize: 14, fontWeight: 700, fontFamily: "var(--font-mono)" }}>
            {result.pkpd_ratio !== undefined ? result.pkpd_ratio.toFixed(2) : "—"}
          </p>
        </div>
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 4 }}>Safety Flags</p>
          {result.safety_flags && result.safety_flags.length > 0
            ? result.safety_flags.map((f) => <Badge key={f} variant="rose">{f}</Badge>)
            : <p style={{ fontSize: 12, color: "var(--color-teal)" }}>None ✓</p>
          }
        </div>
      </div>

      {/* Summary */}
      {result.doctor_summary && (
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 6 }}>Clinical Summary (AI)</p>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.6 }}>{result.doctor_summary}</p>
        </div>
      )}
    </div>
  );
}

export default function ConsultationPage() {
  const { user } = useAuthStore();
  const [step, setStep] = useState<"form" | "running" | "done">("form");
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [region, setRegion] = useState("south_india");
  const [result, setResult] = useState<Consultation | null>(null);
  const [pollingId, setPollingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const { data: patients = [], isLoading: loadingPts } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(50),
    enabled: !!user,
  });

  // Poll consultation result every 2s
  const {} = useQuery({
    queryKey: ["consultation-poll", pollingId],
    queryFn: () => consultationsApi.get(pollingId!),
    enabled: !!pollingId,
    refetchInterval: 2000,
    select: (data: Consultation) => {
      if (data.status === "complete" || data.status === "failed") {
        setResult(data);
        setStep("done");
        setPollingId(null);
      }
      return data;
    },
  });

  const startMutation = useMutation({
    mutationFn: consultationsApi.start,
    onSuccess: (data: {consultation_id: string}) => {
      setPollingId(data.consultation_id);
      setStep("running");
    },
    onError: (e: unknown) => {
      const msg = (e as {response?:{data?:{detail?:string}}})?.response?.data?.detail;
      setError(msg || "Failed to start consultation.");
    },
  });

  function toggleSymptom(s: string) {
    setSymptoms((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPatientId) { setError("Select a patient."); return; }
    if (symptoms.length === 0) { setError("Select at least one symptom."); return; }
    setError("");
    startMutation.mutate({ patient_id: selectedPatientId, symptoms, region });
  }

  const selectedPatient = (patients as {id:string;name:string}[]).find((p) => p.id === selectedPatientId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--color-teal-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Stethoscope size={16} style={{ color: "var(--color-teal)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>New Consultation</h1>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
              AI-powered diagnosis and drug recommendation
            </p>
          </div>
          {step !== "form" && (
            <button className="btn btn-ghost" style={{ marginLeft: "auto", fontSize: 12 }}
              onClick={() => { setStep("form"); setResult(null); setPollingId(null); setSymptoms([]); setSelectedPatientId(""); }}>
              New
            </button>
          )}
        </div>
      </div>

      {step === "form" && (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Patient select */}
          <div className="card card-pad">
            <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Patient</p>
            {loadingPts ? <PageSpinner /> : (
              <select className="select" style={{ width: "100%" }}
                value={selectedPatientId} onChange={(e) => setSelectedPatientId(e.target.value)}>
                <option value="">— Select patient —</option>
                {(patients as {id:string;name:string;age:number}[]).map((p) => (
                  <option key={p.id} value={p.id}>{p.name} (Age {p.age})</option>
                ))}
              </select>
            )}
          </div>

          {/* Symptoms */}
          <div className="card card-pad" style={{ position: "relative", zIndex: 50 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <p style={{ fontSize: 13, fontWeight: 700 }}>Symptoms & Conditions</p>
              <span style={{ fontSize: 11, color: "var(--color-text-muted)" }}>{symptoms.length} selected</span>
            </div>
            <div style={{ marginBottom: 12 }}>
              <MedicalAutocomplete 
                type="condition" 
                placeholder="Search for symptoms (e.g. cough, pain)..."
                onSelect={(val) => { if (!symptoms.includes(val)) setSymptoms([...symptoms, val]); }} 
              />
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {SYMPTOM_OPTIONS.map((s) => {
                const active = symptoms.includes(s);
                return (
                  <button key={s} type="button" onClick={() => toggleSymptom(s)} style={{
                    padding: "5px 11px", borderRadius: 100, fontSize: 12, fontWeight: 500, cursor: "pointer",
                    border: "none",
                    background: active ? "var(--color-teal)" : "var(--color-canvas)",
                    color: active ? "#fff" : "var(--color-text-secondary)",
                    transition: "all 0.15s ease",
                  }}>
                    {s.replace(/_/g, " ")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Region */}
          <div className="card card-pad">
            <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Region (resistance patterns)</p>
            <div style={{ display: "flex", gap: 8 }}>
              {REGIONS.map((r) => (
                <button key={r} type="button" onClick={() => setRegion(r)} style={{
                  padding: "6px 14px", borderRadius: 100, fontSize: 12, fontWeight: 500, cursor: "pointer",
                  border: "none",
                  background: region === r ? "var(--color-teal)" : "var(--color-canvas)",
                  color: region === r ? "#fff" : "var(--color-text-secondary)",
                  transition: "all 0.15s",
                }}>
                  {r.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div style={{ padding: "9px 12px", background: "var(--color-rose-light)", borderRadius: 8, border: "1px solid rgba(244,63,94,0.2)", fontSize: 12, color: "#9F1239" }}>{error}</div>
          )}

          <div className="card card-pad">
            <button className="btn btn-primary" type="submit" disabled={startMutation.isPending} style={{ width: "100%", justifyContent: "center" }}>
              <Activity size={14} /> Start AI Consultation
            </button>
          </div>
        </form>
      )}

      {step === "running" && (
        <div className="card card-pad animate-fade-in" style={{ textAlign: "center" }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 14 }}>
            <Spinner size={28} />
          </div>
          <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Pipeline running…</p>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginBottom: 16 }}>
            Running 7 AI agents. This takes 10–20 seconds.
          </p>
          <div style={{ textAlign: "left", maxWidth: 280, margin: "0 auto" }}>
            <PipelineProgress updates={[
              "SymptomAnalysisAgent:running",
              "DiagnosisAgent:pending",
              "DrugRecommendationAgent:pending",
              "ResistanceCheckAgent:pending",
              "PatientSafetyAgent:pending",
              "ExplainabilityAgent:pending",
              "ReportAgent:pending",
            ]} />
          </div>
        </div>
      )}

      {step === "done" && result && (
        <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div className="card card-pad" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {result.status === "complete"
              ? <CheckCircle size={18} style={{ color: "var(--color-teal)" }} />
              : <XCircle size={18} style={{ color: "var(--color-rose)" }} />
            }
            <div>
              <p style={{ fontSize: 14, fontWeight: 700 }}>
                {result.status === "complete" ? "Consultation complete" : "Pipeline failed"}
              </p>
              <p style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
                Patient: {selectedPatient?.name}
              </p>
            </div>
            <Clock size={11} style={{ marginLeft: "auto", color: "var(--color-text-muted)" }} />
            <span style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
              {new Date(result.created_at).toLocaleTimeString()}
            </span>
          </div>
          {result.status === "complete" && <ResultCard result={result.pipeline_output} />}
          {result.status === "failed" && (
            <div style={{ padding: 16, background: "var(--color-rose-light)", borderRadius: 10, fontSize: 12, color: "#9F1239" }}>
              The pipeline encountered an error. Please check logs and retry.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
