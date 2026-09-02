# SIH26165 — SIF Precursor Detection Backend

Phase 1 provides a production-shaped FastAPI foundation for unsafe-act, unsafe-condition, near-miss, and incident reports. It intentionally does not implement NLP inference (Phase 2).

## Architecture

`API routes → Pydantic schemas → services → repositories → SQLAlchemy models → PostgreSQL`.

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

## Primary endpoints

- `GET /api/v1/health`, `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `GET /api/v1/users/me`
- `POST/GET /api/v1/sites`, `GET/PATCH /api/v1/sites/{site_id}`
- `POST/GET /api/v1/reports`, `GET/PATCH/DELETE /api/v1/reports/{report_id}`

See Swagger for endpoint contracts, authentication, enums, and response formats.
