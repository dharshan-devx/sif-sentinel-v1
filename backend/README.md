# SIH26165 — SIF Precursor Detection Backend

Phase 1 and 2 provide a production-shaped FastAPI foundation plus a local, reproducible SIF analysis engine for unsafe-act, unsafe-condition, near-miss, and incident reports. It does not use an LLM or external API key.

## Architecture

`API routes → Pydantic schemas → services → repositories → SQLAlchemy models → PostgreSQL`.

For report analysis, the flow is `preprocess → TF-IDF/logistic SIF classifier → controlled entity/barrier extraction → Life-Saving Rule mapping → source evidence → weighted confidence → persistence/review routing`. Original report text is never modified. The lexical extraction and JSON knowledge base are deliberately deterministic, versioned, and replaceable by a future semantic layer.

The application uses asynchronous SQLAlchemy sessions, UUID primary keys, JWT bearer authentication, role authorization, database-backed report filtering/pagination, audit records, request IDs, and structured API errors.

## Quick start

1. `cd backend`
2. `python -m venv .venv`
3. Activate it (`.venv\\Scripts\\Activate.ps1` on PowerShell)
4. `pip install -e .[dev]`
5. Copy `.env.example` to `.env` and set a strong `JWT_SECRET_KEY`.
6. Start PostgreSQL, then run `alembic upgrade head`
7. `python scripts/seed.py`
8. `uvicorn app.main:app --reload`

The tracked prototype model artifact is generated from the clearly labelled synthetic dataset. To regenerate it reproducibly, run `python -m app.ml.training.train_sif_model` from `backend`.

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

Tests use a separate local SQLite database and never target `DATABASE_URL`, so they do not destroy development data.

## Demo seed data

`python scripts/seed.py` creates synthetic demo users (`admin@sif.demo`, `analyst@sif.demo`, `reviewer@sif.demo`) and OIL-style sample sites. All use `Demo-Only-Password-2026!`. These demo records and Life-Saving Rule starters are not official OIL policy.

## Tables

`users`, `sites`, `reports`, `report_analyses`, `life_saving_rules`, `precursor_patterns`, `reviews`, `model_predictions`, and `audit_logs`.

## ML baseline and prototype data

The classifier is a TF-IDF (word 1–2 grams) + class-balanced logistic-regression model. Its data is [safety_reports.csv](data/training/safety_reports.csv): 640 synthetic prototype records, balanced between SIF and non-SIF examples and tagged `source_type=SYNTHETIC`. It is not OIL operational data and must not be used to claim real-world performance.

Training performs a stratified 80/20 split with random seed 2026 and writes the model, vectorizer, versioned metadata, classification report, confusion matrix, and ROC-AUC to `app/ml/artifacts/metadata.json`. Metrics returned from `/api/v1/models/.../metrics` are read from that saved evaluation metadata; they are never fabricated at API time. The current synthetic dataset contains repeated controlled templates, so its evaluation numbers are only a pipeline check, not a generalization estimate.

## Analysis endpoints

- `POST /api/v1/analyze` — authenticated direct text analysis; does not persist a report.
- `POST /api/v1/reports/{report_id}/analyze` — runs the full pipeline, stores `ReportAnalysis` and `ModelPrediction`, updates report status, and creates a pending `Review` when review is required.
- `GET /api/v1/models`, `GET /api/v1/models/{model_name}`, `GET /api/v1/models/{model_name}/metrics` — authenticated model metadata and saved metrics.

Review is required when confidence is below threshold, classification is ambiguous, evidence is absent, or a medium/high risk prediction lacks a known rule mapping.

## Primary endpoints

- `GET /api/v1/health`, `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `GET /api/v1/users/me`
- `POST/GET /api/v1/sites`, `GET/PATCH /api/v1/sites/{site_id}`
- `POST/GET /api/v1/reports`, `GET/PATCH/DELETE /api/v1/reports/{report_id}`

See Swagger for endpoint contracts, authentication, enums, and response formats.
