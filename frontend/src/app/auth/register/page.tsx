"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Activity, Mail, Lock, User, AlertCircle } from "lucide-react";
import { authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", name: "", role: "doctor" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      await authApi.register(form);
      router.push("/auth/login?registered=1");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        // Pydantic validation error list
        setError(detail.map((d: any) => d.msg).join(", "));
      } else {
        setError("Registration failed. Please check your inputs.");
      }
    } finally { setLoading(false); }
  }

  return (
    <div style={{
      minHeight: "100vh", background: "var(--color-canvas)",
      display: "flex", alignItems: "center", justifyContent: "center", padding: 16,
    }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12, background: "var(--color-teal)",
            display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px",
          }}>
            <Activity size={22} color="#fff" />
          </div>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>Create account</h1>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 4 }}>Join RxBridge</p>
        </div>

        <div className="card card-pad animate-fade-in" style={{ padding: 24 }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>Full name</label>
              <div style={{ position: "relative" }}>
                <User size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input className="input" style={{ paddingLeft: 32 }} type="text" placeholder="Dr. Jane Smith"
                  value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>Email address</label>
              <div style={{ position: "relative" }}>
                <Mail size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input className="input" style={{ paddingLeft: 32 }} type="email" placeholder="doctor@hospital.com"
                  value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>Password</label>
              <div style={{ position: "relative" }}>
                <Lock size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input className="input" style={{ paddingLeft: 32 }} type="password" placeholder="Min 10 chars, 1 uppercase, 1 number"
                  value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>I am a</label>
              <select className="select" style={{ width: "100%" }}
                value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="doctor">Doctor / Clinician</option>
                <option value="patient">Patient</option>
              </select>
            </div>

            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: 8, padding: "9px 12px",
                background: "var(--color-rose-light)", borderRadius: "var(--radius-inner)",
                border: "1px solid rgba(244,63,94,0.2)",
              }}>
                <AlertCircle size={13} style={{ color: "var(--color-rose)", flexShrink: 0 }} />
                <p style={{ fontSize: 12, color: "#9F1239" }}>{error}</p>
              </div>
            )}

            <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: 2 }}>
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", fontSize: 12, color: "var(--color-text-muted)", marginTop: 16 }}>
          Already have an account?{" "}
          <Link href="/auth/login" style={{ color: "var(--color-teal)", fontWeight: 600, textDecoration: "none" }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
