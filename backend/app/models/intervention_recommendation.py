import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class InterventionRecommendation(UUIDTimestampMixin, Base):
    """Immutable deterministic recommendation with separate human review fields."""

    __tablename__ = "intervention_recommendations"
    __table_args__ = (
        Index("ix_intervention_recommendations_priority", "priority"),
        Index("ix_intervention_recommendations_review_status", "review_status"),
        Index("ix_intervention_recommendations_category", "category"),
    )

    report_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("reports.id"), index=True)
    precursor_pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("precursor_patterns.id"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    intervention_rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    review_required: Mapped[bool] = mapped_column(nullable=False, default=False)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_rule: Mapped[str] = mapped_column(String(160), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_priority: Mapped[str | None] = mapped_column(String(20))
    life_saving_rule: Mapped[str | None] = mapped_column(String(255))

    review_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer_comments: Mapped[str | None] = mapped_column(Text)
    reviewer_title: Mapped[str | None] = mapped_column(String(255))
    reviewer_description: Mapped[str | None] = mapped_column(Text)
    reviewer_rationale: Mapped[str | None] = mapped_column(Text)
