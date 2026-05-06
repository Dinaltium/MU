"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { alertsApi, type Alert } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Badge, severityBadge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";
import { Bell, CheckCheck, Filter, Clock, AlertTriangle } from "lucide-react";

export default function AlertsPage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["alerts", unreadOnly],
    queryFn: () => alertsApi.list(unreadOnly, 50),
    enabled: !!user,
    refetchInterval: 15_000,
  });

  const markRead = useMutation({
    mutationFn: alertsApi.markRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const unreadCount = (alerts as Alert[]).filter((a) => !a.read).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Header */}
      <div className="card card-pad" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: "var(--color-rose-light)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Bell size={16} style={{ color: "var(--color-rose)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 17, fontWeight: 700 }}>Alerts</h1>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 1 }}>
              {unreadCount > 0 ? `${unreadCount} unread` : "All caught up"}
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => setUnreadOnly(!unreadOnly)} style={{ fontSize: 12 }}>
            <Filter size={12} /> {unreadOnly ? "Show all" : "Unread only"}
          </button>
        </div>
      </div>

      {/* Alerts list */}
      <div className="card card-pad">
        {isLoading ? <PageSpinner /> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {(alerts as Alert[]).map((alert) => (
              <div key={alert.id} className="animate-fade-in" style={{
                padding: "12px", borderRadius: "var(--radius-inner)",
                background: alert.read ? "var(--color-canvas)" : alert.severity === "HIGH" || alert.severity === "CRITICAL" ? "var(--color-rose-light)" : "var(--color-ember-light)",
                border: `1px solid ${alert.read ? "var(--color-border)" : alert.severity === "HIGH" || alert.severity === "CRITICAL" ? "rgba(244,63,94,0.2)" : "rgba(245,158,11,0.2)"}`,
                display: "flex", gap: 10,
              }}>
                <div style={{ paddingTop: 2, flexShrink: 0 }}>
                  <AlertTriangle size={14} style={{
                    color: alert.severity === "HIGH" || alert.severity === "CRITICAL" ? "var(--color-rose)"
                      : alert.severity === "MODERATE" ? "var(--color-ember)"
                        : "var(--color-teal)"
                  }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <Badge variant={severityBadge(alert.severity)}>{alert.severity}</Badge>
                    <span className="badge badge-slate">{alert.alert_type.replace(/_/g, " ")}</span>
                    {!alert.read && (
                      <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--color-rose)", display: "inline-block", marginLeft: 2 }} />
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: "var(--color-text-primary)", lineHeight: 1.5 }}>{alert.message}</p>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 6 }}>
                    <p style={{ fontSize: 10, color: "var(--color-text-muted)", display: "flex", alignItems: "center", gap: 3 }}>
                      <Clock size={9} /> {new Date(alert.created_at).toLocaleString()}
                    </p>
                    {!alert.read && (
                      <button
                        onClick={() => markRead.mutate(alert.id)}
                        disabled={markRead.isPending}
                        style={{ display: "flex", alignItems: "center", gap: 4, background: "none", border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600, color: "var(--color-teal)" }}
                      >
                        <CheckCheck size={11} /> Mark read
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {alerts.length === 0 && (
              <div style={{ textAlign: "center", padding: "32px 0" }}>
                <Bell size={28} style={{ color: "var(--color-border)", margin: "0 auto 10px" }} />
                <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>No alerts found</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
