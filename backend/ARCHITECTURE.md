# SIF Sentinel Backend — Architecture Guide

> Practical reference for the development team. Keep this document up to date
> when the structure of the backend changes meaningfully.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application factory
│   ├── api/
│   │   ├── deps.py              # Centralized DI: DBSession, CurrentUser, require_roles()
│   │   ├── router.py            # Top-level API router (prefix /api/v1)
│   │   └── routes/              # One file per resource group (thin handlers only)
│   │       ├── analysis.py
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── health.py
│   │       ├── models.py
│   │       ├── precursors.py
│   │       ├── reports.py
│   │       ├── reviews.py
│   │       ├── risk.py
│   │       ├── rules.py
│   │       ├── sites.py
│   │       └── users.py
│   ├── core/
│   │   ├── config.py            # Pydantic Settings — ALL configuration here
│   │   ├── constants.py         # ALL shared enums (UserRole, ReportStatus, …)
│   │   ├── exceptions.py        # AppError, NotFoundError
│   │   ├── logging.py           # structlog configuration
│   │   ├── security.py          # password hashing, JWT creation
│   │   └── validators.py        # validate_report_text() — shared boundary validator
│   ├── db/
│   │   ├── base.py              # SQLAlchemy declarative Base
│   │   ├── init_db.py           # create_tables() — used by scripts/tests
│   │   └── session.py           # engine, SessionLocal, get_db()
│   ├── middleware/
│   │   ├── error_handler.py     # register_error_handlers() — centralized error responses
│   │   └── request_id.py        # RequestIDMiddleware — X-Request-ID + security headers
│   ├── models/                  # SQLAlchemy ORM models (persistence only)
│   │   ├── __init__.py          # re-exports all models (required for Alembic auto-detect)
│   │   ├── mixins.py            # UUIDTimestampMixin (id, created_at, updated_at)
│   │   ├── audit_log.py
│   │   ├── life_saving_rule.py
│   │   ├── model_prediction.py
│   │   ├── precursor_pattern.py
│   │   ├── report.py
│   │   ├── report_analysis.py
│   │   ├── review.py
│   │   ├── site.py
│   │   └── user.py
│   ├── schemas/                 # Pydantic I/O schemas (API boundary only)
│   │   ├── common.py            # ORMModel, Page, Message, IDResponse
│   │   ├── analysis.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── precursor.py
│   │   ├── report.py
│   │   ├── review.py
│   │   ├── risk.py
│   │   ├── site.py
│   │   └── user.py
│   ├── repositories/
│   │   └── report_repository.py # ReportRepository — DB queries for Report model
│   ├── services/                # Business logic — one service per responsibility
│   │   ├── analysis/
│   │   │   └── analysis_service.py  # Run & persist the NLP analysis pipeline
│   │   ├── nlp/                 # Pure NLP pipeline (no DB dependency)
│   │   │   ├── analysis_pipeline.py # analyze_text() — top-level pipeline entry point
│   │   │   ├── sif_classifier.py
│   │   │   ├── entity_extractor.py
│   │   │   ├── evidence_extractor.py
│   │   │   ├── confidence.py
│   │   │   ├── preprocessing.py
│   │   │   ├── model_registry.py
│   │   │   └── llm.py           # LLM extension point (disabled by default)
│   │   ├── precursor_engine/
│   │   │   ├── precursor_service.py  # PrecursorService — pattern rebuild + queries
│   │   │   ├── pattern_aggregator.py
│   │   │   ├── pattern_builder.py
│   │   │   └── trend_analyzer.py
│   │   ├── risk_engine/
│   │   │   ├── risk_service.py   # RiskService — site/activity/hazard/barrier risk
│   │   │   ├── scoring.py
│   │   │   └── ranking.py
│   │   ├── analytics_service.py  # AnalyticsService — dashboard aggregations
│   │   ├── audit_service.py      # record_audit() — single shared audit helper
│   │   ├── auth_service.py       # AuthService — register, authenticate
│   │   ├── model_service.py      # Model metadata + feedback aggregation
│   │   ├── report_service.py     # ReportService — report CRUD + list
│   │   ├── review_service.py     # ReviewService — review queue + decision workflow
│   │   ├── rules_service.py      # RulesService — LSR list, get, analytics
│   │   └── site_service.py       # SiteService — site CRUD
│   ├── knowledge/               # Bundled knowledge base (JSON + loader)
│   │   ├── life_saving_rules.json
│   │   ├── activities.json
│   │   ├── hazards.json
│   │   ├── barriers.json
│   │   ├── lsr_mapper.py
│   │   └── taxonomy.py
│   └── ml/                      # ML model artifacts and inference
│       ├── inference/
│       └── artifacts/
├── alembic/                     # Database migrations
├── tests/                       # pytest test suite
│   ├── conftest.py
│   ├── test_analysis.py
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_precursor_analytics.py
│   ├── test_reports.py
│   ├── test_review_hardening.py
│   ├── test_review_workflow.py
│   └── test_validation.py
├── scripts/                     # Seed and utility scripts
├── .env.example                 # Environment variable template
├── pyproject.toml               # Project metadata and tool config
└── Dockerfile
```

---

## Request Flow

```
HTTP Request
    │
    ▼
RequestIDMiddleware          ← Adds X-Request-ID, security headers, request logging
    │
    ▼
CORS Middleware
    │
    ▼
FastAPI Route Handler        ← Thin: parse input, call DI deps, call service, return response
    │
    ├── app.api.deps         ← DBSession (AsyncSession), CurrentUser, require_roles()
    │
    ▼
Service Layer                ← Business logic, transaction boundaries, audit logging
    │
    ├── Repository           ← Complex DB queries (currently only ReportRepository)
    │
    ▼
SQLAlchemy AsyncSession      ← ORM / raw SQL via engine
    │
    ▼
PostgreSQL (prod) / SQLite (dev/test)
```

**Error path:** Any `AppError` raised in any layer propagates up to the registered
`error_handler.py` exception handler, which returns a consistent JSON error envelope.

---

## Service Responsibilities

| Service | Responsibility |
|---------|---------------|
| `AuthService` | User registration, credential authentication |
| `ReportService` | Report CRUD, human-readable ID generation |
| `AnalysisService` | Run NLP pipeline, persist ReportAnalysis + Review + ModelPrediction |
| `ReviewService` | Review state machine (PENDING → APPROVE/REJECT/MODIFY), AI provenance |
| `AnalyticsService` | Dashboard aggregation queries (summary, trend, distribution) |
| `PrecursorService` | Precursor pattern rebuild and queries |
| `RiskService` | Site/activity/hazard/barrier risk ranking |
| `RulesService` | LSR retrieval and analytics |
| `ModelService` | ML model metadata introspection, review feedback aggregation |
| `SiteService` | Site CRUD |
| `record_audit()` | Single shared function that adds an AuditLog row to the caller's transaction |

---

## Database & Session Pattern

- **Engine**: `create_async_engine` backed by `asyncpg` (PostgreSQL) or `aiosqlite` (SQLite)
- **Pooling**: `QueuePool` (pool_size=5, max_overflow=10) in production; `NullPool` during tests
- **Session**: `async_sessionmaker` → `AsyncSession` with `expire_on_commit=False`
- **Injection**: `get_db()` yields a session via `Depends(get_db)` in every route that needs DB access
- **Transaction boundaries**: Services own commits and rollbacks. Routes must NOT call `db.commit()` or `db.rollback()` directly (exception: the explicit `POST /precursors/rebuild` endpoint delegates commit to the service via `commit=True`)
- **Test isolation**: Set `TESTING=1` or `TEST_DATABASE_URL` in the environment; `session.py` detects this and switches to `NullPool`

---

## Configuration

All configuration lives in `app/core/config.py` (`Settings` class backed by `pydantic-settings`).

- Load from `.env` file and environment variables
- Accessed via `get_settings()` (LRU-cached — safe to call repeatedly)
- Never import `Settings` directly; always use `get_settings()`
- No secrets, credentials, or environment-specific logic may be hardcoded anywhere else

**Key settings:**
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | HS256 signing key (min 16 chars) |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `ANALYSIS_REVIEW_THRESHOLD` | Confidence below which human review is triggered (default 0.62) |
| `APP_ENV` | `development` / `production` |

---

## Authentication & Authorization

- **JWT** bearer tokens issued at `/api/v1/auth/login`
- Token payload contains `sub` (user UUID) and `exp`
- `get_current_user()` in `deps.py` decodes the token and loads the user from DB
- `require_roles(*roles)` is a role-guard factory that returns a FastAPI dependency
- Use `CurrentUser` type alias for routes that only need the authenticated user identity

---

## Testing

```bash
# SQLite (default, fast)
pytest

# PostgreSQL
$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/sif_sentinel_test"
pytest

# Create PostgreSQL test DB if it doesn't exist
python create_test_db.py
```

- Tests live in `tests/` and are organized around API behavior, not implementation internals
- `conftest.py` sets `TESTING=1` (→ NullPool), creates and drops the schema, provides fixtures
- 72 tests covering auth, reports, analysis, review workflow, validation, precursors, health

---

## Migrations

```bash
# Auto-generate a migration from model changes
alembic revision --autogenerate -m "describe the change"

# Apply pending migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1
```

- Migration files live in `alembic/versions/`
- The `env.py` imports `app.models` to auto-detect model changes
- Never modify existing migration files; create a new one instead
- Both PostgreSQL and SQLite are supported; avoid dialect-specific SQL in migrations

---

## Key Design Constraints

1. **AI provenance is immutable**: `ReportAnalysis` rows are NEVER mutated after creation. Human corrections are stored in `Review.corrected_*` columns only.
2. **Review state machine**: `PENDING → APPROVE | REJECT | MODIFY`. Transitions are enforced in `ReviewService.decide()`. Any attempt to re-decide raises HTTP 409.
3. **Audit logging**: Every mutating operation records an `AuditLog` entry via `record_audit()` within the same transaction.
4. **Thin routes**: Route handlers call exactly one service method. No direct DB access from routes.
5. **No LLM/RAG/embeddings in core paths**: The NLP pipeline is purely deterministic. `llm.py` exists as a disabled extension point.
