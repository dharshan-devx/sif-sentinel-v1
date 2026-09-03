"use client";

import { useState } from "react";
import { useDashboardTrend } from "@/hooks/use-dashboard-summary";
import type { DashboardWindow } from "@/lib/api/dashboard";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

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

export function TrendSectionSkeleton() {
  return (
    <section aria-label="Safety trend loading" aria-busy="true">
      <Skeleton className="mb-4 h-5 w-48" />
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <Skeleton className="h-64 w-full" />
      </div>
    </section>
  );
}

export function TrendSection() {
  const [window, setWindow] = useState<DashboardWindow>("30d");
  const { data, isLoading, isError, error, refetch } = useDashboardTrend(window);

  if (isError) {
    return (
      <ErrorState
        error={error}
        retry={() => void refetch()}
      />
    );
  }

  return (
    <section aria-labelledby="trend-heading">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 id="trend-heading" className="text-sm font-semibold uppercase tracking-widest text-slate-500">
          SIF Trend
        </h2>
        <div role="group" aria-label="Trend window" className="flex gap-1">
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
          <Skeleton className="h-64 w-full" />
        ) : !data || data.length === 0 ? (
          <p className="flex h-64 items-center justify-center text-sm text-slate-400" role="status">
            Insufficient data to display this trend. Reports will appear once the system receives incidents.
          </p>
        ) : (
          <div 
            className="h-64 w-full"
            role="img"
            aria-label={`SIF trend over the last ${WINDOWS.find((w) => w.value === window)?.label}`}
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
                <Legend iconType="circle" wrapperStyle={{ fontSize: "12px", color: "#64748b", paddingTop: "10px" }} />
                <Bar name="Total reports" dataKey="total_reports" stackId="a" fill="#bae6fd" radius={[0, 0, 0, 0]} />
                <Bar name="SIF-potential" dataKey="sif_reports" stackId="b" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="sr-only" aria-live="polite">
              Showing {data.length} data points over the selected window. Peak total reports: {Math.max(...data.map((p) => p.total_reports))}.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
