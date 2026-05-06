"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { useAuthStore } from "@/lib/auth";
import { PageSpinner } from "@/components/ui/Spinner";

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, init } = useAuthStore();
  const router = useRouter();

  useEffect(() => { init(); }, [init]);

  useEffect(() => {
    if (!loading && !user) router.push("/auth/login");
    if (!loading && user && user.role === "doctor") router.push("/doctor/dashboard");
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-canvas)" }}>
        <PageSpinner />
      </div>
    );
  }

  return (
    <div className="bento-layout">
      <Sidebar role="patient" />
      <main className="bento-main">{children}</main>
    </div>
  );
}
