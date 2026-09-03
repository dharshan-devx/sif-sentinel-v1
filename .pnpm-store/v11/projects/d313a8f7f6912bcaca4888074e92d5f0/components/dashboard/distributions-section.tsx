"use client";

import {
  useDashboardActivityDistribution,
  useDashboardHazardDistribution,
  useDashboardLsrDistribution,
} from "@/hooks/use-dashboard-distributions";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import type { DistributionItem } from "@/types/api";

interface HorizontalBarChartProps {
  title: string;
  data: DistributionItem[];
  "aria-labelledby": string;
}

function HorizontalBarChart({ title, data, "aria-labelledby": labelledBy }: HorizontalBarChartProps) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-slate-400" role="status">
        No data available for {title.toLowerCase()}.
      </p>
    );
  }

  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div role="img" aria-labelledby={labelledBy}>
      <p className="sr-only" aria-live="polite">
        {title}: {data.map((d) => `${d.name} — ${d.count} reports (${d.sif_count} SIF, ${d.percentage.toFixed(1)}%)`).join("; ")}
      </p>
      <ul className="mt-3 space-y-2.5" aria-hidden="true">
        {data.slice(0, 8).map((item) => (
          <li key={item.name} className="grid grid-cols-[1fr_auto] gap-3 items-center">
            <div>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="truncate font-medium text-slate-700" title={item.name}>
                  {item.name}
                </span>
                <span className="ml-2 shrink-0 text-slate-500">{item.count}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-sky-500 transition-all"
                  style={{ width: `${(item.count / maxCount) * 100}%` }}
                />
              </div>
              {item.sif_count > 0 && (
                <p className="mt-0.5 text-[10px] text-amber-700">
                  {item.sif_count} SIF-potential ({(item.sif_density * 100).toFixed(1)}% density)
                </p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DistributionCard({
  id,
  title,
  isLoading,
  isError,
  error,
  data,
  onRetry,
}: {
  id: string;
  title: string;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  data: DistributionItem[] | undefined;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 id={id} className="text-sm font-bold text-slate-950">
        {title}
      </h3>
      {isLoading ? (
        <div className="mt-3 space-y-2.5">
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
        </div>
      ) : isError ? (
        <ErrorState
          error={error}
          retry={onRetry}
        />
      ) : (
        <HorizontalBarChart title={title} data={data ?? []} aria-labelledby={id} />
      )}
    </div>
  );
}

export function DistributionsSection() {
  const lsr = useDashboardLsrDistribution();
  const activity = useDashboardActivityDistribution();
  const hazard = useDashboardHazardDistribution();

  return (
    <section aria-labelledby="distributions-heading">
      <h2
        id="distributions-heading"
        className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-500"
      >
        Safety Distributions
      </h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <DistributionCard
          id="lsr-dist-title"
          title="Life-Saving Rule Distribution"
          isLoading={lsr.isLoading}
          isError={lsr.isError}
          error={lsr.error}
          data={lsr.data}
          onRetry={() => void lsr.refetch()}
        />
        <DistributionCard
          id="activity-dist-title"
          title="Activity Distribution"
          isLoading={activity.isLoading}
          isError={activity.isError}
          error={activity.error}
          data={activity.data}
          onRetry={() => void activity.refetch()}
        />
        <DistributionCard
          id="hazard-dist-title"
          title="Hazard Distribution"
          isLoading={hazard.isLoading}
          isError={hazard.isError}
          error={hazard.error}
          data={hazard.data}
          onRetry={() => void hazard.refetch()}
        />
      </div>
    </section>
  );
}
