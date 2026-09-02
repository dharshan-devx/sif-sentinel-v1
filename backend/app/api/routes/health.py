from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.schemas.dashboard import HealthResponse
from app.services.nlp.sif_classifier import model_metadata

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="Application liveness")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")

@router.get("/health/status", summary="Application and local model status")
async def health_status() -> dict:
    try:
        version, model_status = model_metadata().get("model_version"), "ready"
    except RuntimeError:
        version, model_status = None, "unavailable"
    return {"application": "sif-backend", "version": "0.1.0", "environment": get_settings().app_env, "database": "use /health/ready", "model_status": model_status, "model_version": version}

@router.get("/health/ready", response_model=HealthResponse, summary="Database readiness")
async def readiness(db: DBSession) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError("DATABASE_UNAVAILABLE", "Database is not ready", 503) from exc
    return HealthResponse(status="ready")
