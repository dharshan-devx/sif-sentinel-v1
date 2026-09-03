const TOKEN_KEY = "sif-sentinel.access-token";

function browserStorage(): Storage | null {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

export const tokenStore = {
  get(): string | null { return browserStorage()?.getItem(TOKEN_KEY) ?? null; },
  set(token: string): void { browserStorage()?.setItem(TOKEN_KEY, token); },
  clear(): void { browserStorage()?.removeItem(TOKEN_KEY); },
  has(): boolean { return this.get() !== null; },
};
