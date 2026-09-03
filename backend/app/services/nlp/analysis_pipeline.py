from dataclasses import dataclass

from app.core.config import get_settings
from app.core.constants import SIFLevel
from app.knowledge.lsr_mapper import map_to_life_saving_rule
from app.services.nlp.confidence import overall_confidence
from app.services.nlp.entity_extractor import extract_entities
from app.services.nlp.evidence_extractor import extract_evidence
from app.services.nlp.preprocessing import preprocess_text
from app.services.nlp.sif_classifier import classify_sif


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


def analyze_text(text: str) -> PipelineResult:
    document = preprocess_text(text)
    prediction = classify_sif(document.normalized_text)
    entities = extract_entities(document)
    rule = map_to_life_saving_rule(entities.activity, entities.hazard, entities.barrier, entities.barrier_failure, document.normalized_text)
    evidence = extract_evidence(document, entities)
    confidence = overall_confidence(max(prediction.probability, 1 - prediction.probability), entities.confidence, rule.confidence, evidence.confidence)
    ambiguous = 0.42 <= prediction.probability <= 0.58
    high_risk_without_rule = prediction.sif_level in (SIFLevel.HIGH, SIFLevel.MEDIUM) and not rule.rule
    review_required = confidence < get_settings().analysis_review_threshold or ambiguous or not evidence.evidence_span or high_risk_without_rule
    level = SIFLevel.REVIEW if review_required and prediction.sif_level in (SIFLevel.NON_SIF, SIFLevel.LOW, SIFLevel.REVIEW) else prediction.sif_level
    return PipelineResult(prediction.sif_potential, level, prediction.probability, entities.activity, entities.hazard, entities.barrier, entities.barrier_status.value, entities.barrier_failure, rule.rule, rule.confidence, evidence.evidence_span, evidence.evidence_sentences, evidence.evidence_terms, confidence, review_required, prediction.model_name, prediction.model_version, _explain(prediction.sif_level, entities, rule.rule, evidence.evidence_span, prediction.predictive_terms))


def _explain(level: SIFLevel, entities, rule: str | None, evidence: str | None, predictive_terms: list[str]) -> str:
    concepts = [item for item in (entities.activity, entities.hazard, entities.barrier) if item]
    description = ", ".join(concepts) if concepts else "limited controlled-domain signals"
    failure = f" and indicates the control was {entities.barrier_failure}" if entities.barrier_failure else ""
    mapping = f" This maps to the {rule} Life-Saving Rule." if rule else " No controlled Life-Saving Rule mapping was established."
    evidence_note = " Evidence was found in the submitted report." if evidence else " No meaningful source evidence was found."
    
    explanation = f"The report was classified as {level.value} SIF potential based on {description}{failure}.{mapping}{evidence_note}"
    
    if predictive_terms:
        formatted_terms = ", ".join(f"'{term}'" for term in predictive_terms)
        explanation += f" Top predictive terms identified by the model: {formatted_terms}."
        
    return explanation
