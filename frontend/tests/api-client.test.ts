import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError, normalizeApiError } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/config";

function response(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), { status: 200, ...init, headers: { "content-type": "application/json", ...init.headers } });
}

describe("ApiClient", () => {
  it("uses one normalized API root and sends JSON requests", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ saved: true }));
    const client = new ApiClient({ baseUrl: "https://api.example.test/api/v1/", fetcher });
    await expect(client.post("reports", { text: "A safety observation" })).resolves.toEqual({ saved: true });
    expect(fetcher).toHaveBeenCalledWith("https://api.example.test/api/v1/reports", expect.objectContaining({ method: "POST", body: JSON.stringify({ text: "A safety observation" }) }));
  });

  it("adds the API version once when an origin is configured", () => {
    expect(getApiBaseUrl("https://api.example.test/")).toBe("https://api.example.test/api/v1");
    expect(getApiBaseUrl("https://api.example.test/api/v1")).toBe("https://api.example.test/api/v1");
  });

  it("normalizes controlled errors and preserves the request ID", async () => {
    const fetcher = vi.fn().mockResolvedValue(response({ success: false, error: { code: "VALIDATION_ERROR", message: "Report text is required", details: [{ loc: ["text"] }] }, request_id: "body-id" }, { status: 422, headers: { "X-Request-ID": "header-id" } }));
    const client = new ApiClient({ baseUrl: "https://api.example.test", fetcher });
    await expect(client.get("health")).rejects.toMatchObject({ status: 422, code: "VALIDATION_ERROR", requestId: "body-id", message: "Report text is required" });
  });

  it("does not expose an internal-server message", () => {
    const error = normalizeApiError(500, { error: { code: "INTERNAL_ERROR", message: "Traceback: database password" } }, "req-7");
    expect(error.message).toBe("The service could not complete this request.");
    expect(error.requestId).toBe("req-7");
  });

  it("returns a normalized timeout and network error", async () => {
    const timeoutClient = new ApiClient({ baseUrl: "https://api.example.test", timeoutMs: 1, fetcher: (_url, init) => new Promise((_resolve, reject) => init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")))) });
    await expect(timeoutClient.get("health")).rejects.toMatchObject({ code: "REQUEST_TIMEOUT", status: 0 });
    const networkClient = new ApiClient({ baseUrl: "https://api.example.test", fetcher: vi.fn().mockRejectedValue(new TypeError("offline")) });
    await expect(networkClient.get("health")).rejects.toBeInstanceOf(ApiError);
    await expect(networkClient.get("health")).rejects.toMatchObject({ code: "NETWORK_ERROR" });
  });
});
