"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { patientsApi, PatientCreatePayload } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { PageSpinner } from "@/components/ui/Spinner";
import { Plus, X, User, MapPin, Pill, AlertCircle, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { MedicalAutocomplete } from "@/components/ui/MedicalAutocomplete";

const SYMPTOM_OPTIONS = [
  "headache", "fever", "cough", "nausea", "vomiting", "diarrhoea",
  "chest_pain", "shortness_of_breath", "fatigue", "rash", "sore_throat",
  "neck_stiffness", "confusion", "abdominal_pain", "dysuria",
];

const REGIONS = ["south_india", "north_india", "default"];

function AddPatientForm({ onSuccess }: { onSuccess: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<PatientCreatePayload>({
    name: "", age: 0, gender: "male", location: "south_india",
    weight_kg: 70, renal_function: 1.0,
    conditions: [], allergies: [], medications: [],
  });
  const [newAllergy, setNewAllergy] = useState("");
  const [newMed, setNewMed] = useState("");
  const [error, setError] = useState("");

  const { mutate, isPending } = useMutation({
    mutationFn: (data: PatientCreatePayload) => patientsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["patients"] }); onSuccess(); },
    onError: (e: unknown) => {
      const msg = (e as {response?:{data?:{detail?:string}}})?.response?.data?.detail;
      setError(msg || "Failed to create patient.");
    },
  });

  function addTag(field: "allergies" | "medications", value: string) {
    if (!value.trim()) return;
    setForm((f) => ({ ...f, [field]: [...(f[field] || []), value.trim()] }));
    if (field === "allergies") setNewAllergy(""); else setNewMed("");
  }

  function removeTag(field: "allergies" | "medications", idx: number) {
    setForm((f) => ({ ...f, [field]: (f[field] || []).filter((_, i) => i !== idx) }));
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutate(form); }}
      style={{ display: "flex", flexDirection: "column", gap: 12 }}>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Full Name *</label>
          <input className="input" placeholder="Patient name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Age *</label>
          <input className="input" type="number" min={1} max={149} placeholder="Age"
            value={form.age || ""} onChange={(e) => setForm({ ...form, age: +e.target.value })} required />
        </div>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Gender</label>
          <select className="select" style={{ width: "100%" }} value={form.gender || ""}
            onChange={(e) => setForm({ ...form, gender: e.target.value })}>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Region</label>
          <select className="select" style={{ width: "100%" }} value={form.location || ""}
            onChange={(e) => setForm({ ...form, location: e.target.value })}>
            {REGIONS.map((r) => <option key={r} value={r}>{r.replace("_", " ")}</option>)}
          </select>
        </div>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Weight (kg)</label>
          <input className="input" type="number" step="0.1" value={form.weight_kg || ""}
            onChange={(e) => setForm({ ...form, weight_kg: +e.target.value })} />
        </div>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Renal function (0–1)</label>
          <input className="input" type="number" step="0.01" min={0} max={1} value={form.renal_function ?? ""}
            onChange={(e) => setForm({ ...form, renal_function: +e.target.value })} />
        </div>
      </div>

      {/* Allergies */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Allergies</label>
        <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
          <MedicalAutocomplete 
            type="condition" 
            placeholder="Search for allergy/condition (ICD-10)..."
            onSelect={(val) => addTag("allergies", val)} 
          />
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {(form.allergies || []).map((a, i) => (
            <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "2px 8px", borderRadius: 100, background: "var(--color-rose-light)", fontSize: 11, fontWeight: 600, color: "#9F1239" }}>
              {a} <button type="button" onClick={() => removeTag("allergies", i)} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", color: "#9F1239" }}><X size={9} /></button>
            </span>
          ))}
        </div>
      </div>

      {/* Medications */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 4 }}>Current Medications</label>
        <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
          <MedicalAutocomplete 
            type="medication" 
            placeholder="Search for medication (RxNorm)..."
            onSelect={(val) => addTag("medications", val)} 
          />
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {(form.medications || []).map((m, i) => (
            <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "2px 8px", borderRadius: 100, background: "var(--color-sky-light)", fontSize: 11, fontWeight: 600, color: "#0369A1" }}>
              {m} <button type="button" onClick={() => removeTag("medications", i)} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", color: "#0369A1" }}><X size={9} /></button>
            </span>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ display: "flex", gap: 6, alignItems: "center", padding: "8px 10px", background: "var(--color-rose-light)", borderRadius: 8, border: "1px solid rgba(244,63,94,0.2)" }}>
          <AlertCircle size={12} style={{ color: "var(--color-rose)" }} />
          <p style={{ fontSize: 11, color: "#9F1239" }}>{error}</p>
        </div>
      )}

      <button className="btn btn-primary" type="submit" disabled={isPending} style={{ alignSelf: "flex-end" }}>
        <Plus size={13} /> {isPending ? "Adding…" : "Add Patient"}
      </button>
    </form>
  );
}

function PatientRow({ patient }: { patient: {id:string;name:string;age:number;gender?:string;location?:string;conditions?:string[];allergies?:string[];medications?:string[]} }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ borderRadius: "var(--radius-inner)", background: "var(--color-canvas)", overflow: "hidden" }}>
      <div
        style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", cursor: "pointer" }}
        onClick={() => setOpen(!open)}
      >
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--color-teal-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "var(--color-teal-dark)", flexShrink: 0 }}>
          {patient.name[0]}
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: 13, fontWeight: 600 }}>{patient.name}</p>
          <p style={{ fontSize: 11, color: "var(--color-text-muted)" }}>Age {patient.age} · {patient.gender} · {patient.location?.replace("_", " ")}</p>
        </div>
        {(patient.allergies?.length || 0) > 0 && (
          <span className="badge badge-rose">{patient.allergies?.length} allerg.</span>
        )}
        {open ? <ChevronUp size={14} style={{ color: "var(--color-text-muted)" }} /> : <ChevronDown size={14} style={{ color: "var(--color-text-muted)" }} />}
      </div>
      {open && (
        <div style={{ padding: "0 12px 12px", background: "var(--color-canvas)", borderTop: "1px solid var(--color-border)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, paddingTop: 10 }}>
            <div>
              <p className="label-xs" style={{ marginBottom: 4 }}>Conditions</p>
              <p style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                {Array.isArray(patient.conditions) ? patient.conditions.join(", ") : "None recorded"}
              </p>
            </div>
            <div>
              <p className="label-xs" style={{ marginBottom: 4 }}>Allergies</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                {Array.isArray(patient.allergies) && patient.allergies.length > 0
                  ? patient.allergies.map((a) => <span key={a} className="badge badge-rose">{a}</span>)
                  : <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>None</span>
                }
              </div>
            </div>
            <div>
              <p className="label-xs" style={{ marginBottom: 4 }}>Current Medications</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                {Array.isArray(patient.medications) && patient.medications.length > 0
                  ? patient.medications.map((m) => <span key={m} className="badge badge-sky">{m}</span>)
                  : <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>None</span>
                }
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PatientsPage() {
  const { user } = useAuthStore();
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");

  const { data: patients = [], isLoading } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(50),
    enabled: !!user,
  });

  const filtered = (patients as {id:string;name:string;age:number;gender?:string;location?:string;conditions?:string[];allergies?:string[];medications?:string[]}[]).filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: 17, fontWeight: 700 }}>Patients</h1>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
            {filtered.length} patient{filtered.length !== 1 ? "s" : ""} registered
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)} style={{ fontSize: 12 }}>
          <Plus size={13} /> Add Patient
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="card card-pad animate-fade-in" style={{ position: "relative", zIndex: 50 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <p style={{ fontSize: 13, fontWeight: 700 }}>New Patient</p>
            <button onClick={() => setShowForm(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-text-muted)" }}><X size={16} /></button>
          </div>
          <AddPatientForm onSuccess={() => setShowForm(false)} />
        </div>
      )}

      {/* Search + list */}
      <div className="card card-pad">
        <div style={{ position: "relative", marginBottom: 10 }}>
          <User size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
          <input className="input" style={{ paddingLeft: 30 }} placeholder="Search patients…"
            value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {isLoading ? <PageSpinner /> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {filtered.map((pt) => <PatientRow key={pt.id} patient={pt} />)}
            {filtered.length === 0 && (
              <p style={{ textAlign: "center", fontSize: 12, color: "var(--color-text-muted)", padding: "24px 0" }}>
                {search ? "No patients match your search." : "No patients yet. Add one above."}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
