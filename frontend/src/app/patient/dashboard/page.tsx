"use client";
import { useQuery } from "@tanstack/react-query";
import { alertsApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Badge, severityBadge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";
import { Bell, Activity, ClipboardCheck, Pill, Clock, Heart, TrendingUp, AlertTriangle, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function PatientDashboard() {
  const { user } = useAuthStore();

  const { data: alerts = [], isLoading: loadingAlerts } = useQuery({
    queryKey: ["my-alerts"],
    queryFn: () => alertsApi.list(false, 5),
    enabled: !!user,
    refetchInterval: 30_000,
  });

  const unread = (alerts as {read:boolean}[]).filter((a) => !a.read).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ fontSize: 18, fontWeight: 700 }}>My Health</h1>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
            Hello, {user?.name?.split(" ")[0]} — stay on track today
          </p>
        </div>
        <Link href="/patient/checkin" className="btn btn-primary" style={{ fontSize: 12 }}>
          <Heart size={13} /> Daily Check-in
        </Link>
      </div>

      {/* Stats */}
      <div className="bento-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
        {[
          { label: "Alerts", value: unread, icon: Bell, color: "var(--color-rose)", sub: unread > 0 ? "Need attention" : "All clear" },
          { label: "Treatment", value: "Active", icon: Activity, color: "var(--color-teal)", sub: "Monitoring enabled" },
          { label: "Check-ins", value: "Daily", icon: ClipboardCheck, color: "var(--color-sky)", sub: "Keep it consistent" },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="card card-pad" style={{ position: "relative", overflow: "hidden" }}>
              <div className="stat-card-accent" style={{ background: s.color }} />
              <div style={{ position: "relative" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <p className="label-xs">{s.label}</p>
                  <div style={{ width: 26, height: 26, borderRadius: 7, background: s.color + "20", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={13} style={{ color: s.color }} />
                  </div>
                </div>
                <p className="num-display" style={{ fontSize: 24, color: "var(--color-text-primary)" }}>{s.value}</p>
                <p style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 2 }}>{s.sub}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick actions + alerts */}
      <div className="bento-row" style={{ gridTemplateColumns: "1fr 1.2fr" }}>
        {/* Quick links */}
        <div className="card card-pad">
          <p style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Quick Access</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {[
              { href: "/patient/checkin",      label: "Submit Check-in",  icon: ClipboardCheck, color: "var(--color-teal)" },
              { href: "/patient/medications",  label: "My Medications",   icon: Pill,            color: "var(--color-sky)" },
              { href: "/patient/alerts",       label: `Alerts (${unread})`, icon: Bell,          color: "var(--color-rose)" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} style={{ textDecoration: "none" }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "10px 12px", borderRadius: "var(--radius-inner)",
                    border: "1px solid var(--color-border)",
                    cursor: "pointer", background: "var(--color-canvas)",
                    transition: "border-color 0.15s",
                  }}>
                    <div style={{ width: 30, height: 30, borderRadius: 7, background: item.color + "18", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon size={14} style={{ color: item.color }} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)", flex: 1 }}>{item.label}</span>
                    <ChevronRight size={13} style={{ color: "var(--color-text-muted)" }} />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent alerts */}
        <div className="card card-pad">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <p style={{ fontSize: 13, fontWeight: 700 }}>Recent Alerts</p>
            <Link href="/patient/alerts" style={{ fontSize: 11, color: "var(--color-teal)", fontWeight: 600, textDecoration: "none", display: "flex", alignItems: "center", gap: 3 }}>
              View all <ChevronRight size={11} />
            </Link>
          </div>
          {loadingAlerts ? <PageSpinner /> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {(alerts as {id:string;severity:string;message:string;read:boolean;created_at:string;alert_type:string}[]).map((a) => (
                <div key={a.id} style={{
                  padding: "9px 10px", borderRadius: "var(--radius-inner)",
                  border: `1px solid ${a.read ? "var(--color-border)" : "rgba(244,63,94,0.2)"}`,
                  background: a.read ? "transparent" : "var(--color-rose-light)",
                  display: "flex", gap: 8, alignItems: "flex-start",
                }}>
                  <AlertTriangle size={12} style={{ color: a.read ? "var(--color-text-muted)" : "var(--color-rose)", flexShrink: 0, marginTop: 1 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", gap: 4, marginBottom: 2 }}>
                      <Badge variant={severityBadge(a.severity)}>{a.severity}</Badge>
                    </div>
                    <p style={{ fontSize: 11, color: "var(--color-text-primary)", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {a.message}
                    </p>
                    <p style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 2, display: "flex", alignItems: "center", gap: 3 }}>
                      <Clock size={9} /> {new Date(a.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
              {alerts.length === 0 && (
                <p style={{ textAlign: "center", fontSize: 12, color: "var(--color-text-muted)", padding: "20px 0" }}>
                  No alerts. You&apos;re doing great!
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Health tip */}
      <div className="card card-pad" style={{ background: "var(--color-sidebar-bg)", border: "none" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <TrendingUp size={18} style={{ color: "var(--color-teal)", flexShrink: 0 }} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>Complete your daily check-in</p>
            <p style={{ fontSize: 12, color: "var(--color-sidebar-text)", marginTop: 2 }}>
              Your check-ins help your doctor monitor your recovery and adjust treatment if needed.
            </p>
          </div>
          <Link href="/patient/checkin" className="btn btn-primary" style={{ fontSize: 11, flexShrink: 0, marginLeft: "auto" }}>
            Check in now
          </Link>
        </div>
      </div>
    </div>
  );
}
