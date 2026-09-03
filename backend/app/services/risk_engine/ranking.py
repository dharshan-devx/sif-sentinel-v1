from app.services.risk_engine.scoring import aggregate_risk_level, aggregate_risk_score


def rank_metrics(items: list[dict]) -> list[dict]:
    """Assign consistently calculated risk score/level and return descending risk order."""
    for item in items:
        item["risk_score"] = aggregate_risk_score(**item.pop("score_inputs"))
        item["risk_level"] = aggregate_risk_level(item["risk_score"])
    return sorted(items, key=lambda item: item["risk_score"], reverse=True)
