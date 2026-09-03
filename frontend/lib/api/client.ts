import { tokenStore } from "@/lib/auth/token-store";
import type { BackendErrorBody } from "@/types/api";

const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_TIMEOUT_MS = 15_000;

export interface ApiClientOptions {
  baseUrl?: string;
  getToken?: () => string | null;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
}

export interface RequestOptions extends Omit<RequestInit, "body" | "headers"> {
  body?: unknown;
  headers?: HeadersInit;
  token?: string | null;
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly details: unknown,
    public readonly requestId: string | null,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

function isBackendError(value: unknown): value is BackendErrorBody {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<BackendErrorBody>;
  return candidate.success === false && typeof candidate.error?.code === "string" && typeof candidate.error.message === "string";
}

function normaliseBaseUrl(url: string): string {
  return url.replace(/\/$/, "");
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly getToken: () => string | null;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = normaliseBaseUrl(options.baseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL);
    this.getToken = options.getToken ?? tokenStore.get;
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const controller = new AbortController();
    const timeout = globalThis.setTimeout(() => controller.abort(), this.timeoutMs);
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");
    const token = options.token === undefined ? this.getToken() : options.token;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (options.body !== undefined) headers.set("Content-Type", "application/json");

    try {
      const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
        ...options,
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
        signal: controller.signal,
      });
      const requestId = response.headers.get("X-Request-ID");
      const text = await response.text();
      const payload: unknown = text ? safelyParseJson(text) : undefined;

      if (!response.ok) {
        if (isBackendError(payload)) {
          const error = new ApiClientError(payload.error.message, response.status, payload.error.code, payload.error.details, payload.request_id ?? requestId);
          notifyUnauthorized(error);
          throw error;
        }
        const error = new ApiClientError("The service could not complete this request.", response.status, "HTTP_ERROR", undefined, requestId);
        notifyUnauthorized(error);
        throw error;
      }
      return payload as T;
    } catch (error) {
      if (error instanceof ApiClientError) throw error;
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiClientError("The request timed out. Please try again.", 0, "TIMEOUT", undefined, null);
      }
      throw new ApiClientError("The service could not be reached. Please try again.", 0, "NETWORK_ERROR", undefined, null);
    } finally {
      globalThis.clearTimeout(timeout);
    }
  }

  get<T>(path: string, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }
  post<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "POST", body });
  }
  patch<T>(path: string, body: unknown, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "PATCH", body });
  }
  delete<T>(path: string, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }
}

function safelyParseJson(text: string): unknown {
  try { return JSON.parse(text) as unknown; } catch { return undefined; }
}

export const apiClient = new ApiClient();
export function isApiClientError(error: unknown): error is ApiClientError { return error instanceof ApiClientError; }

function notifyUnauthorized(error: ApiClientError): void {
  if (error.status === 401 && typeof window !== "undefined") window.dispatchEvent(new Event("sif:unauthorized"));
}
