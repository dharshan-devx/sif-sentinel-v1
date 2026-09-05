const API_VERSION_PATH = "/api/v1";

/** Returns a normalized API root without ever appending the API prefix twice. */
export function getApiBaseUrl(value = process.env.NEXT_PUBLIC_API_URL): string {
  const configuredUrl = value?.trim();
  if (!configuredUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  }

  const normalized = configuredUrl.replace(/\/+$/, "");
  return normalized.endsWith(API_VERSION_PATH)
    ? normalized
    : `${normalized}${API_VERSION_PATH}`;
}
