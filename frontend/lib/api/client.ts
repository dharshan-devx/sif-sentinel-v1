import { tokenStore } from "@/lib/auth";
import { getApiBaseUrl } from "@/lib/config";
import type { ApiErrorPayload, HealthResponse } from "@/types/api";
import { ApiError, normalizeApiError } from "./errors";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export interface ApiClientOptions {
  baseUrl?: string;
  timeoutMs?: number;
  fetcher?: typeof fetch;
  getAccessToken?: () => string | null | undefined;
}

export interface RequestOptions {
  body?: unknown;
  headers?: HeadersInit;
  signal?: AbortSignal;
  /** Used only by public auth calls, which must never send an old bearer token. */
  skipAuth?: boolean;
}

type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | undefined;

export function setUnauthorizedHandler(handler?: UnauthorizedHandler): void {
  unauthorizedHandler = handler;
}

function joinPath(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

export class ApiClient {
  private readonly baseUrl?: string;
  private readonly timeoutMs: number;
  private readonly fetcher: typeof fetch;
  private readonly getAccessToken?: () => string | null | undefined;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ? getApiBaseUrl(options.baseUrl) : undefined;
    this.timeoutMs = options.timeoutMs ?? 12_000;
    this.fetcher = options.fetcher ?? fetch;
    this.getAccessToken = options.getAccessToken;
  }

  get<T>(path: string, options?: Omit<RequestOptions, "body">) { return this.request<T>("GET", path, options); }
  post<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body">) { return this.request<T>("POST", path, { ...options, body }); }
  patch<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body">) { return this.request<T>("PATCH", path, { ...options, body }); }
  delete<T>(path: string, options?: Omit<RequestOptions, "body">) { return this.request<T>("DELETE", path, options); }

  health() { return this.get<HealthResponse>("/health"); }

  private async request<T>(method: HttpMethod, path: string, options: RequestOptions = {}): Promise<T> {
    const timeoutController = new AbortController();
    const timeout = globalThis.setTimeout(() => timeoutController.abort(), this.timeoutMs);
    const signal = options.signal ?? timeoutController.signal;
    const headers = new Headers({ Accept: "application/json", ...options.headers });
    const token = options.skipAuth ? null : (this.getAccessToken?.() ?? tokenStore.get());
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (options.body !== undefined) headers.set("Content-Type", "application/json");

    try {
      const response = await this.fetcher(joinPath(this.baseUrl ?? getApiBaseUrl(), path), {
        method,
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
        signal,
      });
      const requestId = response.headers.get("X-Request-ID");
      const contentType = response.headers.get("content-type") ?? "";
      const payload = contentType.includes("application/json")
        ? await response.json() as unknown
        : undefined;

      if (!response.ok) {
        const normalizedError = normalizeApiError(response.status, payload as ApiErrorPayload | undefined, requestId);
        if (response.status === 401 && token) unauthorizedHandler?.();
        throw normalizedError;
      }
      return payload as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (timeoutController.signal.aborted) {
        throw new ApiError({ status: 0, code: "REQUEST_TIMEOUT", message: "The request timed out. Please try again." });
      }
      throw new ApiError({ status: 0, code: "NETWORK_ERROR", message: "Unable to reach the service. Check your connection and try again." });
    } finally {
      globalThis.clearTimeout(timeout);
    }
  }
}

export const apiClient = new ApiClient();
