import type { AuthUser, LoginRequest, RegisterRequest, TokenResponse } from "@/types/api";
import { apiClient } from "./client";

export const authApi = {
  login: (payload: LoginRequest) => apiClient.post<TokenResponse>("/auth/login", payload, { skipAuth: true }),
  register: (payload: RegisterRequest) => apiClient.post<AuthUser>("/auth/register", payload, { skipAuth: true }),
  me: () => apiClient.get<AuthUser>("/auth/me"),
};
