import { useQuery } from "@tanstack/react-query";
import { dashboardApi, type DashboardWindow } from "@/lib/api/dashboard";

export const DASHBOARD_SUMMARY_KEY = ["dashboard", "summary"] as const;

export function useDashboardSummary() {
  return useQuery({
    queryKey: DASHBOARD_SUMMARY_KEY,
    queryFn: () => dashboardApi.summary(),
    staleTime: 60_000, // 1 minute
  });
}

export const DASHBOARD_TREND_KEY = (window: DashboardWindow) =>
  ["dashboard", "trend", window] as const;

export function useDashboardTrend(window: DashboardWindow = "30d") {
  return useQuery({
    queryKey: DASHBOARD_TREND_KEY(window),
    queryFn: () => dashboardApi.sifTrend(window),
    staleTime: 60_000,
  });
}
