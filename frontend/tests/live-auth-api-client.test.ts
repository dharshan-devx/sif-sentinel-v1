// @vitest-environment node
import { describe, expect, it } from "vitest";
import { ApiClient } from "@/lib/api";

const live = process.env.RUN_LIVE_AUTH_TEST === "1" ? it : it.skip;

describe("live authentication contract", () => {
  live("registers a Viewer, logs in, restores /auth/me, rejects invalid tokens, and preserves Viewer authorization", async () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL;
    const publicClient = new ApiClient({ baseUrl, timeoutMs: 8_000 });
    const email = `f2.${Date.now()}@example.com`;
    const password = "F2-safe-test-password";
    const registered = await publicClient.post<{ role: string }>("/auth/register", { email, password, full_name: "F2 Verification User" }, { skipAuth: true });
    expect(registered.role).toBe("VIEWER");
    const session = await publicClient.post<{ access_token: string }>("/auth/login", { email, password }, { skipAuth: true });
    const authenticatedClient = new ApiClient({ baseUrl, timeoutMs: 8_000, getAccessToken: () => session.access_token });
    await expect(authenticatedClient.get<{ email: string }>("/auth/me")).resolves.toMatchObject({ email });
    const invalidTokenClient = new ApiClient({ baseUrl, timeoutMs: 8_000, getAccessToken: () => "invalid-token" });
    await expect(invalidTokenClient.get("/auth/me")).rejects.toMatchObject({ status: 401 });
    await expect(authenticatedClient.post("/sites", { name: "No access", code: "NO-ACCESS", location: "Test", region: "Test" })).rejects.toMatchObject({ status: 403 });
  });
});
