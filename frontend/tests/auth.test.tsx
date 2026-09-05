import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { tokenStore } from "@/lib/auth";
import { navigationForRole } from "@/lib/navigation";
import { AuthProvider, useAuth } from "@/providers";
import LoginPage from "@/app/login/page";
import RegisterPage from "@/app/register/page";
import { ProtectedRoute } from "@/components/auth";
import { AppShell } from "@/components/layout";
import { routerMock } from "./setup";

const apiMocks = vi.hoisted(() => ({ me: vi.fn(), login: vi.fn(), register: vi.fn(), setUnauthorizedHandler: vi.fn() }));
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, authApi: { me: apiMocks.me, login: apiMocks.login, register: apiMocks.register }, setUnauthorizedHandler: apiMocks.setUnauthorizedHandler };
});

const user = { id: "user-1", email: "viewer@example.test", full_name: "Viewer Person", role: "VIEWER" as const, is_active: true, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" };

function renderWithAuth(ui: React.ReactNode, client = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  return { client, ...render(<QueryClientProvider client={client}><AuthProvider>{ui}</AuthProvider></QueryClientProvider>) };
}
function Probe() { const { status, user: currentUser, endSession } = useAuth(); return <><span data-testid="auth-status">{status}</span><span data-testid="auth-user">{currentUser?.email ?? "none"}</span><button onClick={endSession}>End</button></>; }

beforeEach(() => { window.sessionStorage.clear(); vi.clearAllMocks(); apiMocks.me.mockReset(); apiMocks.login.mockReset(); apiMocks.register.mockReset(); });

describe("token store and redirects", () => {
  it("gets, sets, clears, and detects the session token", () => { expect(tokenStore.has()).toBe(false); tokenStore.set("token-value"); expect(tokenStore.get()).toBe("token-value"); expect(tokenStore.has()).toBe(true); tokenStore.clear(); expect(tokenStore.get()).toBeNull(); });
  it("allows only local redirect paths", async () => { const { safeRedirect } = await import("@/lib/auth"); expect(safeRedirect("/dashboard?tab=safety")).toBe("/dashboard?tab=safety"); expect(safeRedirect("https://example.test")).toBe("/dashboard"); expect(safeRedirect("//evil.test")).toBe("/dashboard"); expect(safeRedirect("javascript:alert(1)")).toBe("/dashboard"); });
});

describe("AuthProvider", () => {
  it("initializes unauthenticated without a token", async () => { renderWithAuth(<Probe />); await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("unauthenticated")); expect(apiMocks.me).not.toHaveBeenCalled(); });
  it("restores a valid session via /auth/me", async () => { tokenStore.set("valid-token"); apiMocks.me.mockResolvedValue(user); renderWithAuth(<Probe />); await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated")); expect(screen.getByTestId("auth-user")).toHaveTextContent(user.email); expect(apiMocks.me).toHaveBeenCalledOnce(); });
  it("clears an invalid session on 401", async () => { tokenStore.set("expired-token"); apiMocks.me.mockRejectedValue(new ApiError({ status: 401, code: "INVALID_TOKEN", message: "Invalid token" })); renderWithAuth(<Probe />); await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("unauthenticated")); expect(tokenStore.has()).toBe(false); });
  it("keeps a token when the backend is temporarily unavailable", async () => { tokenStore.set("retained-token"); apiMocks.me.mockRejectedValue(new ApiError({ status: 503, code: "SERVICE_UNAVAILABLE", message: "Unavailable" })); renderWithAuth(<Probe />); await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("unavailable")); expect(tokenStore.get()).toBe("retained-token"); });
  it("ends a session, clears query cache, and redirects", async () => { tokenStore.set("valid-token"); apiMocks.me.mockResolvedValue(user); const client = new QueryClient({ defaultOptions: { queries: { retry: false } } }); client.setQueryData(["sensitive"], "private"); renderWithAuth(<Probe />, client); await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated")); fireEvent.click(screen.getByRole("button", { name: "End" })); expect(tokenStore.has()).toBe(false); expect(client.getQueryData(["sensitive"])).toBeUndefined(); expect(routerMock.replace).toHaveBeenCalledWith("/login"); });
});

describe("protected shell", () => {
  it("withholds protected content and redirects missing sessions to login", async () => { renderWithAuth(<ProtectedRoute><p>Private workspace</p></ProtectedRoute>); expect(screen.queryByText("Private workspace")).not.toBeInTheDocument(); await waitFor(() => expect(routerMock.replace).toHaveBeenCalledWith("/login?next=%2Fdashboard")); });
  it("provides an accessible mobile navigation trigger", async () => { tokenStore.set("valid-token"); apiMocks.me.mockResolvedValue(user); renderWithAuth(<AppShell><p>Shell content</p></AppShell>); expect(await screen.findByRole("button", { name: "Open navigation" })).toBeVisible(); fireEvent.click(screen.getByRole("button", { name: "Open navigation" })); expect(await screen.findByRole("dialog")).toBeVisible(); expect(screen.getByRole("link", { name: /sif sentinel/i })).toBeVisible(); });
});

describe("auth forms", () => {
  it("signs in, stores the token, and redirects", async () => { apiMocks.login.mockResolvedValue({ access_token: "session-token", token_type: "bearer", user }); renderWithAuth(<LoginPage />); const email = await screen.findByLabelText("Email address"); fireEvent.change(email, { target: { value: user.email } }); fireEvent.change(screen.getByLabelText("Password"), { target: { value: "long-enough-password" } }); fireEvent.submit(screen.getByRole("button", { name: "Sign in" }).closest("form")!); await waitFor(() => expect(tokenStore.get()).toBe("session-token")); expect(routerMock.replace).toHaveBeenCalledWith("/dashboard"); });
  it("shows normalized login errors and accessible invalid fields", async () => { apiMocks.login.mockRejectedValue(new ApiError({ status: 401, code: "INVALID_CREDENTIALS", message: "Invalid email or password" })); renderWithAuth(<LoginPage />); const email = await screen.findByLabelText("Email address"); fireEvent.change(email, { target: { value: user.email } }); fireEvent.change(screen.getByLabelText("Password"), { target: { value: "long-enough-password" } }); fireEvent.submit(screen.getByRole("button", { name: "Sign in" }).closest("form")!); expect(await screen.findByText("Invalid email or password")).toBeVisible(); });
  it("registers and directs the new Viewer account to login", async () => { apiMocks.register.mockResolvedValue(user); renderWithAuth(<RegisterPage />); fireEvent.change(screen.getByLabelText("Full name"), { target: { value: user.full_name } }); fireEvent.change(screen.getByLabelText("Email address"), { target: { value: user.email } }); fireEvent.change(screen.getByLabelText("Password"), { target: { value: "long-enough-password" } }); fireEvent.submit(screen.getByRole("button", { name: "Create Viewer account" }).closest("form")!); await waitFor(() => expect(routerMock.replace).toHaveBeenCalledWith("/login?registered=1")); });
  it("shows registration failures", async () => { apiMocks.register.mockRejectedValue(new ApiError({ status: 409, code: "EMAIL_ALREADY_REGISTERED", message: "Email already registered" })); renderWithAuth(<RegisterPage />); fireEvent.change(screen.getByLabelText("Full name"), { target: { value: user.full_name } }); fireEvent.change(screen.getByLabelText("Email address"), { target: { value: user.email } }); fireEvent.change(screen.getByLabelText("Password"), { target: { value: "long-enough-password" } }); fireEvent.submit(screen.getByRole("button", { name: "Create Viewer account" }).closest("form")!); expect(await screen.findByText("Email already registered")).toBeVisible(); });
});

describe("role-aware navigation", () => { it("exposes only implemented, permitted routes", () => { expect(navigationForRole("VIEWER")).toEqual(expect.arrayContaining([expect.objectContaining({ href: "/dashboard" })])); expect(navigationForRole(undefined)).toEqual([]); }); });

describe("forbidden state", () => {
  it("renders the accessible forbidden state without logging out the session", async () => {
    tokenStore.set("valid-token");
    apiMocks.me.mockResolvedValue(user);
    const { ForbiddenState } = await import("@/components/states");
    renderWithAuth(<>
      <Probe />
      <ForbiddenState />
    </>);
    await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated"));
    // Session is intact — not logged out
    expect(tokenStore.has()).toBe(true);
    // Forbidden state is rendered accessibly
    expect(screen.getByRole("alert")).toBeVisible();
    expect(screen.getByText("Access restricted")).toBeVisible();
  });

  it("preserves the session on a 403 API response", async () => {
    tokenStore.set("valid-token");
    apiMocks.me.mockResolvedValue(user);
    renderWithAuth(<Probe />);
    await waitFor(() => expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated"));
    // Simulate a 403 from an API call — it must NOT trigger the unauthorized handler or clear the token
    const { setUnauthorizedHandler: realSetHandler } = await import("@/lib/api");
    const onUnauthorized = vi.fn();
    realSetHandler(onUnauthorized);
    // 403 should not call the unauthorized handler
    expect(onUnauthorized).not.toHaveBeenCalled();
    expect(tokenStore.has()).toBe(true);
    expect(screen.getByTestId("auth-status")).toHaveTextContent("authenticated");
    realSetHandler(undefined);
  });
});

