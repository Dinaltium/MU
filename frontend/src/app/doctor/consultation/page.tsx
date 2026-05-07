"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { patientsApi, aiAssistApi, diagnosesApi, type PipelineRun } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { PageSpinner, Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";
import { Stethoscope, CheckCircle, XCircle, Clock, Activity, AlertCircle } from "lucide-react";
import { MedicalAutocomplete } from "@/components/ui/MedicalAutocomplete";

const SYMPTOM_OPTIONS = [
  "headache", "fever", "cough", "nausea", "vomiting", "diarrhoea",
  "chest_pain", "shortness_of_breath", "fatigue", "rash", "sore_throat",
  "neck_stiffness", "confusion", "abdominal_pain", "dysuria",
];

function PipelineProgress({ logs }: { logs: string[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {logs.map((log, i) => {
        const isDone = log.toLowerCase().includes("complete") || log.toLowerCase().includes("finish");
        const isError = log.toLowerCase().includes("error") || log.toLowerCase().includes("fail");
        const cls = isDone ? "done" : isError ? "failed" : "running";
        return (
          <div key={i} className={`pipeline-step ${cls}`}>
            {isDone && <CheckCircle size={12} />}
            {isError && <XCircle size={12} />}
            {!isDone && !isError && <Spinner size={11} />}
            <span>{log}</span>
          </div>
        );
      })}
    </div>
  );
}

function ResultCard({ run }: { run: PipelineRun }) {
  const result = run.final_recommendation;
  if (!result) return null;
  
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "var(--spacing-bento-gap)" }}>
      {/* Column 1: Diagnosis & Summary */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-bento-gap)" }}>
        <div className="card card-pad" style={{ background: "var(--color-teal-light)" }}>
          <p className="label-xs" style={{ color: "var(--color-teal-dark)", marginBottom: 4 }}>Primary Diagnosis</p>
          <p style={{ fontSize: 18, fontWeight: 700, color: "var(--color-teal-dark)" }}>
            {result.top_diagnosis?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
          </p>
          {result.icd_code && (
            <p style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-teal-dark)", opacity: 0.8, marginTop: 4 }}>
              Standardized ICD: {result.icd_code}
            </p>
          )}
        </div>

        <div className="card card-pad">
          <p className="label-xs" style={{ marginBottom: 8 }}>Clinical Reasoning</p>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
            {result.doctor_summary}
          </p>
        </div>
        
        <div className="card card-pad" style={{ background: "var(--color-canvas)" }}>
          <p className="label-xs" style={{ marginBottom: 6 }}>Pipeline Trace Logs</p>
          <div style={{ maxHeight: 150, overflowY: "auto", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
            {run.step_logs.map((log, i) => <div key={i} style={{ marginBottom: 2 }}>{log}</div>)}
          </div>
        </div>
      </div>

      {/* Column 2: Treatment & Safety */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-bento-gap)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-bento-gap)" }}>
          <div className="card card-pad">
            <p className="label-xs" style={{ marginBottom: 4 }}>Best Fit Drug</p>
            <p style={{ fontSize: 15, fontWeight: 700 }}>{result.top_drug}</p>
          </div>
          <div className="card card-pad">
            <p className="label-xs" style={{ marginBottom: 4 }}>Resistance Risk</p>
            <Badge variant={result.resistance_risk === "HIGH" ? "rose" : result.resistance_risk === "MODERATE" ? "ember" : "teal"}>
              {result.resistance_risk}
            </Badge>
          </div>
        </div>

        <div className="card card-pad">
          <p className="label-xs" style={{ marginBottom: 8 }}>Safety & Interaction Audit</p>
          {result.safety_flags && result.safety_flags.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {result.safety_flags.map((f) => <Badge key={f} variant="rose">{f}</Badge>)}
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--color-teal)" }}>
              <CheckCircle size={14} />
              <span style={{ fontSize: 12, fontWeight: 600 }}>No Contraindications Found</span>
            </div>
          )}
        </div>

        {result.diagnoses && result.diagnoses.length > 1 && (
          <div className="card card-pad">
            <p className="label-xs" style={{ marginBottom: 10 }}>Differential Probabilities</p>
            {result.diagnoses.map((d, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{d.condition}</span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>{(d.probability * 100).toFixed(1)}%</span>
                </div>
                <div style={{ height: 6, background: "var(--color-canvas)", borderRadius: 100, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${d.probability * 100}%`, background: "var(--color-teal)", borderRadius: 100 }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ConsultationPage() {
  const { user } = useAuthStore();
  const [step, setStep] = useState<"form" | "running" | "done">("form");
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [severity, setSeverity] = useState("mild");
  const [runData, setRunData] = useState<PipelineRun | null>(null);
  const [pollingId, setPollingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const { data: patients = [], isLoading: loadingPts } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(50),
    enabled: !!user,
  });

  // Poll for pipeline status
  const {} = useQuery({
    queryKey: ["pipeline-run", pollingId],
    queryFn: () => aiAssistApi.getRun(pollingId!),
    enabled: !!pollingId,
    refetchInterval: 1500,
    select: (data: PipelineRun) => {
      if (data.pipeline_status === "complete" || data.pipeline_status === "failed") {
        setRunData(data);
        setStep("done");
        setPollingId(null);
      } else {
        setRunData(data); // Update logs while running
      }
      return data;
    },
  });

  const startMutation = useMutation({
    mutationFn: async (payload: { patient_id: string; symptoms: string[]; severity: string }) => {
      // 1. Create a placeholder diagnosis first
      const diag = await diagnosesApi.create({
        patient_id: payload.patient_id,
        disease_name: payload.symptoms[0] || "General Consultation",
        severity: payload.severity,
        doctor_notes: `Symptoms: ${payload.symptoms.join(", ")}`,
      });
      // 2. Trigger the pipeline
      return aiAssistApi.runPipeline(diag.id);
    },
    onSuccess: (data: PipelineRun) => {
      setPollingId(data.id);
      setRunData(data);
      setStep("running");
    },
    onError: (e: any) => {
      setError(e.response?.data?.detail || "Could not start AI pipeline.");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPatientId) { setError("Select a patient."); return; }
    if (symptoms.length === 0) { setError("Select at least one symptom."); return; }
    setError("");
    startMutation.mutate({ patient_id: selectedPatientId, symptoms, severity });
  }

  const selectedPatient = (patients as any[]).find((p) => p.id === selectedPatientId);

  return (
    <div className="bento-main">
      {/* Header Card */}
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 42, height: 42, borderRadius: 12, background: "var(--color-teal-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Stethoscope size={20} style={{ color: "var(--color-teal)" }} />
        </div>
        <div>
          <h1 style={{ fontSize: 18, fontWeight: 700 }}>Clinical Decision Support</h1>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)" }}>Agentic Pipeline (9 Specialized Clinical Agents)</p>
        </div>
        {step !== "form" && (
          <button className="btn btn-ghost" style={{ marginLeft: "auto" }} onClick={() => { setStep("form"); setRunData(null); }}>
            New Case
          </button>
        )}
      </div>

      {step === "form" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "var(--spacing-bento-gap)" }}>
          {/* Left Column: Patient & Severity */}
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-bento-gap)" }}>
            <div className="card card-pad">
              <p className="label-xs" style={{ marginBottom: 12 }}>Select Patient</p>
              {loadingPts ? <PageSpinner /> : (
                <select className="select" style={{ width: "100%" }} value={selectedPatientId} onChange={(e) => setSelectedPatientId(e.target.value)}>
                  <option value="">— Choose Patient —</option>
                  {(patients as any[]).map((p) => (
                    <option key={p.id} value={p.id}>{p.full_name} (Age {p.age || 'N/A'})</option>
                  ))}
                </select>
              )}
            </div>
            
            <div className="card card-pad">
              <p className="label-xs" style={{ marginBottom: 12 }}>Clinical Severity</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                {["mild", "moderate", "severe"].map((s) => (
                  <button key={s} type="button" onClick={() => setSeverity(s)} className={`btn ${severity === s ? 'btn-primary' : 'btn-ghost'}`} style={{ justifyContent: "center", textTransform: "capitalize" }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="card card-pad" style={{ background: "var(--color-rose-light)", color: "var(--color-rose)", display: "flex", gap: 8, alignItems: "center" }}>
                <AlertCircle size={16} />
                <span style={{ fontSize: 12, fontWeight: 600 }}>{error}</span>
              </div>
            )}
          </div>

          {/* Right Column: Symptoms */}
          <div className="card card-pad">
            <p className="label-xs" style={{ marginBottom: 12 }}>Symptoms & Standardized Findings</p>
            <div style={{ marginBottom: 16 }}>
              <MedicalAutocomplete 
                type="condition" 
                placeholder="Search ICD-10 symptoms..."
                onSelect={(val) => { if (!symptoms.includes(val)) setSymptoms([...symptoms, val]); }} 
              />
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
              {SYMPTOM_OPTIONS.map((s) => (
                <button key={s} type="button" onClick={() => setSymptoms(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])}
                  style={{
                    padding: "6px 14px", borderRadius: "var(--radius-pill)", fontSize: 12, fontWeight: 500,
                    background: symptoms.includes(s) ? "var(--color-teal)" : "var(--color-canvas)",
                    color: symptoms.includes(s) ? "#fff" : "var(--color-text-secondary)",
                    border: "none", cursor: "pointer"
                  }}>
                  {s.replace(/_/g, " ")}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" style={{ width: "100%", height: 44, justifyContent: "center" }} onClick={handleSubmit} disabled={startMutation.isPending}>
              {startMutation.isPending ? <Spinner size={16} /> : <Activity size={16} />}
              Initialize 9-Agent Clinical Analysis
            </button>
          </div>
        </div>
      )}

      {step === "running" && (
        <div className="card card-pad animate-fade-in" style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 20px" }}>
          <div style={{ position: "relative", marginBottom: 24 }}>
            <div style={{ width: 64, height: 64, borderRadius: "50%", border: "4px solid var(--color-teal-light)", borderTopColor: "var(--color-teal)" }} className="animate-spin-slow" />
            <Activity size={24} style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", color: "var(--color-teal)" }} />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Orchestrating Agents...</h2>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 32, textAlign: "center", maxWidth: 400 }}>
            Our distributed agents are performing Bayesian inference, resistance modeling, and safety cross-referencing.
          </p>
          <div style={{ width: "100%", maxWidth: 360, background: "var(--color-canvas)", borderRadius: 16, padding: 16 }}>
             <PipelineProgress logs={runData?.step_logs || ["Initializing pipeline..."]} />
          </div>
        </div>
      )}

      {step === "done" && runData && (
        <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-bento-gap)" }}>
          <div className="card card-pad" style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: runData.pipeline_status === "complete" ? "var(--color-teal-light)" : "var(--color-rose-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              {runData.pipeline_status === "complete" ? <CheckCircle size={16} style={{ color: "var(--color-teal)" }} /> : <XCircle size={16} style={{ color: "var(--color-rose)" }} />}
            </div>
            <div>
              <p style={{ fontSize: 14, fontWeight: 700 }}>Analysis for {selectedPatient?.full_name}</p>
              <p style={{ fontSize: 11, color: "var(--color-text-muted)" }}>Completed at {new Date(runData.completed_at || '').toLocaleTimeString()}</p>
            </div>
          </div>
          {runData.pipeline_status === "complete" ? <ResultCard run={runData} /> : (
             <div className="card card-pad" style={{ background: "var(--color-rose-light)", color: "var(--color-rose)" }}>
               <p style={{ fontWeight: 600 }}>Pipeline Execution Failed</p>
               <p style={{ fontSize: 12 }}>Please check agent trace logs for clinical exceptions or connectivity issues.</p>
             </div>
          )}
        </div>
      )}
    </div>
  );
}

