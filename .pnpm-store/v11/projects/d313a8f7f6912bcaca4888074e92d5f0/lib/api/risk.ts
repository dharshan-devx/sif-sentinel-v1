import { apiClient, type ApiClient } from "@/lib/api/client";
import type { BarrierRiskItem, RiskItem, SiteRiskItem } from "@/types/api";
export interface RiskParams { date_from?: string; date_to?: string; limit?: number }
const query = (params: RiskParams) => { const q = new URLSearchParams(); for (const [key, value] of Object.entries(params)) if (value !== undefined) q.set(key, String(value)); return q.size ? `?${q}` : ""; };
export const riskApi = {
  sites(params: RiskParams = {}, client: ApiClient = apiClient): Promise<SiteRiskItem[]> { return client.get(`/risk/sites${query(params)}`); },
  activities(params: RiskParams = {}, client: ApiClient = apiClient): Promise<RiskItem[]> { return client.get(`/risk/activities${query(params)}`); },
  hazards(params: RiskParams = {}, client: ApiClient = apiClient): Promise<RiskItem[]> { return client.get(`/risk/hazards${query(params)}`); },
  barriers(params: RiskParams = {}, client: ApiClient = apiClient): Promise<BarrierRiskItem[]> { return client.get(`/risk/barriers${query(params)}`); },
};
