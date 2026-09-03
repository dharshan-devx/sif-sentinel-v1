import { apiClient, type ApiClient } from "@/lib/api/client";
import type { MessageResponse, PrecursorDetail, PrecursorGraph, PrecursorSummary } from "@/types/api";

export interface PrecursorParams { site?: string; activity?: string; hazard?: string; barrier?: string; priority?: string; date_from?: string; date_to?: string; limit?: number; sort?: "risk_score" | "recent" }
const makeQuery = (params: PrecursorParams): string => {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value !== undefined) query.set(key, String(value));
  return query.size ? `?${query}` : "";
};
export const precursorsApi = {
  list(params: PrecursorParams = {}, client: ApiClient = apiClient): Promise<PrecursorSummary[]> { return client.get(`/precursors${makeQuery(params)}`); },
  trends(limit?: number, client: ApiClient = apiClient): Promise<PrecursorSummary[]> { return client.get(`/precursors/trends${limit ? `?limit=${limit}` : ""}`); },
  rebuild(client: ApiClient = apiClient): Promise<MessageResponse> { return client.post("/precursors/rebuild"); },
  get(id: string, client: ApiClient = apiClient): Promise<PrecursorDetail> { return client.get(`/precursors/${encodeURIComponent(id)}`); },
  graph(id: string, client: ApiClient = apiClient): Promise<PrecursorGraph> { return client.get(`/precursors/${encodeURIComponent(id)}/graph`); },
};
