from uuid import UUID

from pydantic import BaseModel


class RiskItem(BaseModel):
    name: str
    report_count: int
    sif_count: int
    sif_density: float
    barrier_failure_count: int
    risk_score: float
    risk_level: str
    explanation: str


class SiteRiskItem(RiskItem):
    site_id: UUID
    total_reports: int
    sif_reports: int
    sif_rate: float
    high_risk_reports: int
    active_precursor_patterns: int
    recent_reports: int


class BarrierRiskItem(BaseModel):
    barrier: str
    total_occurrences: int
    failed_count: int
    failure_rate: float
    associated_sif_count: int
    risk_score: float
    risk_level: str
    explanation: str
