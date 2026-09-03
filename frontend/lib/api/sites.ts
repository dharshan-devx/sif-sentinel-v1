import { apiClient, type ApiClient } from "@/lib/api/client";
import type { Site, SiteCreate, SiteUpdate } from "@/types/api";
export const sitesApi = {
  list(client: ApiClient = apiClient): Promise<Site[]> { return client.get("/sites"); },
  get(id: string, client: ApiClient = apiClient): Promise<Site> { return client.get(`/sites/${encodeURIComponent(id)}`); },
  create(payload: SiteCreate, client: ApiClient = apiClient): Promise<Site> { return client.post("/sites", payload); },
  update(id: string, payload: SiteUpdate, client: ApiClient = apiClient): Promise<Site> { return client.patch(`/sites/${encodeURIComponent(id)}`, payload); },
};
