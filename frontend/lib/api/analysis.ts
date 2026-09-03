import { apiClient, type ApiClient } from "@/lib/api/client";
import type { AnalysisResponse } from "@/types/api";
export const analysisApi = { analyzeText(text: string, client: ApiClient = apiClient): Promise<AnalysisResponse> { return client.post("/analyze", { text }); } };
