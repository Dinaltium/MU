"use client";
// Patient alerts — same data as doctor alerts but filtered to their own records by the backend
import { useQuery } from "@tanstack/react-query";
import { alertsApi, type Alert } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Badge, severityBadge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";
import { Bell, AlertTriangle, Clock } from "lucide-react";

export default function PatientAlertsPage() {
  const { user } = useAuthStore();
  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["my-alerts-all"],
    queryFn: () => alertsApi.list(false, 50),
    enabled: !!user,
    refetchInterval: 30_000,
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--color-rose-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Bell size={16} style={{ color: "var(--color-rose)" }} />
        </div>
        <div>
          <h1 style={{ fontSize: 17, fontWeight: 700 }}>My Alerts</h1>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
            Notifications from your care team
          </p>
        </div>
      </div>

      <div className="card card-pad">
        {isLoading ? <PageSpinner /> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {(alerts as Alert[]).map((a) => (
              <div key={a.id} style={{
                padding: "12px", borderRadius: "var(--radius-inner)",
                background: a.read ? "var(--color-canvas)" : "var(--color-rose-light)",
                border: `1px solid ${a.read ? "var(--color-border)" : "rgba(244,63,94,0.2)"}`,
                display: "flex", gap: 10,
              }}>
                <AlertTriangle size={14} style={{ color: a.read ? "var(--color-text-muted)" : "var(--color-rose)", flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ display: "flex", gap: 5, marginBottom: 4 }}>
                    <Badge variant={severityBadge(a.severity)}>{a.severity}</Badge>
                    {!a.read && <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--color-rose)", display: "inline-block", alignSelf: "center" }} />}
                  </div>
                  <p style={{ fontSize: 13, color: "var(--color-text-primary)", lineHeight: 1.5 }}>{a.message}</p>
                  <p style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 4, display: "flex", alignItems: "center", gap: 3 }}>
                    <Clock size={9} /> {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
            {alerts.length === 0 && (
              <div style={{ textAlign: "center", padding: "32px 0" }}>
                <Bell size={28} style={{ color: "var(--color-border)", margin: "0 auto 10px" }} />
                <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>No alerts yet</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
