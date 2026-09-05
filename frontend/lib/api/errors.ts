import type { ApiErrorPayload } from "@/types/api";

export type ApiErrorCode =
  | "AUTHENTICATION_REQUIRED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "VALIDATION_ERROR"
  | "SERVICE_UNAVAILABLE"
  | "REQUEST_TIMEOUT"
  | "NETWORK_ERROR"
  | "INTERNAL_ERROR"
  | string;

export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor({ status, code, message, details, requestId }: {
    status: number;
    code: ApiErrorCode;
    message: string;
    details?: unknown;
    requestId?: string | null;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId ?? null;
  }
}

const safeMessageByStatus: Record<number, string> = {
  401: "Your session is not available. Please sign in again.",
  403: "You do not have access to this resource.",
  404: "The requested resource was not found.",
  409: "This item changed before your request could be completed.",
  422: "Please review the highlighted information and try again.",
  500: "The service could not complete this request.",
  503: "The service is temporarily unavailable. Please try again.",
};

export function normalizeApiError(
  status: number,
  payload: ApiErrorPayload | undefined,
  requestId: string | null,
): ApiError {
  const isControlled = Boolean(payload?.error?.message) && status < 500;
  return new ApiError({
    status,
    code: payload?.error?.code ?? (status >= 500 ? "INTERNAL_ERROR" : "REQUEST_FAILED"),
    message: isControlled ? payload!.error!.message! : (safeMessageByStatus[status] ?? "The request could not be completed."),
    details: status >= 500 ? undefined : payload?.error?.details,
    requestId: payload?.request_id ?? requestId,
  });
}
