import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class CorrectiveAction(UUIDTimestampMixin, Base):
    """
    Persistent, auditable corrective action item with human-in-the-loop state machine.
    Maintains immutable provenance of original deterministic recommendation.
    """

    __tablename__ = "corrective_actions"
    __table_args__ = (
        Index("ix_corrective_actions_status", "status"),
        Index("ix_corrective_actions_priority", "priority"),
        Index("ix_corrective_actions_hierarchy_level", "hierarchy_level"),
        Index("ix_corrective_actions_report_id", "report_id"),
        Index("ix_corrective_actions_created_by", "created_by"),
    )

    report_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("reports.id"))
    intervention_recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("intervention_recommendations.id")
    )
    intervention_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hierarchy_level: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)

    # Immutable provenance snapshot of the original recommendation
    original_recommendation: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Track complete history of user modifications: [{user_id, timestamp, field, old, new, reason}]
    user_modifications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    assigned_to: Mapped[str | None] = mapped_column(String(255))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    closed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    verification_notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
