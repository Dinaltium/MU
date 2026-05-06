"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Activity, Mail, Lock, Eye, EyeOff, AlertCircle } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError("");
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
    } finally { setLoading(false); }
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--color-canvas)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 16,
    }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: "var(--color-teal)",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto 12px",
          }}>
            <Activity size={22} color="#fff" />
          </div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: "var(--color-text-primary)" }}>Welcome back</h1>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 4 }}>
            Sign in to RxBridge
          </p>
        </div>

        {/* Card */}
        <div className="card card-pad animate-fade-in" style={{ padding: 24 }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Email */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>
                Email address
              </label>
              <div style={{ position: "relative" }}>
                <Mail size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 32 }}
                  type="email"
                  placeholder="dr.smith@hospital.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)", display: "block", marginBottom: 5 }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <Lock size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }} />
                <input
                  className="input"
                  style={{ paddingLeft: 32, paddingRight: 36 }}
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--color-text-muted)", display: "flex" }}
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "9px 12px",
                background: "var(--color-rose-light)",
                borderRadius: "var(--radius-inner)",
                border: "1px solid rgba(244,63,94,0.2)",
              }}>
                <AlertCircle size={13} style={{ color: "var(--color-rose)", flexShrink: 0 }} />
                <p style={{ fontSize: 12, color: "#9F1239" }}>{error}</p>
              </div>
            )}

            <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: 2 }}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", fontSize: 12, color: "var(--color-text-muted)", marginTop: 16 }}>
          Don&apos;t have an account?{" "}
          <Link href="/auth/register" style={{ color: "var(--color-teal)", fontWeight: 600, textDecoration: "none" }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
