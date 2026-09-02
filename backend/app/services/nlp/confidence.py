from app.core.config import get_settings


def overall_confidence(classification: float, entity: float, rule: float, evidence: float) -> float:
    settings = get_settings()
    score = settings.classifier_weight * classification + settings.entity_weight * entity + settings.rule_weight * rule + settings.evidence_weight * evidence
    return round(min(1.0, max(0.0, score)), 3)
