import { ApiClientError, isBackendError, safelyParseJson } from "@/lib/api/errors";

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";
const DEFAULT_TIMEOUT_MS = 15_000;

export interface RequestOptions extends Omit<RequestInit, "body" | "headers"> {
  body?: unknown;
  headers?: HeadersInit;
  token?: string | null;
}

export interface ApiClientOptions {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  getToken?: () => string | null;
}

function normaliseBaseUrl(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;
  private readonly getToken: () => string | null;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = normaliseBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.fetchImpl = options.fetchImpl ?? globalThis.fetch.bind(globalThis);
    
    // Default token retriever (to be provided via dependency injection later by F2 AuthProvider)
    this.getToken = options.getToken ?? (() => null);
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);
    const headers = new Headers(options.headers);
    
    headers.set("Accept", "application/json");
    if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    const token = options.token !== undefined ? options.token : this.getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    const url = `${this.baseUrl}${normalizedPath}`;

    try {
      const response = await this.fetchImpl(url, {
        ...options,
        headers,
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      const requestId = response.headers.get("X-Request-ID");
      const text = await response.text();
      const payload = text ? safelyParseJson(text) : undefined;

      if (!response.ok) {
        if (isBackendError(payload)) {
          throw new ApiClientError(
            payload.error.message,
            response.status,
            payload.error.code,
            payload.error.details,
            payload.request_id || requestId
          );
        }
        
        throw new ApiClientError(
          "The service could not complete this request.",
          response.status,
          "HTTP_ERROR",
          undefined,
          requestId
        );
      }

      return payload as T;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiClientError("The request timed out.", 0, "TIMEOUT", undefined, null);
      }
      throw new ApiClientError("The service could not be reached.", 0, "NETWORK_ERROR", undefined, null);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  get<T>(path: string, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  post<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, body, method: "POST" });
  }

  patch<T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, body, method: "PATCH" });
  }

  delete<T>(path: string, options?: Omit<RequestOptions, "body" | "method">): Promise<T> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }
}

// Global default singleton instance
export const apiClient = new ApiClient();
