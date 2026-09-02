import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.constants import BarrierStatus, ReviewDecision, SIFLevel
from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class Review(UUIDTimestampMixin, Base):
    __tablename__ = "reviews"
    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("reports.id"), nullable=False, index=True)
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("report_analyses.id"), index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision, native_enum=False), nullable=False, index=True)
    corrected_sif_level: Mapped[SIFLevel | None] = mapped_column(Enum(SIFLevel, native_enum=False))
    corrected_activity: Mapped[str | None] = mapped_column(String(255))
    corrected_hazard: Mapped[str | None] = mapped_column(String(255))
    corrected_barrier: Mapped[str | None] = mapped_column(String(255))
    corrected_barrier_status: Mapped[BarrierStatus | None] = mapped_column(Enum(BarrierStatus, native_enum=False))
    corrected_barrier_failure: Mapped[str | None] = mapped_column(Text)
    corrected_life_saving_rule: Mapped[str | None] = mapped_column(String(255))
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    report = relationship("Report", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
