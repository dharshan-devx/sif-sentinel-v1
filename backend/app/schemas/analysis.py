from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import BarrierStatus, SIFLevel
from app.core.validators import validate_report_text
from app.schemas.common import ORMModel


class RiskComponent(BaseModel):
    name: str
    score: int
    reason: str


class RiskDetail(BaseModel):
    score: int
    priority: str
    components: list[RiskComponent]
    version: str


class AnalysisRead(ORMModel):
    sif_potential: bool | None
    sif_level: SIFLevel | None
    barrier_status: BarrierStatus | None
    reviewer_summary: str | None = None
    llm_attempted: bool = False
    llm_used: bool = False
    llm_provider: str | None = None
    llm_model_used: str | None = None
    llm_timestamp: datetime | None = None
    llm_error_code: str | None = None


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
    model_probability: float
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
    risk: RiskDetail | None = None
    
    # Phase 5B: Causal Safety Reasoning Metadata
    safety_graph: dict | None = None
    causal_chains: list[dict] | None = None
    reasoning_summary: str | None = None

    # Phase 5E: Narrative Translation Metadata
    narrative: dict | None = None

    # Phase 5F: Corrective Intervention & Prevention Metadata
    interventions: list[dict] | None = None
    prevention_plan: dict | None = None

    # Phase J: LLM Assistive Metadata
    reviewer_summary: str | None = None
    llm_attempted: bool = False
    llm_used: bool = False
    llm_provider: str | None = None
    llm_model_used: str | None = None
    llm_timestamp: datetime | None = None
    llm_error_code: str | None = None


class CounterfactualRequest(BaseModel):
    report_text: str | None = None
    target_control: str
    target_node_id: str | None = None
    simulated_status: str = "VERIFIED"
    safety_graph: dict | None = None
    causal_chains: list[dict] | None = None
    risk_score: int | None = None
    has_lsr: bool = True
    precursor_priority: str | None = "HIGH"


class CounterfactualChangeSchema(BaseModel):
    element_type: str
    element_name: str
    observed_value: Any
    simulated_value: Any
    description: str


class CounterfactualResponse(BaseModel):
    scenario_id: str
    target_node_id: str | None = None
    target_control: str
    original_status: str
    simulated_status: str
    original_barrier_failure: bool
    simulated_barrier_failure: bool
    original_exposure: str
    simulated_exposure: str
    original_risk_score: int
    simulated_risk_score: int
    risk_delta: int
    risk_direction: str
    original_sif_potential: bool
    simulated_sif_potential: bool
    original_sif_classification: str
    simulated_sif_classification: str
    causal_changes: list[CounterfactualChangeSchema]
    affected_nodes: list[str]
    affected_edges: list[dict[str, Any]]
    assumptions: list[str]
    interpretation: str
    confidence: float
    simulated_graph: dict[str, Any]
    simulation_only: bool = True
    created_at: str


class NarrativeBarrierAnalysisSchema(BaseModel):
    control: str
    observed_status: str
    failure: bool
    explanation: str
    source_basis: str = "CAUSAL_GRAPH"


class NarrativeActionSchema(BaseModel):
    action: str
    reason: str
    priority: str
    source_basis: str
    target_control: str | None = None


class NarrativeGroundingSchema(BaseModel):
    claim: str
    source_type: str
    source_reference: str


class NarrativeRequest(BaseModel):
    incident_text: str = Field(min_length=1, max_length=20_000)
    mode: str = "EXECUTIVE"
    safety_graph: dict[str, Any] | None = None
    causal_chains: list[dict[str, Any]] | None = None
    risk_score: int | None = None
    risk_priority: str | None = None
    sif_potential: bool | None = None
    sif_level: str | None = None
    life_saving_rule: str | None = None
    evidence_span: str | None = None
    evidence_terms: list[str] = Field(default_factory=list)
    counterfactual_scenario: dict[str, Any] | None = None
    confidence: float | None = None


class NarrativeResponse(BaseModel):
    mode: str
    executive_summary: str
    incident_interpretation: str
    causal_explanation: str
    barrier_analysis: list[NarrativeBarrierAnalysisSchema]
    sif_explanation: str
    risk_explanation: str
    lsr_explanation: str | None = None
    key_findings: list[str]
    recommended_actions: list[NarrativeActionSchema]
    counterfactual_explanation: str | None = None
    confidence_statement: str
    limitations: list[str]
    grounding: list[NarrativeGroundingSchema]
    validation_status: str
    validation_errors: list[str] = Field(default_factory=list)
    provider_name: str
    model_name: str
    latency_ms: float
    generated_at: str


# ============================================================
# Phase 5F: Corrective Intervention & Prevention Schemas
# ============================================================


class InterventionRecommendationSchema(BaseModel):
    id: str
    intervention_code: str
    title: str
    description: str
    hierarchy_level: str
    action_type: str
    priority: str
    priority_score: int
    urgency: str
    rationale: str
    linked_hazard: str
    linked_activity: str
    linked_barrier: str
    target_node_id: str | None = None
    current_barrier_status: str
    target_barrier_status: str = "VERIFIED"
    predicted_original_risk: int
    predicted_simulated_risk: int
    predicted_risk_delta: int
    feasibility_score: str
    implementation_timeframe: str
    required_lsr: str | None = None
    source_basis: str = "CAUSAL_GRAPH + RISK_ENGINE + BARRIER_STATUS"
    deterministic_rule_id: str
    confidence: float = 0.95
    status: str = "GENERATED"
    created_at: str


class PreventionTrajectoryStepSchema(BaseModel):
    step_number: int
    barrier_name: str
    action_title: str
    simulated_risk_score: int
    step_risk_delta: int
    cumulative_risk_delta: int
    residual_sif_potential: bool


class CumulativePreventionPlanSchema(BaseModel):
    plan_id: str
    baseline_risk: int
    target_risk: int
    total_risk_delta: int
    defense_in_depth_layers: list[str]
    trajectory: list[PreventionTrajectoryStepSchema]
    primary_mitigation: str
    secondary_mitigation: str | None = None
    residual_risk_level: str
    assumptions: list[str]


class InterventionAnalysisRequest(BaseModel):
    incident_text: str | None = None
    safety_graph: dict[str, Any] | None = None
    risk_score: int | None = None
    risk_priority: str | None = None
    life_saving_rule: str | None = None
    sif_level: str | None = None


class InterventionAnalysisResponse(BaseModel):
    total_recommendations: int
    overall_hierarchy_level: str
    baseline_risk_score: int
    target_risk_score: int
    cumulative_risk_delta: int
    recommendations: list[InterventionRecommendationSchema]
    cumulative_prevention_plan: CumulativePreventionPlanSchema
    source_basis: str
    deterministic: bool = True
    generated_at: str



