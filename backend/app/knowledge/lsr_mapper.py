from dataclasses import dataclass

from app.knowledge.taxonomy import life_saving_rules


@dataclass(frozen=True)
class RuleMatch:
    rule: str | None
    confidence: float
    matched_signals: list[str]


def map_to_life_saving_rule(activity: str | None, hazard: str | None, barrier: str | None, barrier_failure: str | None, text: str) -> RuleMatch:
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
        score = min(1.0, 0.16 * len(signals))
        if barrier_failure and any(signal.startswith("failure:") for signal in signals):
            score = min(1.0, score + 0.12)
        if score:
            candidates.append((score, rule["name"], signals))
    if not candidates:
        return RuleMatch(None, 0.0, [])
    score, rule, signals = max(candidates, key=lambda item: item[0])
    if score < 0.32:
        return RuleMatch(None, 0.0, [])
    return RuleMatch(rule, round(score, 3), signals)
