import { describe, expect, it } from "vitest";
import { safeRedirectPath } from "@/components/auth/auth-form";

describe("safe post-login redirects", () => {
  it("allows only local application paths", () => { expect(safeRedirectPath("/reports")).toBe("/reports"); expect(safeRedirectPath("https://unsafe.example")).toBe("/dashboard"); expect(safeRedirectPath("//unsafe.example")).toBe("/dashboard"); });
});
