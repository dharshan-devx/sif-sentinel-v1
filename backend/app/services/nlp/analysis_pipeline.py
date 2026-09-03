from dataclasses import dataclass

from app.core.config import get_settings
from app.core.constants import SIFLevel
from app.knowledge.lsr_mapper import map_to_life_saving_rule
from app.services.nlp.confidence import overall_confidence
from app.services.nlp.entity_extractor import extract_entities, get_structured_evidence
from app.services.nlp.evidence_extractor import extract_evidence
from app.services.nlp.evidence_model import EvidenceType, StructuredEvidence
from app.services.nlp.precursor_rules import PrecursorCandidateItem, generate_precursor_candidates
from app.services.nlp.preprocessing import preprocess_text
from app.services.nlp.sif_classifier import classify_sif
from app.services.risk_engine.calculator import calculate_risk


@dataclass(frozen=True)
class PipelineResult:
    sif_potential: bool
    sif_level: SIFLevel
    sif_probability: float
    activity: str | None
    hazard: str | None
    barrier: str | None
    barrier_status: str
    barrier_failure: str | None
    life_saving_rule: str | None
    rule_confidence: float
    evidence_span: str | None
    evidence_sentences: list[str]
    evidence_terms: list[str]
    overall_confidence: float
    review_required: bool
    model_name: str
    model_version: str
    explanation: str
    precursor_candidates: list[PrecursorCandidateItem]
    risk: dict | None


def analyze_text(text: str, precursor_priority: str | None = None) -> PipelineResult:
    document = preprocess_text(text)
    prediction = classify_sif(document.normalized_text)
    
    structured_evidence = get_structured_evidence(document)
    entities = extract_entities(document)
    
    rule = map_to_life_saving_rule(
        entities.activity, 
        entities.hazard, 
        entities.barrier, 
        entities.barrier_failure, 
        document.normalized_text, 
        structured_evidence
    )
    
    evidence = extract_evidence(document, entities)
    confidence = overall_confidence(max(prediction.probability, 1 - prediction.probability), entities.confidence, rule.confidence, evidence.confidence)
    ambiguous = 0.42 <= prediction.probability <= 0.58
    
    # If a barrier is explicitly 'unknown', force review
    has_unknown_barrier = any(ctrl.verification_status == "unknown" for ctrl in structured_evidence.get_by_type(EvidenceType.CONTROL))
    
    high_risk_without_rule = prediction.sif_level in (SIFLevel.HIGH, SIFLevel.MEDIUM) and not rule.rule
    review_required = confidence < get_settings().analysis_review_threshold or ambiguous or not evidence.evidence_span or high_risk_without_rule or has_unknown_barrier
    
    level = SIFLevel.REVIEW if review_required and prediction.sif_level in (SIFLevel.NON_SIF, SIFLevel.LOW, SIFLevel.REVIEW) else prediction.sif_level
    
    precursor_candidates = generate_precursor_candidates(structured_evidence)
    
    risk_data = calculate_risk(
        sif_level=level,
        sif_potential=prediction.sif_potential,
        barrier_status=entities.barrier_status,
        has_lsr=bool(rule.rule),
        precursor_priority=precursor_priority
    )
    
    return PipelineResult(
        prediction.sif_potential, level, prediction.probability, 
        entities.activity, entities.hazard, entities.barrier, 
        entities.barrier_status.value, entities.barrier_failure, 
        rule.rule, rule.confidence, evidence.evidence_span, 
        evidence.evidence_sentences, evidence.evidence_terms, 
        confidence, review_required, prediction.model_name, 
        prediction.model_version, 
        _explain(prediction.sif_level, structured_evidence, rule.rule, evidence.evidence_span, prediction.predictive_terms, review_required, has_unknown_barrier),
        precursor_candidates,
        risk_data
    )


def _explain(level: SIFLevel, structured: StructuredEvidence, rule: str | None, evidence: str | None, predictive_terms: list[str], review_required: bool, has_unknown_barrier: bool) -> str:
    parts = []
    
    activities = structured.get_by_type(EvidenceType.ACTIVITY)
    hazards = structured.get_by_type(EvidenceType.HAZARD)
    controls = structured.get_by_type(EvidenceType.CONTROL)
    
    if activities or hazards:
        concepts = [item.normalized_concept for item in activities + hazards]
        parts.append(f"Evidence identified {', '.join(concepts)}.")
        
    for ctrl in controls:
        if ctrl.verification_status == "verified":
            parts.append(f"The report states that {ctrl.normalized_concept} was explicitly verified.")
        elif ctrl.verification_status == "not verified":
            parts.append(f"The report states that {ctrl.normalized_concept} was NOT verified.")
        elif ctrl.verification_status == "failed":
            parts.append(f"The report states that {ctrl.normalized_concept} failed or was bypassed.")
        elif ctrl.verification_status == "not performed":
            parts.append(f"The report states that the activity was performed without {ctrl.normalized_concept}.")
        elif ctrl.verification_status == "unknown":
            parts.append(f"The report mentions {ctrl.normalized_concept} but its verification status is ambiguous or unknown.")
            
    if rule:
        parts.append(f"This evidence maps to the {rule} Life-Saving Rule.")
    else:
        parts.append("No controlled Life-Saving Rule mapping was established.")
        
    if not evidence:
        parts.append("No meaningful source evidence was found.")
        
    if predictive_terms:
        formatted_terms = ", ".join(f"'{term}'" for term in predictive_terms)
        parts.append(f"The ML model identified {formatted_terms} as top predictive terms.")
        
    if review_required:
        if has_unknown_barrier:
            parts.append("Human review is recommended because the assessment depends on an ambiguous or unknown verification state.")
        else:
            parts.append("Human review is recommended to confirm this assessment.")

    return " ".join(parts)
