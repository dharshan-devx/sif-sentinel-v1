import { apiClient, type ApiClient } from "@/lib/api/client";
import type { AnalysisResponse, MessageResponse, Report, ReportCreate, ReportPage, ReportUpdate } from "@/types/api";

export interface ReportListParams { page?: number; page_size?: number; site_id?: string; report_type?: string; status?: string; source_type?: string; date_from?: string; date_to?: string; search?: string }
const query = (values: Record<string, string | number | undefined>) => {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => { if (value !== undefined) params.set(key, String(value)); });
  return params.size ? `?${params}` : "";
};
export const reportsApi = {
  list(params: ReportListParams = {}, client: ApiClient = apiClient): Promise<ReportPage> { return client.get(`/reports${query(params)}`); },
  get(reportId: string, client: ApiClient = apiClient): Promise<Report> { return client.get(`/reports/${encodeURIComponent(reportId)}`); },
  create(payload: ReportCreate, client: ApiClient = apiClient): Promise<Report> { return client.post("/reports", payload); },
  update(reportId: string, payload: ReportUpdate, client: ApiClient = apiClient): Promise<Report> { return client.patch(`/reports/${encodeURIComponent(reportId)}`, payload); },
  remove(reportId: string, client: ApiClient = apiClient): Promise<MessageResponse> { return client.delete(`/reports/${encodeURIComponent(reportId)}`); },
  analyze(reportId: string, client: ApiClient = apiClient): Promise<AnalysisResponse> { return client.post(`/reports/${encodeURIComponent(reportId)}/analyze`); },
};
