import { describe, expect, it } from "vitest";
import { hasCapability } from "@/lib/constants/roles";

describe("role capability matrix", () => {
  it("keeps viewer navigation read-only", () => { expect(hasCapability("VIEWER", "report:write")).toBe(false); expect(hasCapability("VIEWER", "review:decide")).toBe(false); });
  it("allows only reviewer-capable roles to decide reviews", () => { expect(hasCapability("REVIEWER", "review:decide")).toBe(true); expect(hasCapability("HSE_ANALYST", "review:decide")).toBe(false); });
});
