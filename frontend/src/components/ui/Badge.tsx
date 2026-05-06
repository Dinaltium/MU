// components/ui/Badge.tsx
import clsx from "clsx";

type Variant = "teal" | "ember" | "rose" | "sky" | "slate" | "violet";

export function Badge({ children, variant = "slate" }: { children: React.ReactNode; variant?: Variant }) {
  return <span className={clsx("badge", `badge-${variant}`)}>{children}</span>;
}

// Severity → variant
export function severityBadge(s?: string) {
  if (!s) return "slate";
  const map: Record<string, Variant> = {
    LOW: "teal", MODERATE: "ember", HIGH: "rose", CRITICAL: "rose",
  };
  return map[s.toUpperCase()] ?? "slate";
}
