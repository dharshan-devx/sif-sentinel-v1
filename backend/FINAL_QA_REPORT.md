# Final QA report — Phase L

## Executive summary

Phase L fixed verified release defects without changing the authority chain.
Fresh Alembic migrations, startup, deterministic workflow checks, and full
SQLite/PostgreSQL suites passed. The baseline release mode is `LLM_ENABLED=false`.

## Repository audit and defects fixed

Baseline was `1326353`. The unrelated deletion of `LLM_PROVIDER.md` was already
present and is excluded from Phase L. The audit fixed:

- an absent `precursor_patterns.risk_level` column being indexed on fresh migration;
- historical migrations reapplying current metadata fields;
- retry analysis duplicating report precursor candidates; and
- PostgreSQL review-decision races without row locking.

## Migration and database results

`alembic upgrade head` ran from an empty temporary SQLite database and a newly
recreated public schema in isolated PostgreSQL `sif_test_db`. Both reached
`20260903_0004` and contain `intervention_recommendations`. Application startup
and readiness were verified against the migrated SQLite schema. No development
or production data was accessed.

## Startup, API, and security

Health, readiness, and `/openapi.json` returned HTTP 200 with LLM disabled and
with LLM enabled but no provider key. OpenAPI exposes health, auth, reports,
reviews, precursors, risk, and interventions. JWT/RBAC tests cover missing and
malformed tokens, 401/403 responses, controlled validation errors, and prompt
injection as untrusted report data. CORS uses configured origins with credentials.

## Safety, review, and audit

The suite covers structured evidence, SIF/LSR mappings, precursor recurrence,
exact risk authority, intervention provenance/idempotency, review transitions,
and audit records. Re-analysis now replaces current precursor candidates before
rebuilding patterns. Normal and intervention review decisions use row locking
where supported. The release smoke test exercises report → analysis →
intervention → HSE acceptance → audit.

## LLM and model reproducibility

Provider tests cover disabled, missing/invalid provider, timeout, malformed,
adversarial, and mocked-success paths. Authority-invariant tests preserve all
deterministic outputs. No real Gemini E2E ran because no validated key was
available. The v1 model now records its runtime and newline-normalized hash of
the versioned 640-record synthetic source; tests enforce both values.

## Demo and documentation

Seed data is explicitly synthetic. `DEMO_CLAIMS.md` records bounded claims and
limitations. README and model documentation now describe the current authority
chain, intervention API, LLM boundary, test database setup, and model provenance.

## Tests and warnings

The final SQLite suite passed **158 tests in 33.15 seconds**. The final
PostgreSQL suite passed **158 tests in 102.62 seconds**. Each emitted five
non-blocking third-party deprecations from FastAPI/Starlette TestClient,
Windows asyncio selector policy, and `google-genai` typing aliases. The prior
scikit-learn artifact-version warning is eliminated.

## Remaining limitations

All model data is synthetic; no real Gemini key was validated; no frontend or
WebSocket implementation exists; and concurrency was smoke-hardened rather than
load tested.

## Final scorecard

| Area | Status |
| --- | --- |
| Correctness | PASS |
| Reliability | PASS WITH NOTES |
| Security | PASS WITH NOTES |
| Authentication | PASS |
| Authorization | PASS |
| Data Integrity | PASS |
| Migration Integrity | PASS |
| NLP | PASS |
| SIF/LSR | PASS |
| Precursor | PASS |
| Risk Engine | PASS |
| Intervention | PASS |
| LLM Isolation | PASS |
| API Stability | PASS |
| PostgreSQL | PASS |
| SQLite | PASS |
| Demo Reliability | PASS WITH NOTES |
| Documentation | PASS |
| Repository Hygiene | PASS WITH NOTES |

## Release recommendation

**PASS WITH NOTES — ready for the deterministic hackathon demo.** Use
`LLM_ENABLED=false` unless a separately validated provider key is available.
