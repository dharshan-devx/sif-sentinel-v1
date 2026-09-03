# SIF SENTINEL frontend architecture

## Runtime boundary

```text
Browser
  ↓
Next.js App Router (layout, route guard, accessible UI components)
  ↓
Typed API client + TanStack Query
  ↓
FastAPI REST API (/api/v1)
  ↓
PostgreSQL
```

The browser has no PostgreSQL credentials and never connects to the database. `frontend/lib/api/` is the only place that makes HTTP requests. Its one `ApiClient` sets the base URL, bearer token, JSON/Accept headers, timeout, normalised errors, and request-ID capture. Resource modules are typed adapters over that client rather than additional clients.

## Source of truth and safety boundary

The backend OpenAPI and [backend/frontend contract](BACKEND_FRONTEND_CONTRACT.md) are the source of truth. Local role awareness improves navigation but does not authorise an action; FastAPI RBAC remains final.

Structured evidence, SIF level, Life-Saving Rule, barrier status, precursor state, risk score/priority, review routing, and intervention source evidence are deterministic backend results. An optional LLM can supply only `reviewer_summary` metadata. Future UI must display it as “Reviewer assistance” and visually separate it from authoritative evidence and recommendations.

## State and errors

TanStack Query is the single server-state mechanism. Future mutations must invalidate/refetch their related query keys because the REST API supplies no WebSocket, SSE, cache validators, or background notification channel.

Controlled backend errors preserve status, machine code, safe message, details, and request ID. `401` clears local token state and redirects safely to login; `403` retains accessible data and reports access denied; `409` requires a refetch rather than retrying a final decision; and `422` is available for field-level display. Raw exception objects are never shown.

## Authentication

The session bearer token is stored in `sessionStorage` behind a small token store abstraction. This matches the current backend's lack of refresh, logout, and revocation endpoints. It is not a claim of server-side revocation; the UI’s “End session” is a local clear only.

## Team boundaries

- `components/ui`: shared primitives and states.
- `components/<domain>`: future domain views, once their phase begins.
- `app`: page composition only.
- `lib/api`: HTTP adapters and request types.
- `types`: backend-aligned contract types.
- `providers` / `hooks`: cross-cutting client state and access helpers.

F1 intentionally provides shell and route placeholders only. Dashboard widgets, report submission/analysis, review decisions, recommendations, precursor graphs, and risk charts begin in later phases.
