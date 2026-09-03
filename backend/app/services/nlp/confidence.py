from app.core.config import get_settings


def overall_confidence(classification: float, entity: float, rule: float, evidence: float) -> float:
    """
    Calculate a heuristic confidence score used to determine if human review is required.
    
    This is NOT a calibrated statistical probability. It is an arbitrary linear combination
    of the NLP model's prediction certainty, the strength of the entity matching,
    the presence of a mapped life-saving rule, and the presence of supporting evidence.
    It is used purely as an internal thresholding metric to route reports to reviewers
    when the combined signals are weak.
    """
    settings = get_settings()
    score = settings.classifier_weight * classification + settings.entity_weight * entity + settings.rule_weight * rule + settings.evidence_weight * evidence
    return round(min(1.0, max(0.0, score)), 3)
