from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.analysis import (
    AnalysisResponse,
    AnalyzeTextRequest,
    CounterfactualRequest,
    CounterfactualResponse,
    InterventionAnalysisRequest,
    InterventionAnalysisResponse,
    NarrativeRequest,
    NarrativeResponse,
)
from app.services.analysis.analysis_service import AnalysisService
from app.services.narrative.narrative_models import NarrativeMode
from app.services.narrative.narrative_service import NarrativeTranslationService
from app.services.nlp.causal_engine import ControlStatus
from app.services.nlp.counterfactual_engine import CounterfactualSafetyEngine
from app.services.nlp.intervention_engine import SafetyInterventionEngine

router = APIRouter(tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResponse, summary="Analyze text without persisting a report")
async def analyze_text_endpoint(payload: AnalyzeTextRequest, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER))) -> AnalysisResponse:
    return AnalysisService(None).analyze_direct(payload.text)


@router.post("/analyze/counterfactual", response_model=CounterfactualResponse, summary="Simulate counterfactual safety barrier restoration")
async def analyze_counterfactual_endpoint(payload: CounterfactualRequest, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER))) -> CounterfactualResponse:
    graph = payload.safety_graph
    risk_score = payload.risk_score

    if not graph:
        if not payload.report_text:
            raise HTTPException(status_code=422, detail="Either safety_graph or report_text must be provided for simulation.")
        analysis = AnalysisService(None).analyze_direct(payload.report_text)
        graph = analysis.safety_graph
        if risk_score is None and analysis.risk:
            risk_score = analysis.risk.score

    if not graph:
        raise HTTPException(status_code=422, detail="No causal safety graph available for the incident report.")

    try:
        sim_status = ControlStatus(payload.simulated_status.upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported simulated status '{payload.simulated_status}'.",
        ) from exc

    try:
        scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
            original_graph=graph,
            target_control=payload.target_control,
            simulated_status=sim_status,
            target_node_id=payload.target_node_id,
            original_risk_score=risk_score,
            has_lsr=payload.has_lsr,
            precursor_priority=payload.precursor_priority,
        )
        return CounterfactualResponse(**scenario.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyze/narrative", response_model=NarrativeResponse, summary="Generate explainable AI narrative translation")
async def analyze_narrative_endpoint(
    payload: NarrativeRequest,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER)),
) -> NarrativeResponse:
    try:
        mode = NarrativeMode(payload.mode.upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported narrative mode '{payload.mode}'.",
        ) from exc

    context = NarrativeTranslationService.build_context_from_analysis(
        incident_text=payload.incident_text,
        safety_graph=payload.safety_graph,
        causal_chains=payload.causal_chains,
        risk_score=payload.risk_score,
        risk_priority=payload.risk_priority,
        sif_potential=payload.sif_potential,
        sif_level=payload.sif_level,
        life_saving_rule=payload.life_saving_rule,
        evidence_span=payload.evidence_span,
        evidence_terms=payload.evidence_terms,
        counterfactual=payload.counterfactual_scenario,
        confidence=payload.confidence,
    )

    narrative_svc = NarrativeTranslationService()
    output = await narrative_svc.translate(context, mode)
    return NarrativeResponse(**output.to_dict())


@router.post("/analyze/interventions", response_model=InterventionAnalysisResponse, summary="Generate deterministic hierarchy of controls & prevention plan")
async def analyze_interventions_endpoint(
    payload: InterventionAnalysisRequest,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)),
) -> InterventionAnalysisResponse:
    graph = payload.safety_graph
    risk_score = payload.risk_score
    risk_priority = payload.risk_priority
    lsr = payload.life_saving_rule
    sif_lvl = payload.sif_level

    if not graph:
        if not payload.incident_text:
            raise HTTPException(status_code=422, detail="Either safety_graph or incident_text must be provided for intervention analysis.")
        analysis = AnalysisService(None).analyze_direct(payload.incident_text)
        graph = analysis.safety_graph
        if risk_score is None and analysis.risk:
            risk_score = analysis.risk.score
            risk_priority = analysis.risk.priority
        if not lsr:
            lsr = analysis.life_saving_rule
        if not sif_lvl and analysis.sif_level:
            sif_lvl = analysis.sif_level.value if hasattr(analysis.sif_level, "value") else str(analysis.sif_level)

    if not graph:
        raise HTTPException(status_code=422, detail="No causal safety graph could be constructed for intervention analysis.")

    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=graph,
        risk_score=risk_score,
        risk_priority=risk_priority,
        life_saving_rule=lsr,
        sif_level=sif_lvl,
    )

    return InterventionAnalysisResponse(**result.to_dict())



