"use client";
// Doctor layout — wraps all /doctor/* pages in the bento shell
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { useAuthStore } from "@/lib/auth";
import { useQuery } from "@tanstack/react-query";
import { alertsApi } from "@/lib/api";
import { PageSpinner } from "@/components/ui/Spinner";

export default function DoctorLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, init } = useAuthStore();
  const router = useRouter();

  useEffect(() => { init(); }, [init]);

  useEffect(() => {
    if (!loading && !user) router.push("/auth/login");
    if (!loading && user && user.role !== "doctor") router.push("/patient/dashboard");
  }, [user, loading, router]);

  const { data: alerts } = useQuery({
    queryKey: ["alerts-unread"],
    queryFn: () => alertsApi.list(true, 50),
    enabled: !!user,
    refetchInterval: 30_000,
  });

  const unreadCount = Array.isArray(alerts) ? alerts.length : 0;

  if (loading || !user) {
    return (
      <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-canvas)" }}>
        <PageSpinner />
      </div>
    );
  }

  return (
    <div className="bento-layout">
      <Sidebar role="doctor" alertCount={unreadCount} />
      <main className="bento-main">{children}</main>
    </div>
  );
}
