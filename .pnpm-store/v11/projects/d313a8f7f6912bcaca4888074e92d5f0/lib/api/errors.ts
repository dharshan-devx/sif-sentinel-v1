import type { BackendErrorBody } from "@/types/api";

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

export function isBackendError(value: unknown): value is BackendErrorBody {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<BackendErrorBody>;
  return (
    candidate.success === false &&
    typeof candidate.error?.code === "string" &&
    typeof candidate.error?.message === "string"
  );
}

export function safelyParseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}
