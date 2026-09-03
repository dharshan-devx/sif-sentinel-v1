"""Model service — ML model metadata and human review feedback aggregation.

Responsibility: Wraps model introspection and aggregates review feedback
metrics so routes remain thin and this logic becomes independently testable.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReviewDecision
from app.core.exceptions import AppError
from app.models.model_prediction import ModelPrediction
from app.models.review import Review
from app.services.nlp.sif_classifier import model_metadata as _raw_metadata


def current_model_metadata() -> dict:
    """Return current model metadata dict or raise AppError 503 if unavailable."""
    try:
        return _raw_metadata()
    except RuntimeError as exc:
        raise AppError("MODEL_UNAVAILABLE", "Safety classifier is unavailable", 503) from exc


async def get_feedback(db: AsyncSession) -> dict:
    """Aggregate human-review feedback statistics from the database."""
    total = await db.scalar(select(func.count()).select_from(ModelPrediction)) or 0
    reviewed = (
        await db.scalar(
            select(func.count()).select_from(Review).where(Review.decision != ReviewDecision.PENDING)
        )
        or 0
    )
    approved = (
        await db.scalar(
            select(func.count()).select_from(Review).where(Review.decision == ReviewDecision.APPROVE)
        )
        or 0
    )
    corrected = (
        await db.scalar(
            select(func.count()).select_from(Review).where(Review.decision == ReviewDecision.MODIFY)
        )
        or 0
    )
    return {
        "total_predictions": total,
        "reviewed_predictions": reviewed,
        "approved_predictions": approved,
        "corrected_predictions": corrected,
        "correction_rate": round(corrected / reviewed, 3) if reviewed else None,
        "human_review_metrics": (
            "unavailable: fewer than 10 reviewed predictions"
            if reviewed < 10
            else {"sample_size": reviewed}
        ),
    }


async def get_performance(db: AsyncSession) -> dict:
    """Combine offline model metrics with live human review feedback."""
    return {
        "offline_model_metrics": current_model_metadata()["metrics"],
        "human_review_metrics": await get_feedback(db),
    }
