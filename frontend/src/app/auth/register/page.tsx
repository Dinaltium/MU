"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Activity, Mail, Lock, User, AlertCircle, 
  ShieldCheck, Zap, ChevronRight, CheckCircle2 
} from "lucide-react";
import { authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "doctor" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); 
    setError("");
    try {
      await authApi.register(form);
      router.push("/auth/login?registered=1");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(", "));
      } else {
        setError("Registration failed. Please check your inputs.");
      }
    } finally { 
      setLoading(false); 
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--color-canvas)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 24,
    }}>
      <div style={{
        width: "100%",
        maxWidth: 1000,
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)",
        gridAutoRows: "minmax(100px, auto)",
        gap: 16,
      }}>
        
        {/* Tile 1: Brand (4 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 4", 
          display: "flex", 
          flexDirection: "column", 
          justifyContent: "center",
          alignItems: "flex-start",
          background: "var(--color-teal)",
          color: "white"
        }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14,
            background: "rgba(255,255,255,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            marginBottom: 16,
          }}>
            <Activity size={26} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.02em" }}>RxBridge</h1>
          <p style={{ fontSize: 14, opacity: 0.8, marginTop: 4 }}>Join the network</p>
        </div>

        {/* Tile 2: Privacy (4 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 4",
          display: "flex",
          alignItems: "center",
          gap: 16,
          animationDelay: "0.1s"
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "var(--color-sky-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0
          }}>
            <ShieldCheck size={20} color="var(--color-sky)" />
          </div>
          <div>
            <div className="label-xs" style={{ marginBottom: 2 }}>Data Privacy</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>HIPAA Compliant</div>
          </div>
        </div>

        {/* Tile 3: AI Ready (4 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 4",
          display: "flex",
          alignItems: "center",
          gap: 16,
          animationDelay: "0.2s"
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "var(--color-violet-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0
          }}>
            <Zap size={20} color="var(--color-violet)" />
          </div>
          <div>
            <div className="label-xs" style={{ marginBottom: 2 }}>Intelligence</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>AI-First Workflow</div>
          </div>
        </div>

        {/* Tile 4: Registration Form (7 cols, 4 rows high) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 7", 
          gridRow: "span 4",
          padding: 32,
          animationDelay: "0.3s",
          display: "flex",
          flexDirection: "column"
        }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Create Account</h2>
          <p style={{ fontSize: 14, color: "var(--color-text-muted)", marginBottom: 28 }}>
            Start your journey with precision medical support.
          </p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18, flex: 1 }}>
            {/* Full Name */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 8 }}>
                Full Name
              </label>
              <div style={{ position: "relative" }}>
                <User size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 40, height: 44 }}
                  type="text"
                  placeholder="Dr. Jane Smith"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 8 }}>
                Email Address
              </label>
              <div style={{ position: "relative" }}>
                <Mail size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 40, height: 44 }}
                  type="email"
                  placeholder="name@hospital.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 8 }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 40, height: 44 }}
                  type="password"
                  placeholder="Minimum 8 characters"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </div>

            {/* Role Selection */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 8 }}>
                I am a
              </label>
              <select 
                className="select" 
                style={{ width: "100%", height: 44 }}
                value={form.role} 
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="doctor">Doctor / Clinician</option>
                <option value="patient">Patient</option>
                <option value="lab">Lab Technician</option>
              </select>
            </div>

            {/* Error Message */}
            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "12px",
                background: "var(--color-rose-light)",
                borderRadius: "12px",
              }}>
                <AlertCircle size={16} style={{ color: "var(--color-rose)", flexShrink: 0 }} />
                <p style={{ fontSize: 13, color: "#9F1239", fontWeight: 500 }}>{error}</p>
              </div>
            )}

            <button 
              className="btn btn-primary" 
              type="submit" 
              disabled={loading} 
              style={{ width: "100%", height: 48, justifyContent: "center", marginTop: "auto", fontSize: 15 }}
            >
              {loading ? "Creating account..." : "Join RxBridge"}
              {!loading && <ChevronRight size={18} />}
            </button>
          </form>
        </div>

        {/* Tile 5: Back to Login (5 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 5",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          animationDelay: "0.4s"
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-primary)" }}>Already a member?</div>
            <div style={{ fontSize: 12, color: "var(--color-text-muted)" }}>Sign in to your account.</div>
          </div>
          <Link href="/auth/login" className="btn btn-ghost" style={{ borderRadius: 12 }}>
            Login
          </Link>
        </div>

        {/* Tile 6: Help/Support (5 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 5",
          display: "flex",
          alignItems: "center",
          gap: 16,
          animationDelay: "0.5s"
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "var(--color-ember-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0
          }}>
            <Activity size={20} color="var(--color-ember)" />
          </div>
          <div>
            <div className="label-xs" style={{ marginBottom: 2 }}>Need Help?</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>View setup guide</div>
          </div>
        </div>

      </div>
    </div>
  );
}
