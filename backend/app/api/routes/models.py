from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.core.constants import UserRole
from app.core.exceptions import AppError
from app.models.user import User
from app.services.nlp.sif_classifier import model_metadata

router = APIRouter(prefix="/models", tags=["Models"])


def _current_model() -> dict:
    try:
        return model_metadata()
    except RuntimeError as exc:
        raise AppError("MODEL_UNAVAILABLE", "Safety classifier is unavailable", 503) from exc


@router.get("", summary="List available analysis models")
async def list_models(_: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> list[dict]:
    return [_current_model()]


@router.get("/{model_name}", summary="Get model metadata")
async def get_model(model_name: str, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> dict:
    metadata = _current_model()
    if model_name not in (metadata["model_name"], metadata["model_version"]):
        raise AppError("MODEL_NOT_FOUND", "Model not found", 404)
    return metadata


@router.get("/{model_name}/metrics", summary="Get actual saved evaluation metrics")
async def get_metrics(model_name: str, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> dict:
    metadata = await get_model(model_name, _)
    return metadata["metrics"]
