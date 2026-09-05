export interface HealthResponse {
  status: "ok";
  service: "sif-backend";
}

export interface ApiErrorPayload {
  success?: false;
  error?: { code?: string; message?: string; details?: unknown };
  request_id?: string | null;
}
