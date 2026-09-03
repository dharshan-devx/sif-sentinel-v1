import { SummarySection } from "@/components/dashboard/summary-section";
import { TrendSection } from "@/components/dashboard/trend-section";
import { DistributionsSection } from "@/components/dashboard/distributions-section";
import { BarrierSection } from "@/components/dashboard/barrier-section";
import { AttentionPanel } from "@/components/dashboard/attention-panel";

export const metadata = {
  title: "Safety Intelligence Dashboard — SIF SENTINEL",
  description: "Operational overview of SIF precursor detection, risk signals, and safety intelligence.",
};

export default function DashboardPage() {
  return (
    <div className="space-y-10">
      {/* Page header */}
      <header>
        <h1 className="text-2xl font-bold text-slate-950">Safety Intelligence Dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Current safety posture across monitored operations. All values are sourced from the
          deterministic backend intelligence pipeline and represent authoritative safety data.
        </p>
      </header>

      {/* Section 1 — Executive KPIs */}
      <SummarySection />

      {/* Main grid — trend + attention, then distributions + barrier */}
      <div className="grid grid-cols-1 gap-10 xl:grid-cols-[1fr_320px]">
        <div className="space-y-10">
          {/* Section 2 — SIF Trend */}
          <TrendSection />

          {/* Section 3 — Safety Distributions */}
          <DistributionsSection />

          {/* Section 4 — Barrier Control Failures */}
          <BarrierSection />
        </div>

        {/* Section 5 — Attention / Action Signals */}
        <div>
          <AttentionPanel />
        </div>
      </div>
    </div>
  );
}
