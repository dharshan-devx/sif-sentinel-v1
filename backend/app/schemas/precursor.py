from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class PrecursorRead(ORMModel):
    id: UUID
    activity: str
    hazard: str


class PrecursorSummary(PrecursorRead):
    category: str
    barrier: str
    failure_type: str
    occurrence_count: int
    sif_count: int
    sif_density: float
    recent_count: int
    site_count: int
    department_count: int
    trend: str
    risk_score: float
    priority: str
    first_seen: datetime | None
    last_seen: datetime | None
    why_it_matters: str


class RepresentativeReport(BaseModel):
    report_id: str
    reported_at: datetime
    site_name: str
    department: str
    sif_level: str | None


class PrecursorDetail(PrecursorSummary):
    sites: list[str]
    departments: list[str]
    representative_reports: list[RepresentativeReport]


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    statistics: dict[str, int | float | str]


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str


class PrecursorGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
