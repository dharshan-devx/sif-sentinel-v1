"use client";

import Link from "next/link";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { Skeleton } from "@/components/ui/skeleton";

interface AttentionItem {
  count: number;
  label: string;
  description: string;
  href: string;
  tone: "warning" | "danger" | "critical";
}

const toneClass: Record<AttentionItem["tone"], string> = {
  warning: "border-l-amber-400 bg-amber-50",
  danger: "border-l-red-400 bg-red-50",
  critical: "border-l-violet-400 bg-violet-50",
};

const toneCountClass: Record<AttentionItem["tone"], string> = {
  warning: "text-amber-800",
  danger: "text-red-700",
  critical: "text-violet-800",
};

export function AttentionPanel() {
  const { data, isLoading } = useDashboardSummary();

  if (isLoading) {
    return (
      <section aria-label="Attention signals loading" aria-busy="true">
        <Skeleton className="mb-4 h-5 w-40" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
        </div>
      </section>
    );
  }

  if (!data) return null;

  const items: AttentionItem[] = [
    data.review_required > 0 && {
      count: data.review_required,
      label: "Reviews awaiting decision",
      description: "Reports pending a human reviewer's approve / reject / modify decision.",
      href: "/reviews",
      tone: "warning" as const,
    },
    data.high_risk_reports > 0 && {
      count: data.high_risk_reports,
      label: "High-risk reports",
      description: "Reports with a high or critical deterministic risk score that may require immediate attention.",
      href: "/reports",
      tone: "danger" as const,
    },
    data.active_precursors > 0 && {
      count: data.active_precursors,
      label: "Active precursor patterns",
      description: "Recurring activity–hazard–barrier–failure combinations that indicate systemic risk.",
      href: "/precursors",
      tone: "critical" as const,
    },
  ].filter(Boolean) as AttentionItem[];

  if (items.length === 0) {
    return (
      <section aria-labelledby="attention-heading">
        <h2 id="attention-heading" className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-500">
          Attention &amp; Action Signals
        </h2>
        <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">
          No items currently require immediate attention.
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="attention-heading">
      <h2 id="attention-heading" className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-500">
        Attention &amp; Action Signals
      </h2>
      <ul className="space-y-3" role="list">
        {items.map((item) => (
          <li key={item.label}>
            <Link
              href={item.href}
              className={`block rounded-xl border border-slate-200 border-l-4 p-4 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500 ${toneClass[item.tone]}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className={`text-2xl font-bold tabular-nums ${toneCountClass[item.tone]}`}>
                    {item.count.toLocaleString()}
                  </p>
                  <p className="mt-0.5 font-semibold text-slate-800">{item.label}</p>
                  <p className="mt-1 text-xs text-slate-600">{item.description}</p>
                </div>
                <span className="shrink-0 text-xs font-semibold text-slate-400">View →</span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
