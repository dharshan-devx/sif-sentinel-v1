"use client";

import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { KpiCard, KpiCardSkeleton } from "@/components/dashboard/kpi-card";
import { isApiClientError } from "@/lib/api/client";
import { ErrorState } from "@/components/ui/error-state";
import { ForbiddenState } from "@/components/ui/forbidden-state";

export function SummarySectionSkeleton() {
  return (
    <section aria-label="Safety summary loading" aria-busy="true">
      <div className="mb-4">
        <div className="h-5 w-48 animate-pulse rounded bg-slate-200" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }, (_, i) => <KpiCardSkeleton key={i} />)}
      </div>
    </section>
  );
}

export function SummarySection() {
  const { data, isLoading, isError, error, refetch } = useDashboardSummary();

  if (isLoading) return <SummarySectionSkeleton />;

  if (isError) {
    if (isApiClientError(error) && error.status === 403) {
      return <ForbiddenState />;
    }
    return (
      <ErrorState
        error={error}
        retry={() => void refetch()}
      />
    );
  }

  if (!data) return null;

  const sifRatePct = (data.sif_rate * 100).toFixed(1);
  const highRiskRatePct = (data.high_risk_rate * 100).toFixed(1);

  return (
    <section aria-labelledby="summary-heading">
      <h2 id="summary-heading" className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-500">
        Executive Safety Summary
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total Reports"
          value={data.total_reports}
          help="All reports ingested across all sites"
          tone="neutral"
        />
        <KpiCard
          label="SIF-Potential Reports"
          value={data.total_sif_reports}
          help="Reports classified as having serious-injury or fatality potential"
          tone={data.total_sif_reports > 0 ? "warning" : "neutral"}
        />
        <KpiCard
          label="High-Risk Reports"
          value={data.high_risk_reports}
          help="Reports with a high or critical deterministic risk score"
          tone={data.high_risk_reports > 0 ? "danger" : "neutral"}
        />
        <KpiCard
          label="Awaiting Review"
          value={data.review_required}
          help="Reports routed to human review queue — require a reviewer decision"
          tone={data.review_required > 0 ? "warning" : "neutral"}
        />
        <KpiCard
          label="Active Precursor Patterns"
          value={data.active_precursors}
          help="Recurring precursor patterns identified across the incident database"
          tone={data.active_precursors > 0 ? "critical" : "neutral"}
        />
        <KpiCard
          label="Sites Monitored"
          value={data.sites_monitored}
          help="Number of sites with at least one ingested report"
          tone="neutral"
        />
        <KpiCard
          label="SIF Rate"
          value={sifRatePct}
          suffix="%"
          help="Proportion of all reports classified as SIF-potential"
          tone={data.sif_rate > 0.3 ? "danger" : data.sif_rate > 0.15 ? "warning" : "neutral"}
        />
        <KpiCard
          label="High-Risk Rate"
          value={highRiskRatePct}
          suffix="%"
          help="Proportion of all reports with high deterministic risk scores"
          tone={data.high_risk_rate > 0.2 ? "danger" : data.high_risk_rate > 0.1 ? "warning" : "neutral"}
        />
      </div>
    </section>
  );
}
