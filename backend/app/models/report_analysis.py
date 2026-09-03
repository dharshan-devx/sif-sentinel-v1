import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.constants import BarrierStatus, SIFLevel
from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class ReportAnalysis(UUIDTimestampMixin, Base):
    __tablename__ = "report_analyses"
    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("reports.id"), index=True, nullable=False)
    sif_potential: Mapped[bool | None]
    sif_level: Mapped[SIFLevel | None] = mapped_column(Enum(SIFLevel, native_enum=False), index=True)
    model_probability: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[int | None] = mapped_column(Float) # SQLite doesn't strictly type ints vs floats, but Float is safe. Let's use Float or Integer. The score is 1-100, let's use Float for future proofing or integer. I'll use Float.
    risk_priority: Mapped[str | None] = mapped_column(String(50))
    risk_components: Mapped[dict | None] = mapped_column(JSON)
    risk_version: Mapped[str | None] = mapped_column(String(50))
    activity: Mapped[str | None] = mapped_column(String(255), index=True)
    hazard: Mapped[str | None] = mapped_column(String(255), index=True)
    barrier: Mapped[str | None] = mapped_column(String(255), index=True)
    barrier_status: Mapped[BarrierStatus | None] = mapped_column(Enum(BarrierStatus, native_enum=False))
    barrier_failure: Mapped[str | None] = mapped_column(Text)
    life_saving_rule: Mapped[str | None] = mapped_column(String(255), index=True)
    rule_confidence: Mapped[float | None] = mapped_column(Float)
    evidence_span: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    overall_confidence: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(100))
    
    # Phase J: LLM Metadata
    llm_attempted: Mapped[bool] = mapped_column(default=False, server_default="0", nullable=False)
    llm_used: Mapped[bool] = mapped_column(default=False, server_default="0", nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    analysis_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    report = relationship("Report", back_populates="analyses")
