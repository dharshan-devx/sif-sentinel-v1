"use client";

import { useState } from "react";
import { useDashboardTrend } from "@/hooks/use-dashboard-summary";
import type { DashboardWindow } from "@/lib/api/dashboard";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";

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

  const maxTotal = Math.max(...(data?.map((p) => p.total_reports) ?? [1]), 1);

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
          <>
            {/* Accessible text summary */}
            <p className="sr-only" aria-live="polite">
              Showing {data.length} data points over the selected window.
              Peak total reports: {Math.max(...data.map((p) => p.total_reports))}.
            </p>

            {/* Bar chart */}
            <div
              role="img"
              aria-label={`SIF trend over the last ${WINDOWS.find((w) => w.value === window)?.label}`}
              className="relative"
            >
              {/* Y-axis labels */}
              <div className="flex h-64 gap-1 items-end">
                {data.map((point) => {
                  const totalHeight = (point.total_reports / maxTotal) * 100;
                  const sifHeight = point.total_reports > 0
                    ? (point.sif_reports / point.total_reports) * totalHeight
                    : 0;

                  return (
                    <div
                      key={point.date}
                      className="group relative flex flex-1 flex-col items-center justify-end gap-0.5"
                      title={`${formatDate(point.date)}: ${point.total_reports} total, ${point.sif_reports} SIF (${(point.sif_rate * 100).toFixed(1)}%)`}
                    >
                      {/* Total bar */}
                      <div
                        className="w-full rounded-t-sm bg-sky-200 transition-all"
                        style={{ height: `${totalHeight}%` }}
                        aria-hidden="true"
                      >
                        {/* SIF overlay */}
                        <div
                          className="w-full rounded-t-sm bg-amber-500"
                          style={{ height: `${sifHeight > 0 ? (sifHeight / totalHeight) * 100 : 0}%` }}
                          aria-hidden="true"
                        />
                      </div>
                      {/* Date label (only show some to avoid clutter) */}
                      {data.length <= 14 && (
                        <p className="mt-1 truncate text-[10px] text-slate-400" aria-hidden="true">
                          {formatDate(point.date)}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3 rounded-sm bg-sky-200" aria-hidden="true" />
                Total reports
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3 rounded-sm bg-amber-500" aria-hidden="true" />
                SIF-potential reports
              </span>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
