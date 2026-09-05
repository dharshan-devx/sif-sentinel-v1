const DASHBOARD_PATH = "/dashboard";

/** Allows only a same-origin application path; protects auth flows from open redirects. */
export function safeRedirect(target: string | null | undefined, fallback = DASHBOARD_PATH): string {
  if (!target || !target.startsWith("/") || target.startsWith("//") || target.includes("\\") || /[\u0000-\u001F]/.test(target)) return fallback;
  try {
    const parsed = new URL(target, "https://sif-sentinel.invalid");
    if (parsed.origin !== "https://sif-sentinel.invalid" || !parsed.pathname.startsWith("/")) return fallback;
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch { return fallback; }
}

export function loginPath(next?: string | null): string {
  const destination = safeRedirect(next);
  return `/login?next=${encodeURIComponent(destination)}`;
}
