"use client";
import { useAuthStore } from "@/lib/auth";
import { Pill, AlertTriangle, Info, ShieldCheck } from "lucide-react";

// Static medication education — the actual drug recommendation comes from consultation results.
// In a full implementation, you'd query the last consultation for this patient.

const DRUG_INFO: Record<string, { class: string; how: string; side_effects: string[]; tips: string }> = {
  amoxicillin: {
    class: "Penicillin antibiotic",
    how: "Take with or without food, every 8 hours as prescribed.",
    side_effects: ["Diarrhoea", "Nausea", "Skin rash", "Vomiting"],
    tips: "Complete the full course even if you feel better early.",
  },
  azithromycin: {
    class: "Macrolide antibiotic",
    how: "Take once daily, preferably at the same time each day.",
    side_effects: ["Stomach upset", "Diarrhoea", "Nausea", "Dizziness"],
    tips: "Avoid antacids within 2 hours of taking this medication.",
  },
  ciprofloxacin: {
    class: "Fluoroquinolone antibiotic",
    how: "Take every 12 hours with a full glass of water.",
    side_effects: ["Nausea", "Headache", "Dizziness", "Sun sensitivity"],
    tips: "Avoid dairy products and antacids within 2 hours.",
  },
  ceftriaxone: {
    class: "Third-generation cephalosporin",
    how: "Given by injection — administered by your healthcare team.",
    side_effects: ["Injection site pain", "Diarrhoea", "Rash", "Fever"],
    tips: "Tell your doctor if you have any penicillin allergy.",
  },
  chloroquine: {
    class: "Antimalarial",
    how: "Take after meals to reduce stomach upset.",
    side_effects: ["Nausea", "Headache", "Blurred vision", "Mood changes"],
    tips: "Regular eye check-ups are recommended for long-term use.",
  },
};

export default function MedicationsPage() {
  const { user } = useAuthStore();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--color-sky-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Pill size={16} style={{ color: "var(--color-sky)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>My Medications</h1>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
              Information about your prescribed treatments
            </p>
          </div>
        </div>
      </div>

      {/* Important notice */}
      <div className="card card-pad" style={{ background: "var(--color-ember-light)", border: "1px solid rgba(245,158,11,0.2)" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <AlertTriangle size={15} style={{ color: "var(--color-ember)", flexShrink: 0, marginTop: 1 }} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: "#92400E", marginBottom: 3 }}>Always follow your doctor&apos;s instructions</p>
            <p style={{ fontSize: 12, color: "#92400E", lineHeight: 1.5 }}>
              This information is for education only. Do not change your dose or stop medication without consulting your doctor.
            </p>
          </div>
        </div>
      </div>

      {/* Drug cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {Object.entries(DRUG_INFO).map(([name, info]) => (
          <div key={name} className="card card-pad animate-fade-in">
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: "var(--color-teal-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Pill size={16} style={{ color: "var(--color-teal)" }} />
              </div>
              <div>
                <p style={{ fontSize: 14, fontWeight: 700, textTransform: "capitalize" }}>{name}</p>
                <span className="badge badge-teal">{info.class}</span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div style={{ background: "var(--color-canvas)", borderRadius: 8, padding: 10 }}>
                <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
                  <Info size={12} style={{ color: "var(--color-sky)" }} />
                  <p className="label-xs" style={{ color: "var(--color-sky)" }}>How to take</p>
                </div>
                <p style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.5 }}>{info.how}</p>
              </div>

              <div style={{ background: "var(--color-canvas)", borderRadius: 8, padding: 10 }}>
                <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 4 }}>
                  <ShieldCheck size={12} style={{ color: "var(--color-teal)" }} />
                  <p className="label-xs" style={{ color: "var(--color-teal)" }}>Tip</p>
                </div>
                <p style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.5 }}>{info.tips}</p>
              </div>
            </div>

            <div style={{ marginTop: 8, background: "var(--color-canvas)", borderRadius: 8, padding: 10 }}>
              <p className="label-xs" style={{ marginBottom: 6 }}>Common side effects</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {info.side_effects.map((s) => (
                  <span key={s} className="badge badge-slate">{s}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
