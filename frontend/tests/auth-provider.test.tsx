import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClientError } from "@/lib/api/client";
import { tokenStore } from "@/lib/auth/token-store";

const mockAuthApi = vi.hoisted(() => ({ me: vi.fn(), login: vi.fn(), register: vi.fn() }));
vi.mock("@/lib/api/auth", () => ({ authApi: mockAuthApi }));

import { AuthProvider, useAuth } from "@/providers/auth-provider";

const user = { id: "u-1", email: "reviewer@example.com", full_name: "Reviewer", role: "REVIEWER" as const, is_active: true, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" };
function Probe() { const auth = useAuth(); return <><p data-testid="status">{auth.status}</p><p data-testid="name">{auth.user?.full_name ?? "none"}</p><p data-testid="error">{auth.initializationError ?? "none"}</p><button onClick={auth.signOut}>End session</button></>; }
function renderAuth(client = new QueryClient()) { return { client, ...render(<QueryClientProvider client={client}><AuthProvider><Probe /></AuthProvider></QueryClientProvider>) }; }

describe("authentication provider", () => {
  beforeEach(() => { window.sessionStorage.clear(); vi.clearAllMocks(); });
  it("starts unauthenticated when no session token exists", async () => { renderAuth(); await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated")); expect(mockAuthApi.me).not.toHaveBeenCalled(); });
  it("restores current user from a valid token", async () => { tokenStore.set("valid"); mockAuthApi.me.mockResolvedValue(user); renderAuth(); await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("authenticated")); expect(screen.getByTestId("name")).toHaveTextContent("Reviewer"); });
  it("clears an expired 401 token", async () => { tokenStore.set("expired"); mockAuthApi.me.mockRejectedValue(new ApiClientError("Invalid token", 401, "INVALID_TOKEN", {}, "req-1")); renderAuth(); await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated")); expect(tokenStore.get()).toBeNull(); });
  it("keeps a token on temporary initialization failure", async () => { tokenStore.set("maybe-valid"); mockAuthApi.me.mockRejectedValue(new ApiClientError("Unavailable", 503, "DATABASE_UNAVAILABLE", {}, "req-1")); renderAuth(); await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("unavailable")); expect(tokenStore.get()).toBe("maybe-valid"); });
  it("clears local auth and query cache on session end", async () => { tokenStore.set("valid"); mockAuthApi.me.mockResolvedValue(user); const { client } = renderAuth(); const clear = vi.spyOn(client, "clear"); await screen.findByText("authenticated"); await act(async () => { screen.getByRole("button", { name: "End session" }).click(); }); expect(tokenStore.get()).toBeNull(); expect(clear).toHaveBeenCalledOnce(); expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated"); });
});
