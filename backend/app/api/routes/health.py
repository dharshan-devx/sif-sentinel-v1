from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession
from app.core.exceptions import AppError
from app.schemas.dashboard import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="Application liveness")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")

@router.get("/health/ready", response_model=HealthResponse, summary="Database readiness")
async def readiness(db: DBSession) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError("DATABASE_UNAVAILABLE", "Database is not ready", 503) from exc
    return HealthResponse(status="ready")
