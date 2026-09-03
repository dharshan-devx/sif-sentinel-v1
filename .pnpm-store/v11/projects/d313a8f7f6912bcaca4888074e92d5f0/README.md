# SIF SENTINEL frontend

The SIF Sentinel frontend is a Next.js + TypeScript application for workplace safety decision support. It communicates with the FastAPI backend exclusively through its REST API. It never connects to PostgreSQL, imports Python modules, or contains backend secrets.

## Foundation architecture

```text
Browser -> Next.js routes/components -> typed API modules -> FastAPI /api/v1 -> PostgreSQL
```

- `app/`: route composition, global boundaries, and intentionally minimal F1 placeholder pages.
- `components/ui/`: accessible, reusable primitives; `components/layout/` is the responsive app shell and route guard.
- `lib/api/`: the only HTTP boundary. Pages and UI components must not call `fetch()` directly.
- `lib/auth/`: session token abstraction. `lib/constants/roles.ts` defines client navigation capabilities; the backend is always authoritative.
- `providers/`: TanStack Query and authentication context.
- `types/api.ts`: manually maintained types aligned to the current FastAPI OpenAPI/schema contract.
- `tests/`: API client, auth state, error-normalisation/RBAC, and UI smoke coverage.

The backend's OpenAPI has several dynamic dictionary responses (`/models` and `/rules`) and no formal frontend client-generation step. For F1 we chose a small manual type layer derived from [the backend/frontend contract](../docs/architecture/BACKEND_FRONTEND_CONTRACT.md). This is simpler and safer than introducing code generation prematurely. Refresh the affected types whenever the backend OpenAPI changes.

## Local setup

Use the bundled `pnpm` rather than the currently broken system `npm` shim:

```powershell
cd frontend
pnpm install
Copy-Item .env.example .env.local
pnpm dev
```

Set only this public browser value:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Do not place `JWT_SECRET_KEY`, `LLM_API_KEY`, database credentials, or any server secret in `NEXT_PUBLIC_*` variables. If the UI is hosted at a different origin, add that origin to the backend `CORS_ORIGINS` configuration.

## Authentication

The backend returns an access token from `POST /auth/login` and has no refresh, logout, or revocation endpoint. The frontend stores only that bearer token in `sessionStorage`, so it is cleared when the browser session closes. This is a deliberate trade-off: it reduces persistence but cannot eliminate XSS risk. The token store is isolated so the strategy can change when the backend offers secure cookie or refresh-token support. “End session” only clears local state; it does not revoke a backend token.

On a `401`, the auth provider clears local state and safely redirects to login. On `403`, it retains the session and shows access denial. The app invalidates TanStack Query keys after future mutations because the API has no push events.

### F2 authentication behavior

- Initialisation is explicitly `loading`, `authenticated`, `unauthenticated`, or `unavailable`. A missing token becomes unauthenticated without an API call; a token is validated through `GET /auth/me`.
- Only an explicit backend `401` clears a stored token. Temporary network or `5xx` initialisation failures show a controlled retry state without discarding a potentially valid session.
- Login stores the returned bearer token and backend-returned user, then safely navigates to the requested local path or `/dashboard`.
- Registration uses `POST /auth/register` and returns the backend-created `VIEWER`; it then directs the person to sign in. The UI never claims elevated access.
- “End session” clears local token/auth state and the TanStack Query cache. It makes no backend logout/revocation request because none exists.
- Navigation is filtered by role only as a UX aid. Every backend request remains subject to FastAPI RBAC.

## Commands

```powershell
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## Contribution rules

- Keep all backend calls in `lib/api/` and add/update corresponding types.
- Use TanStack Query for server state; do not add a second global cache.
- Reuse UI primitives and include semantic labels, keyboard behavior, focus treatment, loading, empty, and error states.
- Preserve safety language: “safety signal”, “risk priority”, “evidence”, “deterministic recommendation”, and “requires human review”.
- Render any future LLM `reviewer_summary` separately from deterministic safety evidence. It is reviewer assistance, never an authoritative result.
- Do not implement an API the backend does not expose.
