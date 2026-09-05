FROM python:3.12-slim
WORKDIR /workspace/backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY backend/scripts ./scripts
COPY backend/pyproject.toml ./
COPY artifacts /workspace/artifacts
RUN pip install --no-cache-dir .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
