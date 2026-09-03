from dataclasses import dataclass

from app.knowledge.taxonomy import life_saving_rules
from app.services.nlp.evidence_model import EvidenceType, StructuredEvidence


@dataclass(frozen=True)
class RuleMatch:
    rule: str | None
    confidence: float
    matched_signals: list[str]


def map_to_life_saving_rule(activity: str | None, hazard: str | None, barrier: str | None, barrier_failure: str | None, text: str, structured_evidence: StructuredEvidence = None) -> RuleMatch:
    normalized = text.lower()
    candidates: list[tuple[float, str, list[str]]] = []
    
    for rule in life_saving_rules():
        signals: list[str] = []
        if activity and activity in rule["activities"]:
            signals.append(f"activity:{activity}")
        if hazard and hazard in rule["hazards"]:
            signals.append(f"hazard:{hazard}")
        if barrier and barrier in rule["barriers"]:
            signals.append(f"barrier:{barrier}")
            
        signals.extend(f"keyword:{word}" for word in rule["keywords"] if word in normalized)
        signals.extend(f"failure:{phrase}" for phrase in rule["failure_patterns"] if phrase in normalized)
        
        # If we have structured evidence, we should apply stricter mapping constraints.
        # Only map to the LSR if the control explicitly failed, or is missing/not_verified.
        # If the control is explicitly verified, do not add a strong failure signal.
        if structured_evidence:
            controls = structured_evidence.get_by_type(EvidenceType.CONTROL)
            for ctrl in controls:
                if ctrl.normalized_concept in rule["barriers"]:
                    if ctrl.verification_status in ("failed", "not verified", "not performed", "missing", "bypassed", "expired"):
                        signals.append(f"structured_failure:{ctrl.verification_status}")
                        
        score = min(1.0, 0.16 * len(signals))
        
        if structured_evidence:
            if any(signal.startswith("structured_failure:") for signal in signals):
                score = min(1.0, score + 0.12)
        elif barrier_failure and any(signal.startswith("failure:") for signal in signals):
            score = min(1.0, score + 0.12)
            
        if score:
            candidates.append((score, rule["name"], signals))
            
    if not candidates:
        return RuleMatch(None, 0.0, [])
        
    score, rule, signals = max(candidates, key=lambda item: item[0])
    if score < 0.32:
        return RuleMatch(None, 0.0, [])
        
    return RuleMatch(rule, round(score, 3), signals)
