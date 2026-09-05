// @vitest-environment node
import { describe, expect, it } from "vitest";
import { ApiClient } from "@/lib/api";

const live = process.env.RUN_LIVE_API_TEST === "1" ? it : it.skip;

describe("live API client smoke", () => {
  live("reaches the unauthenticated backend health endpoint", async () => {
    const client = new ApiClient({ baseUrl: process.env.NEXT_PUBLIC_API_URL, timeoutMs: 5_000 });
    await expect(client.health()).resolves.toEqual({ status: "ok", service: "sif-backend" });
  });
});
