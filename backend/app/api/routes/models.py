from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.core.exceptions import AppError
from app.models.model_prediction import ModelPrediction
from app.models.review import Review
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


@router.get("/feedback", summary="Human-review feedback aggregates")
async def feedback(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> dict:
    total = await db.scalar(select(func.count()).select_from(ModelPrediction)) or 0
    reviewed = await db.scalar(select(func.count()).select_from(Review).where(Review.decision != "PENDING")) or 0
    approved = await db.scalar(select(func.count()).select_from(Review).where(Review.decision == "APPROVE")) or 0
    corrected = await db.scalar(select(func.count()).select_from(Review).where(Review.decision == "MODIFY")) or 0
    return {"total_predictions": total, "reviewed_predictions": reviewed, "approved_predictions": approved, "corrected_predictions": corrected, "correction_rate": round(corrected / reviewed, 3) if reviewed else None, "human_review_metrics": "unavailable: fewer than 10 reviewed predictions" if reviewed < 10 else {"sample_size": reviewed}}


@router.get("/performance", summary="Separate offline evaluation from human review feedback")
async def performance(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> dict:
    return {"offline_model_metrics": _current_model()["metrics"], "human_review_metrics": await feedback(db, _)}


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
