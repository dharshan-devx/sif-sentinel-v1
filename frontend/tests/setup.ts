import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

export const routerMock = { replace: vi.fn(), push: vi.fn(), refresh: vi.fn(), back: vi.fn(), prefetch: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));
