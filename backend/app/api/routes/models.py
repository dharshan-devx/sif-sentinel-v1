from fastapi import APIRouter, Depends

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.core.exceptions import AppError
from app.models.user import User
from app.services.model_service import (
    current_model_metadata,
    get_feedback,
    get_performance,
)

router = APIRouter(prefix="/models", tags=["Models"])

_analyst_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST)


@router.get("", summary="List available analysis models")
async def list_models(_: User = Depends(require_roles(*_analyst_roles))) -> list[dict]:
    return [current_model_metadata()]


@router.get("/feedback", summary="Human-review feedback aggregates")
async def feedback(db: DBSession, _: User = Depends(require_roles(*_analyst_roles))) -> dict:
    return await get_feedback(db)


@router.get("/performance", summary="Separate offline evaluation from human review feedback")
async def performance(db: DBSession, _: User = Depends(require_roles(*_analyst_roles))) -> dict:
    return await get_performance(db)


@router.get("/{model_name}", summary="Get model metadata")
async def get_model(model_name: str, _: User = Depends(require_roles(*_analyst_roles))) -> dict:
    metadata = current_model_metadata()
    if model_name not in (metadata["model_name"], metadata["model_version"]):
        raise AppError("MODEL_NOT_FOUND", "Model not found", 404)
    return metadata


@router.get("/{model_name}/metrics", summary="Get actual saved evaluation metrics")
async def get_metrics(model_name: str, _: User = Depends(require_roles(*_analyst_roles))) -> dict:
    metadata = current_model_metadata()
    if model_name not in (metadata["model_name"], metadata["model_version"]):
        raise AppError("MODEL_NOT_FOUND", "Model not found", 404)
    return metadata["metrics"]
