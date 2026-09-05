# SIF SENTINEL frontend architecture

## Current status

The `frontend/` directory is intentionally empty. No Next.js, Vite, React,
TypeScript, package-manager, or browser runtime is currently shipped. Frontend
F1 must start from the backend contract rather than from deleted historical UI
artifacts.

## Required boundary for F1

```text
Browser -> typed REST client -> FastAPI /api/v1 -> PostgreSQL
```

The browser must never receive database credentials or query PostgreSQL
directly. The generated FastAPI OpenAPI document and
[backend/frontend contract](BACKEND_FRONTEND_CONTRACT.md) are the sources of
truth. Deterministic backend results are authoritative for structured evidence,
SIF, LSR, barriers, precursor state, risk, review routing, and intervention
recommendations. Optional LLM output is reviewer assistance only.

Historical Phase 5 documents that refer to files below `frontend/src/` describe
work that is no longer present and must not be used as an implementation-status
claim.
