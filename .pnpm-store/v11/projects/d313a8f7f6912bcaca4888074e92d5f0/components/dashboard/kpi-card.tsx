"use client";

import { cn } from "@/lib/utils/cn";
import { Skeleton } from "@/components/ui/skeleton";

interface KpiCardProps {
  label: string;
  value: number | string;
  help?: string;
  tone?: "neutral" | "warning" | "danger" | "critical";
  suffix?: string;
  icon?: React.ReactNode;
}

const toneStyles: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  neutral: "border-slate-200",
  warning: "border-amber-300 bg-amber-50/40",
  danger: "border-red-300 bg-red-50/40",
  critical: "border-violet-300 bg-violet-50/40",
};

const toneValueStyles: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  neutral: "text-slate-950",
  warning: "text-amber-800",
  danger: "text-red-700",
  critical: "text-violet-800",
};

export function KpiCard({ label, value, help, tone = "neutral", suffix, icon }: KpiCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-white p-5 shadow-sm transition-shadow hover:shadow-md",
        toneStyles[tone]
      )}
      role="region"
      aria-label={label}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-600">{label}</p>
        {icon && <span aria-hidden="true" className="text-slate-400">{icon}</span>}
      </div>
      <p className={cn("mt-2 text-3xl font-bold tabular-nums", toneValueStyles[tone])}>
        {typeof value === "number" ? value.toLocaleString() : value}
        {suffix && <span className="ml-1 text-lg font-medium text-slate-500">{suffix}</span>}
      </p>
      {help && (
        <p className="mt-1.5 text-xs text-slate-500" id={`kpi-help-${label.replace(/\s+/g, "-").toLowerCase()}`}>
          {help}
        </p>
      )}
    </div>
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-busy="true" aria-label="Loading metric">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="mt-3 h-9 w-24" />
      <Skeleton className="mt-2 h-3 w-48" />
    </div>
  );
}
