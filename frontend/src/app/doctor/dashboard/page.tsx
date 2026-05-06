"use client";
import { useQuery } from "@tanstack/react-query";
import { patientsApi, alertsApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Badge, severityBadge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";
import {
  Users, Bell, Activity, TrendingUp, AlertTriangle,
  Stethoscope, ChevronRight, Clock,
} from "lucide-react";
import Link from "next/link";

function StatCard({
  label, value, icon: Icon, accent, sub,
}: { label: string; value: string | number; icon: React.ElementType; accent: string; sub?: string }) {
  return (
    <div className="card card-pad" style={{ position: "relative", overflow: "hidden" }}>
      <div className="stat-card-accent" style={{ background: accent }} />
      <div style={{ position: "relative" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
          <p className="label-xs">{label}</p>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: accent + "22", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Icon size={14} style={{ color: accent }} />
          </div>
        </div>
        <p className="num-display" style={{ fontSize: 28, color: "var(--color-text-primary)" }}>{value}</p>
        {sub && <p style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 4 }}>{sub}</p>}
      </div>
    </div>
  );
}

export default function DoctorDashboard() {
  const { user } = useAuthStore();

  const { data: patients = [], isLoading: loadingPts } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(50),
    enabled: !!user,
  });

  const { data: alerts = [], isLoading: loadingAlerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => alertsApi.list(false, 8),
    enabled: !!user,
    refetchInterval: 30_000,
  });

  const unread = (alerts as {read:boolean}[]).filter((a) => !a.read).length;
  const ptCount = Array.isArray(patients) ? patients.length : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>

      {/* ── Top bar ── */}
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: 18, fontWeight: 700, color: "var(--color-text-primary)" }}>Dashboard</h1>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
            Good morning, {user?.name?.split(" ")[0]}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Link href="/doctor/consultation" className="btn btn-primary" style={{ fontSize: 12 }}>
            <Stethoscope size={13} /> New Consultation
          </Link>
          <Link href="/doctor/patients" className="btn btn-ghost" style={{ fontSize: 12 }}>
            <Users size={13} /> Patients
          </Link>
        </div>
      </div>

      {/* ── Stat row ── */}
      <div className="bento-row" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <StatCard label="Total Patients" value={loadingPts ? "—" : ptCount}
          icon={Users} accent="var(--color-teal)" sub="Under your care" />
        <StatCard label="Unread Alerts" value={unread}
          icon={Bell} accent="var(--color-rose)" sub={unread > 0 ? "Needs attention" : "All clear"} />
        <StatCard label="Pipeline Status" value="Active"
          icon={Activity} accent="var(--color-sky)" sub="AI models running" />
        <StatCard label="Consultations" value="24h"
          icon={TrendingUp} accent="var(--color-violet)" sub="Real-time analysis" />
      </div>

      {/* ── Middle row: Recent patients + Alerts ── */}
      <div className="bento-row" style={{ gridTemplateColumns: "1.2fr 1fr" }}>

        {/* Recent patients */}
        <div className="card card-pad" style={{ overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <p style={{ fontSize: 13, fontWeight: 700 }}>Recent Patients</p>
            <Link href="/doctor/patients" style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-teal)", textDecoration: "none", fontWeight: 600 }}>
              View all <ChevronRight size={11} />
            </Link>
          </div>
          {loadingPts ? <PageSpinner /> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {(patients as {id:string;name:string;age:number;location?:string}[]).slice(0, 6).map((pt) => (
                <Link key={pt.id} href={`/doctor/patients`} style={{ textDecoration: "none" }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "8px 10px", borderRadius: "var(--radius-inner)",
                    cursor: "pointer", transition: "background 0.15s",
                  }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-canvas)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <div style={{
                      width: 30, height: 30, borderRadius: "50%",
                      background: "var(--color-teal-light)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 12, fontWeight: 700, color: "var(--color-teal-dark)", flexShrink: 0,
                    }}>
                      {pt.name[0]}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-primary)" }}>{pt.name}</p>
                      <p style={{ fontSize: 11, color: "var(--color-text-muted)" }}>Age {pt.age} · {pt.location || "Unknown"}</p>
                    </div>
                    <ChevronRight size={12} style={{ color: "var(--color-text-muted)" }} />
                  </div>
                </Link>
              ))}
              {patients.length === 0 && (
                <p style={{ fontSize: 12, color: "var(--color-text-muted)", padding: "20px 0", textAlign: "center" }}>
                  No patients yet. Add your first patient.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Alerts panel */}
        <div className="card card-pad" style={{ overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <p style={{ fontSize: 13, fontWeight: 700 }}>Recent Alerts</p>
              {unread > 0 && (
                <span style={{ background: "var(--color-rose)", color: "#fff", fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 100 }}>{unread}</span>
              )}
            </div>
            <Link href="/doctor/alerts" style={{ fontSize: 11, color: "var(--color-teal)", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 3 }}>
              View all <ChevronRight size={11} />
            </Link>
          </div>

          {loadingAlerts ? <PageSpinner /> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {(alerts as {id:string;severity:string;message:string;read:boolean;created_at:string}[]).map((a) => (
                <div key={a.id} style={{
                  padding: "9px 10px", borderRadius: "var(--radius-inner)",
                  background: a.read ? "rgba(255,255,255,0.5)" : "var(--color-rose-light)",
                  display: "flex", gap: 8, alignItems: "flex-start",
                }}>
                  <AlertTriangle size={12} style={{ color: a.read ? "var(--color-text-muted)" : "var(--color-rose)", marginTop: 1, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <Badge variant={severityBadge(a.severity)}>{a.severity}</Badge>
                    </div>
                    <p style={{ fontSize: 11, color: "var(--color-text-primary)", lineHeight: 1.4 }}>{a.message}</p>
                    <p style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 2, display: "flex", alignItems: "center", gap: 3 }}>
                      <Clock size={9} /> {new Date(a.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
              {alerts.length === 0 && (
                <p style={{ fontSize: 12, color: "var(--color-text-muted)", textAlign: "center", padding: "20px 0" }}>
                  No alerts. All patients stable.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Quick actions ── */}
      <div className="card card-pad">
        <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Quick Actions</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {[
            { label: "New Consultation", desc: "Start AI-guided diagnosis", href: "/doctor/consultation", icon: Stethoscope, color: "var(--color-teal)" },
            { label: "Add Patient",       desc: "Register a new patient",    href: "/doctor/patients",     icon: Users,        color: "var(--color-sky)" },
            { label: "View Alerts",       desc: `${unread} unread alerts`,   href: "/doctor/alerts",       icon: Bell,         color: "var(--color-ember)" },
          ].map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} href={action.href} style={{ textDecoration: "none" }}>
                <div className="card" style={{
                  padding: "12px", cursor: "pointer",
                  border: "1px solid var(--color-border)",
                  display: "flex", gap: 10, alignItems: "center",
                }}>
                  <div style={{ width: 34, height: 34, borderRadius: 8, background: action.color + "15", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <Icon size={16} style={{ color: action.color }} />
                  </div>
                  <div>
                    <p style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-primary)" }}>{action.label}</p>
                    <p style={{ fontSize: 11, color: "var(--color-text-muted)" }}>{action.desc}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
