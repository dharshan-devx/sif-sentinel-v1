import { apiClient, type ApiClient } from "@/lib/api/client";
import type { BarrierFailurePoint, DashboardSummary, DistributionItem, TimeSeriesPoint } from "@/types/api";
export type DashboardWindow = "7d" | "30d" | "90d" | "1y";
export const dashboardApi = {
  summary(client: ApiClient = apiClient): Promise<DashboardSummary> { return client.get("/dashboard/summary"); },
  sifTrend(window: DashboardWindow = "30d", client: ApiClient = apiClient): Promise<TimeSeriesPoint[]> { return client.get(`/dashboard/sif-trend?window=${window}`); },
  lsrDistribution(client: ApiClient = apiClient): Promise<DistributionItem[]> { return client.get("/dashboard/lsr-distribution"); },
  siteComparison(client: ApiClient = apiClient): Promise<DistributionItem[]> { return client.get("/dashboard/site-comparison"); },
  activityDistribution(client: ApiClient = apiClient): Promise<DistributionItem[]> { return client.get("/dashboard/activity-distribution"); },
  hazardDistribution(client: ApiClient = apiClient): Promise<DistributionItem[]> { return client.get("/dashboard/hazard-distribution"); },
  barrierFailures(window: DashboardWindow = "30d", client: ApiClient = apiClient): Promise<BarrierFailurePoint[]> { return client.get(`/dashboard/barrier-failures?window=${window}`); },
};
