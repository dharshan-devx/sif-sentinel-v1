import { apiClient, type ApiClient } from "@/lib/api/client";
import type { LifeSavingRule, RuleAnalytics } from "@/types/api";
export const rulesApi = {
  list(client: ApiClient = apiClient): Promise<LifeSavingRule[]> { return client.get("/rules"); },
  get(id: string, client: ApiClient = apiClient): Promise<LifeSavingRule> { return client.get(`/rules/${encodeURIComponent(id)}`); },
  analytics(id: string, client: ApiClient = apiClient): Promise<RuleAnalytics> { return client.get(`/rules/${encodeURIComponent(id)}/analytics`); },
};
