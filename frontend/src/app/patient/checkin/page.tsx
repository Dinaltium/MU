"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { monitoringApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { ClipboardCheck, CheckCircle, Frown, Meh, Smile, AlertCircle } from "lucide-react";

const FEEL_OPTIONS = [
  { value: "better", label: "Better", icon: Smile,  color: "var(--color-teal)", bg: "var(--color-teal-light)" },
  { value: "same",   label: "Same",   icon: Meh,    color: "var(--color-ember)", bg: "var(--color-ember-light)" },
  { value: "worse",  label: "Worse",  icon: Frown,  color: "var(--color-rose)", bg: "var(--color-rose-light)" },
] as const;

export default function CheckinPage() {
  const { user } = useAuthStore();
  const [consultationId, setConsultationId] = useState("");
  const [feel, setFeel] = useState<"better" | "same" | "worse" | "">("");
  const [severity, setSeverity] = useState(5);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const checkin = useMutation({
    mutationFn: monitoringApi.checkin,
    onSuccess: () => setDone(true),
    onError: (e: unknown) => {
      const msg = (e as {response?:{data?:{detail?:string}}})?.response?.data?.detail;
      setError(msg || "Check-in failed. Please try again.");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!consultationId.trim()) { setError("Enter your consultation ID."); return; }
    if (!feel) { setError("Select how you feel today."); return; }
    setError("");
    checkin.mutate({ consultation_id: consultationId, feel_status: feel, symptom_severity: severity });
  }

  if (done) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="card card-pad" style={{ textAlign: "center", padding: 40 }}>
          <CheckCircle size={40} style={{ color: "var(--color-teal)", margin: "0 auto 14px" }} />
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Check-in recorded</h2>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
            Your doctor has been notified. Keep it up!
          </p>
          <button className="btn btn-primary" style={{ margin: "20px auto 0", justifyContent: "center" }}
            onClick={() => { setDone(false); setFeel(""); setSeverity(5); setConsultationId(""); }}>
            Submit another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--color-teal-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <ClipboardCheck size={16} style={{ color: "var(--color-teal)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>Daily Check-in</h1>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
              Track your recovery progress
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {/* Consultation ID */}
        <div className="card card-pad">
          <label style={{ fontSize: 13, fontWeight: 700, display: "block", marginBottom: 8 }}>
            Consultation ID
          </label>
          <input className="input" placeholder="Paste your consultation ID from the doctor"
            value={consultationId} onChange={(e) => setConsultationId(e.target.value)} />
          <p style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 6 }}>
            Your doctor will share this when your treatment starts.
          </p>
        </div>

        {/* How do you feel */}
        <div className="card card-pad">
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>How are you feeling today?</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
            {FEEL_OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const active = feel === opt.value;
              return (
                <button key={opt.value} type="button" onClick={() => setFeel(opt.value)} style={{
                  padding: "14px 10px",
                  borderRadius: "var(--radius-card)",
                  border: `2px solid ${active ? opt.color : "var(--color-border)"}`,
                  background: active ? opt.bg : "var(--color-canvas)",
                  cursor: "pointer",
                  display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
                  transition: "all 0.15s ease",
                }}>
                  <Icon size={24} style={{ color: opt.color }} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: active ? opt.color : "var(--color-text-secondary)" }}>
                    {opt.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Severity slider */}
        <div className="card card-pad">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <p style={{ fontSize: 13, fontWeight: 700 }}>Symptom severity</p>
            <span className="num-display" style={{ fontSize: 20, color: severity >= 7 ? "var(--color-rose)" : severity >= 4 ? "var(--color-ember)" : "var(--color-teal)" }}>
              {severity}
            </span>
          </div>
          <input type="range" min={1} max={10} value={severity}
            onChange={(e) => setSeverity(+e.target.value)}
            style={{ width: "100%", accentColor: "var(--color-teal)", cursor: "pointer" }} />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ fontSize: 10, color: "var(--color-text-muted)" }}>Mild (1)</span>
            <span style={{ fontSize: 10, color: "var(--color-text-muted)" }}>Severe (10)</span>
          </div>
        </div>

        {error && (
          <div style={{ padding: "10px 12px", background: "var(--color-rose-light)", borderRadius: 8, border: "1px solid rgba(244,63,94,0.2)", display: "flex", gap: 7, alignItems: "center" }}>
            <AlertCircle size={13} style={{ color: "var(--color-rose)", flexShrink: 0 }} />
            <p style={{ fontSize: 12, color: "#9F1239" }}>{error}</p>
          </div>
        )}

        <div className="card card-pad">
          <button className="btn btn-primary" type="submit" disabled={checkin.isPending} style={{ width: "100%", justifyContent: "center" }}>
            <ClipboardCheck size={13} /> {checkin.isPending ? "Submitting…" : "Submit Check-in"}
          </button>
        </div>
      </form>
    </div>
  );
}
