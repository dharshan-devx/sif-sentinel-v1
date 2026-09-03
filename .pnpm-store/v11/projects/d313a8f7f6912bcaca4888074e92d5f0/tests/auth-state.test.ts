import { beforeEach, describe, expect, it } from "vitest";
import { tokenStore } from "@/lib/auth/token-store";

describe("session token store", () => {
  beforeEach(() => { window.sessionStorage.clear(); });
  it("stores and clears only the bearer token", () => { tokenStore.set("test-token"); expect(tokenStore.get()).toBe("test-token"); tokenStore.clear(); expect(tokenStore.get()).toBeNull(); });
});
