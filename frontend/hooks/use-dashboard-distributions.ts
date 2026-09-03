import { useQuery } from "@tanstack/react-query";
import { dashboardApi, type DashboardWindow } from "@/lib/api/dashboard";

export const DASHBOARD_LSR_DISTRIBUTION_KEY = ["dashboard", "lsr-distribution"] as const;
export function useDashboardLsrDistribution() {
  return useQuery({
    queryKey: DASHBOARD_LSR_DISTRIBUTION_KEY,
    queryFn: () => dashboardApi.lsrDistribution(),
    staleTime: 60_000,
  });
}

export const DASHBOARD_ACTIVITY_DISTRIBUTION_KEY = ["dashboard", "activity-distribution"] as const;
export function useDashboardActivityDistribution() {
  return useQuery({
    queryKey: DASHBOARD_ACTIVITY_DISTRIBUTION_KEY,
    queryFn: () => dashboardApi.activityDistribution(),
    staleTime: 60_000,
  });
}

export const DASHBOARD_HAZARD_DISTRIBUTION_KEY = ["dashboard", "hazard-distribution"] as const;
export function useDashboardHazardDistribution() {
  return useQuery({
    queryKey: DASHBOARD_HAZARD_DISTRIBUTION_KEY,
    queryFn: () => dashboardApi.hazardDistribution(),
    staleTime: 60_000,
  });
}

export const DASHBOARD_SITE_COMPARISON_KEY = ["dashboard", "site-comparison"] as const;
export function useDashboardSiteComparison() {
  return useQuery({
    queryKey: DASHBOARD_SITE_COMPARISON_KEY,
    queryFn: () => dashboardApi.siteComparison(),
    staleTime: 60_000,
  });
}

export const DASHBOARD_BARRIER_FAILURES_KEY = (window: DashboardWindow) =>
  ["dashboard", "barrier-failures", window] as const;

export function useDashboardBarrierFailures(window: DashboardWindow = "30d") {
  return useQuery({
    queryKey: DASHBOARD_BARRIER_FAILURES_KEY(window),
    queryFn: () => dashboardApi.barrierFailures(window),
    staleTime: 60_000,
  });
}
