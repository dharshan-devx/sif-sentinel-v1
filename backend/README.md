# SIH26165 — SIF Precursor Detection Backend

SIF Sentinel is a deterministic, evidence-backed safety decision-support backend
for unsafe-act, unsafe-condition, near-miss, and incident reports. Optional LLM
assistance is limited to a reviewer summary and is never required for analysis.

## Architecture

`report → validation → structured evidence → SIF/LSR → precursor → risk → intervention → human review → audit`.

For report analysis, the flow is `preprocess → TF-IDF/logistic SIF classifier → controlled entity/barrier extraction → Life-Saving Rule mapping → source evidence → weighted confidence → persistence/review routing`. Original report text is never modified. The lexical extraction and JSON knowledge base are deliberately deterministic, versioned, and replaceable by a future semantic layer.

The application uses asynchronous SQLAlchemy sessions, UUID primary keys, JWT
bearer authentication, role authorization, database-backed report
filtering/pagination, audit records, request IDs, and structured API errors.
SQLite and PostgreSQL are supported for tests and migrations.

## Quick start

1. `cd backend`
2. `python -m venv .venv`
3. Activate it (`.venv\\Scripts\\Activate.ps1` on PowerShell)
4. `pip install -e .[dev]`
5. Copy `.env.example` to `.env` and set a strong `JWT_SECRET_KEY`.
6. Start PostgreSQL, then run `alembic upgrade head`
7. `python scripts/seed.py`
8. `uvicorn app.main:app --reload`

The tracked prototype model artifact is generated from the versioned,
clearly labelled synthetic v1 dataset. To regenerate it reproducibly, run
`python -m app.ml.training.train_sif_model` from `backend`.

API docs: [http://localhost:8000/docs](http://localhost:8000/docs). The API root is `/api/v1`.

## Docker

From this directory, create `.env` from `.env.example`, set the secret, then run:

`docker compose up --build`

PostgreSQL data is stored in the `postgres_data` Docker volume. The backend waits for the PostgreSQL health check and applies migrations at startup.

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL (`postgresql+psycopg://...`) |
| `JWT_SECRET_KEY` | Required signing secret (16+ characters) |
| `JWT_ALGORITHM` | JWT algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default `60` |
| `APP_ENV` | Environment label |
| `LOG_LEVEL` | Logging level |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `ANALYSIS_REVIEW_THRESHOLD` | Overall confidence below this is queued for review (default `0.62`) |
| `CLASSIFIER_WEIGHT`, `ENTITY_WEIGHT`, `RULE_WEIGHT`, `EVIDENCE_WEIGHT` | Confidence-engine weights (defaults `0.45`, `0.25`, `0.20`, `0.10`) |

## Migrations and tests

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
pytest
ruff check .
```

Tests default to a separate local SQLite database. Set `TEST_DATABASE_URL` to
an isolated PostgreSQL test database to run the same suite against PostgreSQL;
never point it to a development or production database.

## Demo seed data

`python scripts/seed.py` creates synthetic demo users (`admin@sif.demo`, `analyst@sif.demo`, `reviewer@sif.demo`) and OIL-style sample sites. All use `Demo-Only-Password-2026!`. These demo records and Life-Saving Rule starters are not official OIL policy.

## Tables

`users`, `sites`, `reports`, `report_analyses`, `life_saving_rules`,
`precursor_candidates`, `precursor_patterns`, `intervention_recommendations`,
`reviews`, `model_predictions`, and `audit_logs`.

## ML baseline and prototype data

The classifier is a TF-IDF (word 1–2 grams) + class-balanced logistic-regression
model. Its versioned training input is
[safety_reports_v1.csv](data/training/safety_reports_v1.csv): 640 synthetic
prototype records, balanced between SIF and non-SIF examples and tagged
`source_type=SYNTHETIC`. It is not OIL operational data and must not be used to
claim real-world performance. The larger `safety_reports.csv` corpus is retained
for future validated evaluation and is not silently substituted into the v1 model.

Training performs a stratified 80/20 split with random seed 2026 and writes the model, vectorizer, versioned metadata, classification report, confusion matrix, and ROC-AUC to `app/ml/artifacts/metadata.json`. Metrics returned from `/api/v1/models/.../metrics` are read from that saved evaluation metadata; they are never fabricated at API time. The current synthetic dataset contains repeated controlled templates, so its evaluation numbers are only a pipeline check, not a generalization estimate.

## Analysis endpoints

- `POST /api/v1/analyze` — authenticated direct text analysis; does not persist a report.
- `POST /api/v1/reports/{report_id}/analyze` — runs the full pipeline, stores `ReportAnalysis` and `ModelPrediction`, updates report status, and creates a pending `Review` when review is required.
- `GET /api/v1/models`, `GET /api/v1/models/{model_name}`, `GET /api/v1/models/{model_name}/metrics` — authenticated model metadata and saved metrics.

Review is required when confidence is below threshold, classification is ambiguous, evidence is absent, or a medium/high risk prediction lacks a known rule mapping.

## Precursor intelligence and analytics

Phase 3 derives a **precursor pattern** from the latest analysis of each report: normalized `activity | hazard | barrier | barrier failure`. It counts recurring exposure signals; it does not make causal claims. Each report analysis triggers an idempotent pattern refresh, and administrators can run `POST /api/v1/precursors/rebuild` after imports or demonstrations.

Pattern aggregation is SQL-backed and produces occurrence/SIF counts, density, 30-day recency, site and department spread, first/last occurrence, and a trend. Trends compare the most recent 30 days with the previous comparable 30 days: ±20% yields increasing/decreasing; no earlier-period observations yield `NEW`; fewer than three total observations yields `INSUFFICIENT_DATA`.

The configurable 0–1 prototype risk score is:

`0.30 × SIF density + 0.20 × capped frequency + 0.20 × barrier-failure rate + 0.15 × exp(-λ × age days) + 0.10 × trend factor + 0.05 × capped site spread`

where `λ=0.03` by default, frequency caps at 10 reports, site spread caps at five sites, and trend factors are `1.0` increasing, `0.8` new, `0.5` stable, `0.2` decreasing, and `0.35` insufficient data. Levels are configurable: critical ≥0.75, high ≥0.55, medium ≥0.30, otherwise low. All dashboard and risk counts are database aggregations over latest report analyses; no Redis cache is used at prototype scale to avoid stale risk signals.

### Analytics APIs

- `GET /api/v1/precursors`, `GET /api/v1/precursors/trends`, `GET /api/v1/precursors/{id}`, `GET /api/v1/precursors/{id}/graph`
- `POST /api/v1/precursors/rebuild`
- `GET /api/v1/risk/sites`, `/risk/activities`, `/risk/hazards`, `/risk/barriers`
- `GET /api/v1/dashboard/summary`, `/sif-trend`, `/lsr-distribution`, `/site-comparison`, `/activity-distribution`, `/hazard-distribution`, `/barrier-failures`

The graph endpoint emits five React Flow-ready nodes (activity, hazard, barrier, failure, SIF) plus directed relationship edges. Precursor detail returns no more than five representative report summaries, avoiding report-text duplication.

## Primary endpoints

- `GET /api/v1/health`, `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `GET /api/v1/users/me`
- `POST/GET /api/v1/sites`, `GET/PATCH /api/v1/sites/{site_id}`
- `POST/GET /api/v1/reports`, `GET/PATCH/DELETE /api/v1/reports/{report_id}`

See Swagger for endpoint contracts, authentication, enums, and response formats.

## Intervention intelligence

`GET /api/v1/interventions`, `/summary`, and `/{id}` expose deterministic,
evidence-backed advisory recommendations. `POST /api/v1/interventions/{id}/review`
records accept, modify, or reject decisions for authorized HSE reviewers.
Recommendations never execute external actions or change SIF, LSR, precursor,
or risk results. See [INTERVENTION_INTELLIGENCE.md](INTERVENTION_INTELLIGENCE.md).

## LLM assistance

With `LLM_ENABLED=false` (the baseline demo mode), no provider key or network
access is required. With assistance enabled, provider failures are recorded as
metadata and deterministic outputs remain authoritative. See
[LLM_PROVIDER.md](LLM_PROVIDER.md).



test commands

python -m pytest tests/ -v --tb=short 2>&1


python -m pytest tests/ -v -q
