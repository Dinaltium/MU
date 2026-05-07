"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  Activity, Mail, Lock, Eye, EyeOff, AlertCircle, 
  ShieldCheck, Zap, HeartPulse, Microscope, ChevronRight,
  CheckCircle2
} from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setToken, setUser } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (searchParams.get("registered")) {
      setSuccess("Account created successfully! Please sign in.");
    }
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); 
    setError("");
    setSuccess("");
    try {
      const data = await authApi.login(form);
      setToken(data.access_token);
      const user = await authApi.me();
      setUser(user);
      router.push(user.role === "doctor" ? "/doctor/dashboard" : "/patient/dashboard");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(", "));
      } else {
        setError("Login failed. Check your credentials.");
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
        
        {/* Tile 1: Brand & Logo (3 cols) */}
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
          <p style={{ fontSize: 14, opacity: 0.8, marginTop: 4 }}>Next-gen Clinical Support</p>
        </div>

        {/* Tile 2: Security Info (4 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 4",
          display: "flex",
          alignItems: "center",
          gap: 16,
          animationDelay: "0.1s"
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "var(--color-teal-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0
          }}>
            <ShieldCheck size={20} color="var(--color-teal)" />
          </div>
          <div>
            <div className="label-xs" style={{ marginBottom: 2 }}>Security</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>AES-256 Encrypted</div>
          </div>
        </div>

        {/* Tile 3: System Health (4 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 4",
          display: "flex",
          alignItems: "center",
          gap: 16,
          animationDelay: "0.2s"
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "var(--color-sky-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0
          }}>
            <Zap size={20} color="var(--color-sky)" />
          </div>
          <div>
            <div className="label-xs" style={{ marginBottom: 2 }}>Engine</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>AI Models Active</div>
          </div>
        </div>

        {/* Tile 4: Main Login Form (6 cols, 3 rows high) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 6", 
          gridRow: "span 3",
          padding: 32,
          animationDelay: "0.3s",
          display: "flex",
          flexDirection: "column"
        }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Sign In</h2>
          <p style={{ fontSize: 14, color: "var(--color-text-muted)", marginBottom: 28 }}>
            Access your clinical dashboard and patient records.
          </p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20, flex: 1 }}>
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
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)" }}>
                  Password
                </label>
                <Link href="#" style={{ fontSize: 11, color: "var(--color-teal)", fontWeight: 600, textDecoration: "none" }}>
                  Forgot?
                </Link>
              </div>
              <div style={{ position: "relative" }}>
                <Lock size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 40, paddingRight: 44, height: 44 }}
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--color-text-muted)", display: "flex" }}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Notifications */}
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

            {success && (
              <div style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "12px",
                background: "var(--color-teal-light)",
                borderRadius: "12px",
              }}>
                <CheckCircle2 size={16} style={{ color: "var(--color-teal)", flexShrink: 0 }} />
                <p style={{ fontSize: 13, color: "var(--color-teal-dark)", fontWeight: 500 }}>{success}</p>
              </div>
            )}

            <button 
              className="btn btn-primary" 
              type="submit" 
              disabled={loading} 
              style={{ width: "100%", height: 48, justifyContent: "center", marginTop: "auto", fontSize: 15 }}
            >
              {loading ? "Authenticating..." : "Sign in to Dashboard"}
              {!loading && <ChevronRight size={18} />}
            </button>
          </form>
        </div>

        {/* Tile 5: Registration CTA (6 cols) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 6",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          animationDelay: "0.4s"
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-primary)" }}>New to RxBridge?</div>
            <div style={{ fontSize: 12, color: "var(--color-text-muted)" }}>Create a clinician or patient account.</div>
          </div>
          <Link href="/auth/register" className="btn btn-ghost" style={{ borderRadius: 12 }}>
            Register Now
          </Link>
        </div>

        {/* Tile 6: Decorative / Insights (3 cols, 2 rows high) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 3",
          gridRow: "span 2",
          background: "var(--color-surface)",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          animationDelay: "0.5s"
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "var(--color-violet-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <HeartPulse size={18} color="var(--color-violet)" />
          </div>
          <div className="label-xs">Live Patient Flow</div>
          <div style={{ marginTop: "auto" }}>
            <div style={{ fontSize: 24, fontWeight: 700 }} className="num-display">1,284</div>
            <div style={{ fontSize: 11, color: "var(--color-teal)", fontWeight: 600 }}>↑ 12% this week</div>
          </div>
        </div>

        {/* Tile 7: Decorative / Research (3 cols, 2 rows high) */}
        <div className="card card-pad animate-fade-in" style={{ 
          gridColumn: "span 3",
          gridRow: "span 2",
          background: "var(--color-surface)",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          animationDelay: "0.6s"
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "var(--color-ember-light)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Microscope size={18} color="var(--color-ember)" />
          </div>
          <div className="label-xs">Clinical Trials</div>
          <div style={{ marginTop: "auto" }}>
            <div style={{ fontSize: 24, fontWeight: 700 }} className="num-display">42</div>
            <div style={{ fontSize: 11, color: "var(--color-text-muted)" }}>Active datasets</div>
          </div>
        </div>

      </div>
    </div>
  );
}
