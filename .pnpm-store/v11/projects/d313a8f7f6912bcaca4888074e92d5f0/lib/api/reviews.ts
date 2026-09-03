import { apiClient, type ApiClient } from "@/lib/api/client";
import type { DecisionResponse, ReviewDecisionRequest, ReviewQueueItem } from "@/types/api";
export type ReviewStatusFilter = "PENDING" | "REVIEWED" | "ALL";
export const reviewsApi = {
  list(params: { page?: number; page_size?: number; status?: ReviewStatusFilter } = {}, client: ApiClient = apiClient): Promise<ReviewQueueItem[]> { const q = new URLSearchParams(); if (params.page !== undefined) q.set("page", String(params.page)); if (params.page_size !== undefined) q.set("page_size", String(params.page_size)); if (params.status !== undefined) q.set("status", params.status); return client.get(`/reviews${q.size ? `?${q}` : ""}`); },
  get(id: string, client: ApiClient = apiClient): Promise<ReviewQueueItem> { return client.get(`/reviews/${encodeURIComponent(id)}`); },
  decide(id: string, payload: ReviewDecisionRequest, client: ApiClient = apiClient): Promise<DecisionResponse> { return client.post(`/reviews/${encodeURIComponent(id)}/decision`, payload); },
};
