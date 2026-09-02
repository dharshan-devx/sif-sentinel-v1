from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class PrecursorPattern(UUIDTimestampMixin, Base):
    __tablename__ = "precursor_patterns"
    activity: Mapped[str] = mapped_column(String(255), index=True)
    hazard: Mapped[str] = mapped_column(String(255), index=True)
    barrier: Mapped[str] = mapped_column(String(255))
    failure_type: Mapped[str] = mapped_column(String(255))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    sif_count: Mapped[int] = mapped_column(Integer, default=0)
    sif_density: Mapped[float] = mapped_column(Float, default=0)
    recent_count: Mapped[int] = mapped_column(Integer, default=0)
    trend: Mapped[str] = mapped_column(String(50), default="STABLE")
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    risk_level: Mapped[str] = mapped_column(String(50), default="LOW")
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
