"use client";

import { useState } from "react";
import { useDashboardBarrierFailures } from "@/hooks/use-dashboard-distributions";
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

export function BarrierSection() {
  const [window, setWindow] = useState<DashboardWindow>("30d");
  const { data, isLoading, isError, error, refetch } = useDashboardBarrierFailures(window);

  const totalFailures = data?.reduce((acc, p) => acc + p.failed_count, 0) ?? 0;
  const maxFailed = Math.max(...(data?.map((p) => p.failed_count) ?? [1]), 1);

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
          <>
            <p className="sr-only" aria-live="polite">
              Barrier failures: {data.map((p) => `${formatDate(p.date)}: ${p.failed_count}`).join(", ")}
            </p>
            {/* Bar chart of barrier failures over time */}
            <div
              role="img"
              aria-label={`Barrier failures over the last ${WINDOWS.find((w) => w.value === window)?.label}`}
              className="flex h-40 items-end gap-1"
            >
              {data.map((point) => (
                <div
                  key={point.date}
                  className="group relative flex flex-1 flex-col items-center justify-end"
                  title={`${formatDate(point.date)}: ${point.failed_count} barrier failures`}
                >
                  <div
                    className="w-full rounded-t-sm bg-red-400 transition-all group-hover:bg-red-500"
                    style={{ height: `${(point.failed_count / maxFailed) * 100}%` }}
                    aria-hidden="true"
                  />
                  {data.length <= 14 && (
                    <p className="mt-1 truncate text-[10px] text-slate-400" aria-hidden="true">
                      {formatDate(point.date)}
                    </p>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
              <span className="inline-block h-3 w-3 rounded-sm bg-red-400" aria-hidden="true" />
              Barrier failures per day
            </div>
          </>
        )}
      </div>
    </section>
  );
}
