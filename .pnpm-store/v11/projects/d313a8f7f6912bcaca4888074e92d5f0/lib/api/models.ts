import { apiClient, type ApiClient } from "@/lib/api/client";
export type ModelMetadata = Record<string, unknown>;
export interface ModelFeedback { total_predictions: number; reviewed_predictions: number; approved_predictions: number; corrected_predictions: number; correction_rate: number | null; human_review_metrics: Record<string, unknown> | string }
export interface ModelPerformance { offline_model_metrics: Record<string, unknown>; human_review_metrics: ModelFeedback }
export const modelsApi = {
  list(client: ApiClient = apiClient): Promise<ModelMetadata[]> { return client.get("/models"); },
  get(name: string, client: ApiClient = apiClient): Promise<ModelMetadata> { return client.get(`/models/${encodeURIComponent(name)}`); },
  metrics(name: string, client: ApiClient = apiClient): Promise<Record<string, unknown>> { return client.get(`/models/${encodeURIComponent(name)}/metrics`); },
  feedback(client: ApiClient = apiClient): Promise<ModelFeedback> { return client.get("/models/feedback"); },
  performance(client: ApiClient = apiClient): Promise<ModelPerformance> { return client.get("/models/performance"); },
};
