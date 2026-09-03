import { apiClient, type ApiClient } from "@/lib/api/client";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/api";

export const authApi = {
  login(payload: LoginRequest, client: ApiClient = apiClient): Promise<TokenResponse> { return client.post("/auth/login", payload, { token: null }); },
  register(payload: RegisterRequest, client: ApiClient = apiClient): Promise<User> { return client.post("/auth/register", payload, { token: null }); },
  me(client: ApiClient = apiClient): Promise<User> { return client.get("/auth/me"); },
};
