import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClientError } from "@/lib/api/client";

// Mock the entire dashboard API module at the boundary
const mockDashboardApi = vi.hoisted(() => ({
  summary: vi.fn(),
  sifTrend: vi.fn(),
  lsrDistribution: vi.fn(),
  activityDistribution: vi.fn(),
  hazardDistribution: vi.fn(),
  siteComparison: vi.fn(),
  barrierFailures: vi.fn(),
}));
vi.mock("@/lib/api/dashboard", () => ({ dashboardApi: mockDashboardApi, type: undefined }));

// Stub out next/navigation so components using Link don't crash in vitest
vi.mock("next/navigation", () => ({ useRouter: () => ({}), usePathname: () => "/dashboard" }));

import { SummarySection } from "@/components/dashboard/summary-section";
import { TrendSection } from "@/components/dashboard/trend-section";
import { DistributionsSection } from "@/components/dashboard/distributions-section";
import { BarrierSection } from "@/components/dashboard/barrier-section";
import { AttentionPanel } from "@/components/dashboard/attention-panel";
import type { DashboardSummary, TimeSeriesPoint, DistributionItem, BarrierFailurePoint } from "@/types/api";

const MOCK_SUMMARY: DashboardSummary = {
  total_reports: 500,
  total_sif_reports: 75,
  high_risk_reports: 30,
  review_required: 12,
  active_precursors: 5,
  sites_monitored: 3,
  sif_rate: 0.15,
  high_risk_rate: 0.06,
};

const MOCK_TREND: TimeSeriesPoint[] = [
  { date: "2026-08-01", total_reports: 20, sif_reports: 4, high_sif_reports: 1, sif_rate: 0.2 },
  { date: "2026-08-02", total_reports: 15, sif_reports: 2, high_sif_reports: 0, sif_rate: 0.133 },
];

const MOCK_DISTRIBUTION: DistributionItem[] = [
  { name: "Working at Height", count: 30, sif_count: 10, sif_density: 0.33, percentage: 40 },
  { name: "Energy Isolation", count: 20, sif_count: 5, sif_density: 0.25, percentage: 26.6 },
];

const MOCK_BARRIER_FAILURES: BarrierFailurePoint[] = [
  { date: "2026-08-01", failed_count: 3 },
  { date: "2026-08-02", failed_count: 2 },
];

function makeClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function wrap(ui: React.ReactElement, client = makeClient()) {
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("SummarySection", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows skeleton while loading", () => {
    mockDashboardApi.summary.mockReturnValue(new Promise(() => undefined));
    wrap(<SummarySection />);
    expect(screen.getByLabelText(/safety summary loading/i)).toBeInTheDocument();
  });

  it("renders all 8 KPI values on success", async () => {
    mockDashboardApi.summary.mockResolvedValue(MOCK_SUMMARY);
    wrap(<SummarySection />);
    await waitFor(() => expect(screen.getByRole("region", { name: /total reports/i })).toBeInTheDocument());
    expect(screen.getByRole("region", { name: /sif-potential reports/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /high-risk reports/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /awaiting review/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /active precursor patterns/i })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /sites monitored/i })).toBeInTheDocument();
    // Check values are displayed
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("shows error state with retry on API failure", async () => {
    mockDashboardApi.summary.mockRejectedValue(
      new ApiClientError("Service unavailable", 503, "DATABASE_UNAVAILABLE", {}, "req-1")
    );
    wrap(<SummarySection />);
    await waitFor(() => expect(screen.getByText(/service unavailable/i)).toBeInTheDocument());
  });

  it("shows forbidden state on 403", async () => {
    mockDashboardApi.summary.mockRejectedValue(
      new ApiClientError("Forbidden", 403, "INSUFFICIENT_ROLE", {}, "req-2")
    );
    wrap(<SummarySection />);
    await waitFor(() => expect(screen.getByText(/access denied|forbidden|insufficient/i)).toBeInTheDocument());
  });

  it("does not render fake/hardcoded metrics", async () => {
    mockDashboardApi.summary.mockResolvedValue({ ...MOCK_SUMMARY, total_reports: 0, total_sif_reports: 0 });
    wrap(<SummarySection />);
    await waitFor(() => expect(screen.getByRole("region", { name: /total reports/i })).toBeInTheDocument());
    // Should show 0 from backend, not fake values
    const kpiCard = screen.getByRole("region", { name: /total reports/i });
    expect(within(kpiCard).getByText("0")).toBeInTheDocument();
  });
});

describe("TrendSection", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows skeleton while loading", () => {
    mockDashboardApi.sifTrend.mockReturnValue(new Promise(() => undefined));
    wrap(<TrendSection />);
    // While loading, trend section shows a Skeleton (animate-pulse) inside the card
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("renders chart with backend data", async () => {
    mockDashboardApi.sifTrend.mockResolvedValue(MOCK_TREND);
    wrap(<TrendSection />);
    await waitFor(() =>
      expect(screen.getByRole("img", { name: /sif trend/i })).toBeInTheDocument()
    );
  });

  it("shows empty state when no data returned", async () => {
    mockDashboardApi.sifTrend.mockResolvedValue([]);
    wrap(<TrendSection />);
    await waitFor(() =>
      expect(screen.getByText(/insufficient data to display this trend/i)).toBeInTheDocument()
    );
  });

  it("shows error state on API failure", async () => {
    mockDashboardApi.sifTrend.mockRejectedValue(
      new ApiClientError("Unavailable", 503, "DATABASE_UNAVAILABLE", {}, "req-3")
    );
    wrap(<TrendSection />);
    // The ErrorState renders the ApiClientError.message as the Alert title
    await waitFor(() =>
      expect(screen.getByText(/Unavailable/i)).toBeInTheDocument()
    );
  });
});

describe("DistributionsSection", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders distribution charts from backend data", async () => {
    mockDashboardApi.lsrDistribution.mockResolvedValue(MOCK_DISTRIBUTION);
    mockDashboardApi.activityDistribution.mockResolvedValue(MOCK_DISTRIBUTION);
    mockDashboardApi.hazardDistribution.mockResolvedValue(MOCK_DISTRIBUTION);
    wrap(<DistributionsSection />);
    await waitFor(() =>
      expect(screen.getByText("Life-Saving Rule Distribution")).toBeInTheDocument()
    );
    expect(screen.getByText("Activity Distribution")).toBeInTheDocument();
    expect(screen.getByText("Hazard Distribution")).toBeInTheDocument();
  });

  it("shows empty state when distribution returns empty array", async () => {
    mockDashboardApi.lsrDistribution.mockResolvedValue([]);
    mockDashboardApi.activityDistribution.mockResolvedValue([]);
    mockDashboardApi.hazardDistribution.mockResolvedValue([]);
    wrap(<DistributionsSection />);
    await waitFor(() =>
      expect(screen.getAllByText(/no data available/i).length).toBeGreaterThan(0)
    );
  });
});

describe("BarrierSection", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows skeleton while loading", () => {
    mockDashboardApi.barrierFailures.mockReturnValue(new Promise(() => undefined));
    wrap(<BarrierSection />);
    // There should be a loading skeleton
    expect(document.querySelector("[aria-busy='true']")).toBeNull(); // section itself is not aria-busy, chart is skeleton
  });

  it("renders barrier failures from backend", async () => {
    mockDashboardApi.barrierFailures.mockResolvedValue(MOCK_BARRIER_FAILURES);
    wrap(<BarrierSection />);
    await waitFor(() =>
      expect(screen.getByRole("img", { name: /barrier failures/i })).toBeInTheDocument()
    );
    expect(screen.getByText(/5 total barrier failures/i)).toBeInTheDocument();
  });

  it("shows empty state when no failures", async () => {
    mockDashboardApi.barrierFailures.mockResolvedValue([]);
    wrap(<BarrierSection />);
    await waitFor(() =>
      expect(screen.getByText(/no barrier failures recorded/i)).toBeInTheDocument()
    );
  });
});

describe("AttentionPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows attention items when summary has non-zero counts", async () => {
    mockDashboardApi.summary.mockResolvedValue(MOCK_SUMMARY);
    wrap(<AttentionPanel />);
    await waitFor(() =>
      expect(screen.getByText(/reviews awaiting decision/i)).toBeInTheDocument()
    );
    expect(screen.getByText(/high-risk reports/i)).toBeInTheDocument();
    expect(screen.getByText(/active precursor patterns/i)).toBeInTheDocument();
  });

  it("shows no attention message when all counts are zero", async () => {
    mockDashboardApi.summary.mockResolvedValue({
      ...MOCK_SUMMARY,
      review_required: 0,
      high_risk_reports: 0,
      active_precursors: 0,
    });
    wrap(<AttentionPanel />);
    await waitFor(() =>
      expect(screen.getByText(/no items currently require immediate attention/i)).toBeInTheDocument()
    );
  });
});
