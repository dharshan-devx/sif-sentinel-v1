import uuid

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.constants import BarrierStatus, SIFLevel
from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class ReportAnalysis(UUIDTimestampMixin, Base):
    __tablename__ = "report_analyses"
    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("reports.id"), index=True, nullable=False)
    sif_potential: Mapped[bool | None]
    sif_level: Mapped[SIFLevel | None] = mapped_column(Enum(SIFLevel, native_enum=False))
    sif_probability: Mapped[float | None] = mapped_column(Float)
    activity: Mapped[str | None] = mapped_column(String(255))
    hazard: Mapped[str | None] = mapped_column(String(255))
    barrier: Mapped[str | None] = mapped_column(String(255))
    barrier_status: Mapped[BarrierStatus | None] = mapped_column(Enum(BarrierStatus, native_enum=False))
    barrier_failure: Mapped[str | None] = mapped_column(Text)
    life_saving_rule: Mapped[str | None] = mapped_column(String(255))
    rule_confidence: Mapped[float | None] = mapped_column(Float)
    evidence_span: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    overall_confidence: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(100))
    analysis_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    report = relationship("Report", back_populates="analyses")
