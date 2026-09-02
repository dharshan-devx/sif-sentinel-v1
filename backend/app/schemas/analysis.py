from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import BarrierStatus, SIFLevel
from app.core.validators import validate_report_text
from app.schemas.common import ORMModel


class AnalysisRead(ORMModel):
    sif_potential: bool | None
    sif_level: SIFLevel | None
    barrier_status: BarrierStatus | None


class AnalyzeTextRequest(BaseModel):
    # Same outer guard and same configurable policy as report_text — the
    # direct /analyze endpoint must not accept input that /reports would reject.
    text: str = Field(min_length=1, max_length=100_000)

    @field_validator("text")
    @classmethod
    def _validate_text(cls, v: str) -> str:
        return validate_report_text(v)


class AnalysisResponse(BaseModel):
    report_id: str | None = None
    analysis_id: UUID | None = None
    sif_potential: bool
    sif_level: SIFLevel
    sif_probability: float
    activity: str | None
    hazard: str | None
    barrier: str | None
    barrier_status: BarrierStatus
    barrier_failure: str | None
    life_saving_rule: str | None
    rule_confidence: float
    evidence_span: str | None
    evidence_sentences: list[str]
    evidence_terms: list[str]
    overall_confidence: float
    review_required: bool
    model_version: str
    explanation: str
