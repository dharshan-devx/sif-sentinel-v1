# SIF SENTINEL repository audit — 2026-09-05

## Scope and repository map

- `backend/` is the FastAPI modular-monolith runtime: REST routes, SQLAlchemy
  models, Alembic migrations, deterministic NLP/risk/precursor/intervention
  services, optional LLM reviewer assistance, and pytest tests.
- `ml/` is offline research/training; `data/` holds raw/processed datasets;
  `artifacts/` holds model exports and evaluation outputs.
- `scripts/` contains database/demo helpers. `docker-compose.yml` provisions
  PostgreSQL plus the backend. `frontend/` exists but is empty.
- The browser boundary is REST only. The deterministic pipeline remains
  authoritative; LLM output is metadata-only reviewer assistance.

## Findings and completed repairs

### Critical — resolved

1. `backend/app/ml/inference/predictor.py` contained committed Git conflict
   markers and could not be imported. `artifacts/models/metadata.json` had the
   same damage and was invalid JSON. The conflict was resolved using the newer
   multi-artifact predictor branch and matching v2 metadata; compilation,
   OpenAPI generation, and classifier tests now execute.
2. The configured v2 runtime selected a classifier expecting 4,332 features
   but a root vectorizer exposing 131. `SIFPredictor` now loads the paired
   `artifacts/models/v2` classifier/vectorizer set. Root legacy artifacts are
   documented as non-default provenance files.

### High — resolved

1. `PATCH /reports` accepted `status`, allowing writers to bypass analysis and
   review lifecycle state. `ReportUpdate` now forbids unknown fields and
   `ReportService` accepts edits only while a report is `NEW`.
2. Persisted analysis did not lock or guard report state, so repeated or
   concurrent requests could create duplicate analyses. `AnalysisService` now
   locks the report where supported and permits analysis only from `NEW`;
   retries receive `409 REPORT_ALREADY_ANALYZED`.
3. `scripts/database/create_test_db.py` embedded a database credential and
   used an undeclared driver. It now requires `TEST_ADMIN_DATABASE_URL`,
   validates a disposable target suffix, and uses declared `psycopg`.
4. Docker built from `backend/`, so it could not include top-level runtime
   artifacts. Compose now builds from the repository root and the Dockerfile
   copies artifacts to the path used by the predictor.

### Medium — resolved

1. Fuzzy matching returned no match when RapidFuzz was unavailable even though
   the test/runtime dependency set can omit it. A bounded standard-library
   similarity fallback preserves the conservative threshold.
2. `backend/.env.example` used obsolete risk variable names and thresholds.
   It now lists the actual settings keys and safe LLM-disabled defaults.
3. The frontend architecture and contract claimed a present UI, stale OpenAPI
   counts (49/44), and direct PATCH lifecycle control. They now state the empty
   frontend status, 66 operations/60 paths, and the enforced lifecycle.

### Informational / intentionally unresolved

- `v4b_transformer` contains tokenizer/configuration/evaluation metadata but
  not trained weights. It is marked `runtime_available: false`; selecting it
  fails safely with a controlled runtime error. Its inference tests skip until
  versioned weights and optional PyTorch/Transformers dependencies are supplied.
- The initial Alembic revision calls current SQLAlchemy metadata rather than a
  static historical schema snapshot. Fresh SQLite migration works, but this
  remains migration-maintenance risk and should be replaced by a generated,
  reviewed baseline migration before a production schema evolution.
- Docker is not installed on this host. The configured local PostgreSQL database
  was upgraded to Alembic head, but a safe `TEST_ADMIN_DATABASE_URL` was not
  supplied, so a fresh isolated PostgreSQL rebuild and Docker image execution
  were not performed.

## Verification

- Fresh SQLite Alembic chain: upgraded from empty database to
  `20260904_0005 (head)` successfully. The configured local PostgreSQL database
  was also upgraded and reports that same head revision.
- Generated OpenAPI: 66 operations across 60 paths.
- Complete pytest inventory: 337 tests, 333 passed, 4 skipped, 0 failed, and
  0 errors (5 third-party/runtime warnings per bounded group). The four skips
  are v4b inference checks gated on absent transformer weights.
- The project linter still reports 112 pre-existing style/import violations
  across later-phase files and tests; no bulk formatting was performed in this
  repair pass.

## Implementation plan executed

1. Restore importable runtime/model metadata.
2. Enforce report lifecycle and duplicate-analysis guards with regression tests.
3. Pair runtime artifacts and label unavailable research exports honestly.
4. Repair security-sensitive script and Docker artifact path.
5. Verify migrations/tests/OpenAPI and reconcile documentation without
   implementing frontend F1.

## Final stabilization gate

- Ruff was reduced from 112 findings to zero without suppressing rule groups.
- Bounded complete test execution: 337 tests, 333 passed, 4 expected
  weight-dependent transformer skips, 0 failures, and 0 errors.
- A fresh migrated SQLite database passed a real HTTP smoke flow for health,
  auth, RBAC, site/report creation, analysis, review, intervention, precursor,
  and risk routes. It also verified unauthenticated access is rejected.
- The configured PostgreSQL database reports Alembic head. Fresh isolated
  PostgreSQL is environment-unverified because `TEST_ADMIN_DATABASE_URL` is
  unavailable. Docker runtime is also environment-blocked because Docker is not
  installed; Compose paths and environment references were checked statically.
