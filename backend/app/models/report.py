import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.constants import ReportStatus, ReportType, SourceType
from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class Report(UUIDTimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_filter", "site_id", "report_type", "status", "reported_at"),)
    report_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType, native_enum=False), nullable=False, index=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sites.id"), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    activity: Mapped[str | None] = mapped_column(String(255))
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=False), nullable=False, index=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus, native_enum=False), default=ReportStatus.NEW, nullable=False, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    site = relationship("Site", back_populates="reports")
    creator = relationship("User", back_populates="reports")
    analyses = relationship("ReportAnalysis", back_populates="report", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="report", cascade="all, delete-orphan")
    predictions = relationship("ModelPrediction", back_populates="report", cascade="all, delete-orphan")
