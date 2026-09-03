import math

from app.core.config import get_settings


def trend_factor(trend: str) -> float:
    return {"INCREASING": 1.0, "NEW": 0.8, "STABLE": 0.5, "DECREASING": 0.2, "INSUFFICIENT_DATA": 0.35}.get(trend, 0.35)


def aggregate_risk_score(*, sif_density: float, occurrence_count: int, barrier_failure_rate: float, age_days: float, trend: str, site_count: int) -> float:
    settings = get_settings()
    frequency = min(1.0, occurrence_count / 10)
    recency = math.exp(-settings.precursor_recency_lambda * max(0.0, age_days))
    spread = min(1.0, site_count / 5)
    score = (settings.aggregate_density_weight * sif_density + settings.aggregate_frequency_weight * frequency + settings.aggregate_failure_weight * barrier_failure_rate + settings.aggregate_recency_weight * recency + settings.aggregate_trend_weight * trend_factor(trend) + settings.aggregate_spread_weight * spread)
    return round(min(1.0, max(0.0, score)), 3)


def aggregate_risk_level(score: float) -> str:
    # We still map this 0.0-1.0 score to Priority/Level for aggregates, 
    # but we'll use a fixed threshold since the risk_engine 1-100 threshold is different.
    # We can hardcode the old thresholds for aggregate to preserve Phase H logic.
    if score >= 0.75:
        return "CRITICAL"
    if score >= 0.55:
        return "HIGH"
    if score >= 0.30:
        return "MEDIUM"
    return "LOW"
