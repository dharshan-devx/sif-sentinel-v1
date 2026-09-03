import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiClientError } from "@/lib/api/client";

describe("ApiClient", () => {
  it("uses the configured base URL, bearer token, JSON, and Accept header", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { headers: { "X-Request-ID": "req-123" } })) as unknown as typeof fetch;
    const client = new ApiClient({ baseUrl: "http://api.test/api/v1/", getToken: () => "token", fetchImpl });
    await expect(client.post<{ status: string }>("/health", { check: true })).resolves.toEqual({ status: "ok" });
    expect(fetchImpl).toHaveBeenCalledWith("http://api.test/api/v1/health", expect.objectContaining({ method: "POST", body: JSON.stringify({ check: true }) }));
    const request = vi.mocked(fetchImpl).mock.calls[0]?.[1] as RequestInit;
    expect(new Headers(request.headers).get("Authorization")).toBe("Bearer token");
    expect(new Headers(request.headers).get("Accept")).toBe("application/json");
  });

  it("preserves the controlled backend error and request ID", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: false, error: { code: "VALIDATION_ERROR", message: "Request validation failed", details: [{ loc: ["body", "email"] }] }, request_id: "body-request" }), { status: 422, headers: { "X-Request-ID": "header-request" } })) as unknown as typeof fetch;
    const client = new ApiClient({ baseUrl: "http://api.test", fetchImpl });
    await expect(client.get("/reports")).rejects.toMatchObject({ status: 422, code: "VALIDATION_ERROR", requestId: "body-request" });
  });
});
