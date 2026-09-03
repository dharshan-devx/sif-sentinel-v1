# SIF SENTINEL Backend

This directory contains the FastAPI modular monolith.

## Setup
```bash
# In the backend/ directory
uv sync
```

## Running the API
```bash
uv run uvicorn app.main:app --reload
```

## Testing
Run tests locally using SQLite or PostgreSQL.
```bash
# Make sure you are inside the backend/ directory
uv run pytest tests/
```

## Database
Uses SQLAlchemy and Alembic. Ensure your `.env` contains valid configurations for PostgreSQL.
