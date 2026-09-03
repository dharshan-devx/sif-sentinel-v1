import { apiClient, type ApiClient } from "@/lib/api/client";
import type { InterventionRead, InterventionReviewRequest, InterventionSummary } from "@/types/api";
export const interventionsApi = {
  list(params: { report_id?: string; priority?: string } = {}, client: ApiClient = apiClient): Promise<InterventionRead[]> { const q = new URLSearchParams(); if (params.report_id) q.set("report_id", params.report_id); if (params.priority) q.set("priority", params.priority); return client.get(`/interventions${q.size ? `?${q}` : ""}`); },
  summary(client: ApiClient = apiClient): Promise<InterventionSummary> { return client.get("/interventions/summary"); },
  get(id: string, client: ApiClient = apiClient): Promise<InterventionRead> { return client.get(`/interventions/${encodeURIComponent(id)}`); },
  review(id: string, payload: InterventionReviewRequest, client: ApiClient = apiClient): Promise<InterventionRead> { return client.post(`/interventions/${encodeURIComponent(id)}/review`, payload); },
};
