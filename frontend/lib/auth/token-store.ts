const TOKEN_KEY = "sif-sentinel.access-token";

function storage(): Storage | null {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

/** The sole browser-token boundary. Tokens are never persisted beyond this tab session. */
export const tokenStore = {
  get(): string | null { return storage()?.getItem(TOKEN_KEY) ?? null; },
  set(token: string): void { storage()?.setItem(TOKEN_KEY, token); },
  clear(): void { storage()?.removeItem(TOKEN_KEY); },
  has(): boolean { return Boolean(this.get()); },
};
