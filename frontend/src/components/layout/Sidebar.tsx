"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, Stethoscope, Bell,
  Pill, ClipboardCheck, LogOut, Activity,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import clsx from "clsx";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: number;
}

interface SidebarProps {
  role: "doctor" | "patient";
  alertCount?: number;
}

const DOCTOR_NAV: NavItem[] = [
  { href: "/doctor/dashboard",     label: "Dashboard",     icon: LayoutDashboard },
  { href: "/doctor/patients",      label: "Patients",      icon: Users },
  { href: "/doctor/consultation",  label: "Consultation",  icon: Stethoscope },
  { href: "/doctor/alerts",        label: "Alerts",        icon: Bell },
];

const PATIENT_NAV: NavItem[] = [
  { href: "/patient/dashboard",    label: "Dashboard",     icon: LayoutDashboard },
  { href: "/patient/medications",  label: "Medications",   icon: Pill },
  { href: "/patient/checkin",      label: "Daily Check-in", icon: ClipboardCheck },
  { href: "/patient/alerts",       label: "My Alerts",     icon: Bell },
];

export default function Sidebar({ role, alertCount = 0 }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const nav = role === "doctor" ? DOCTOR_NAV : PATIENT_NAV;

  return (
    <aside className="sidebar-card">
      {/* ── Logo ── */}
      <div style={{ padding: "18px 16px 14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "var(--color-teal)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Activity size={16} color="white" />
          </div>
          <div>
            <p style={{ fontWeight: 700, fontSize: 14, color: "var(--color-text-primary)", lineHeight: 1.2 }}>RxBridge</p>
            <p style={{ fontSize: 10, color: "var(--color-text-secondary)", letterSpacing: "0.05em" }}>
              {role === "doctor" ? "Clinical AI" : "Patient Portal"}
            </p>
          </div>
        </div>
      </div>

      {/* ── User badge ── */}
      <div style={{ padding: "0 10px 12px" }}>
        <div style={{
          background: "var(--color-canvas)",
          border: "1px solid var(--color-border)",
          borderRadius: 8, padding: "9px 10px",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: "50%",
            background: "var(--color-teal)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 11, fontWeight: 700, color: "#fff", flexShrink: 0,
          }}>
            {user?.name?.[0]?.toUpperCase() || "?"}
          </div>
          <div style={{ minWidth: 0 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-primary)", lineHeight: 1.2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.name || "Loading…"}
            </p>
            <p style={{ fontSize: 10, color: "var(--color-text-secondary)", lineHeight: 1.4 }}>
              {role === "doctor" ? "Physician" : "Patient"}
            </p>
          </div>
        </div>
      </div>

      <div className="divider" style={{ margin: "0 10px 8px" }} />

      {/* ── Nav ── */}
      <nav style={{ padding: "0 10px", flex: 1 }}>
        <p className="label-xs" style={{ padding: "0 4px 6px" }}>
          Menu
        </p>
        {nav.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href} className={clsx("nav-item", active && "active")}>
              <Icon size={15} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.label === "Alerts" && alertCount > 0 && (
                <span style={{
                  background: "var(--color-rose)",
                  color: "#fff",
                  fontSize: 10, fontWeight: 700,
                  padding: "1px 6px", borderRadius: 100,
                  lineHeight: 1.6,
                }}>
                  {alertCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="divider" style={{ margin: "8px 10px" }} />

      {/* ── Logout ── */}
      <div style={{ padding: "0 10px 14px" }}>
        <button
          onClick={logout}
          className="nav-item"
          style={{ width: "100%", background: "none", border: "none", textAlign: "left" }}
        >
          <LogOut size={15} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
