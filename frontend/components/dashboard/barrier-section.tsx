"use client";

import { useState } from "react";
import { useDashboardBarrierFailures } from "@/hooks/use-dashboard-distributions";
import type { DashboardWindow } from "@/lib/api/dashboard";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

const WINDOWS: { value: DashboardWindow; label: string }[] = [
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "90d", label: "90 days" },
  { value: "1y", label: "1 year" },
];

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

export function BarrierSection() {
  const [window, setWindow] = useState<DashboardWindow>("30d");
  const { data, isLoading, isError, error, refetch } = useDashboardBarrierFailures(window);

  const totalFailures = data?.reduce((acc, p) => acc + p.failed_count, 0) ?? 0;

  return (
    <section aria-labelledby="barrier-heading">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2
            id="barrier-heading"
            className="text-sm font-semibold uppercase tracking-widest text-slate-500"
          >
            Barrier &amp; Control Failures
          </h2>
          {!isLoading && !isError && data && data.length > 0 && (
            <p className="mt-0.5 text-xs text-slate-500">
              {totalFailures} total barrier failures in the selected period
            </p>
          )}
        </div>
        <div role="group" aria-label="Barrier failure window" className="flex gap-1">
          {WINDOWS.map((w) => (
            <button
              key={w.value}
              type="button"
              onClick={() => setWindow(w.value)}
              aria-pressed={window === w.value}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500 ${
                window === w.value
                  ? "bg-sky-700 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : isError ? (
          <ErrorState
            error={error}
            retry={() => void refetch()}
          />
        ) : !data || data.length === 0 ? (
          <p className="flex h-32 items-center justify-center text-sm text-slate-400" role="status">
            No barrier failures recorded in this period.
          </p>
        ) : (
          <div 
            className="h-40 w-full"
            role="img"
            aria-label={`Barrier failures over the last ${WINDOWS.find((w) => w.value === window)?.label}`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: "#64748b" }}
                  dy={10}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: "#64748b" }}
                />
                <Tooltip 
                  cursor={{ fill: "#f1f5f9" }}
                  contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                  labelFormatter={(label) => formatDate(label as string)}
                />
                <Bar name="Barrier failures" dataKey="failed_count" fill="#f87171" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="sr-only" aria-live="polite">
              Barrier failures: {data.map((p) => `${formatDate(p.date)}: ${p.failed_count}`).join(", ")}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
