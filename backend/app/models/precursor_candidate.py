import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import UUIDTimestampMixin


class PrecursorCandidate(UUIDTimestampMixin, Base):
    __tablename__ = "precursor_candidates"
    report_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("reports.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    activity: Mapped[str | None] = mapped_column(String(255))
    hazard: Mapped[str | None] = mapped_column(String(255))
    barrier: Mapped[str | None] = mapped_column(String(255))
    failure_type: Mapped[str | None] = mapped_column(String(255))
    evidence_text: Mapped[str | None] = mapped_column(Text)
    
    report = relationship("Report", backref="precursor_candidates")
