import { render, screen } from "@testing-library/react";
import { Providers } from "@/providers";
import Home from "@/app/page";

// AuthProvider calls authApi.me when a token exists; ensure no real HTTP occurs in tests.
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    authApi: { me: vi.fn().mockResolvedValue(null), login: vi.fn(), register: vi.fn() },
    setUnauthorizedHandler: vi.fn(),
  };
});

describe("root page", () => {
  it("establishes the product purpose without fake operational data", () => {
    render(<Providers><Home /></Providers>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Make safety signals easier to see");
    // Auth-aware header: shows Sign in when unauthenticated/loading
    expect(screen.getByRole("link", { name: /sign in/i })).toBeVisible();
    expect(screen.queryByText(/incidents today/i)).not.toBeInTheDocument();
  });
});
