export interface HealthResponse {
  status: "ok";
  service: "sif-backend";
}

export interface ApiErrorPayload {
  success?: false;
  error?: { code?: string; message?: string; details?: unknown };
  request_id?: string | null;
}

export type UserRole = "ADMIN" | "HSE_MANAGER" | "HSE_ANALYST" | "REVIEWER" | "VIEWER";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest { email: string; password: string; }
export interface RegisterRequest extends LoginRequest { full_name: string; }
export interface TokenResponse { access_token: string; token_type: "bearer"; user: AuthUser; }
