import math

from app.core.config import get_settings


def trend_factor(trend: str) -> float:
    return {"INCREASING": 1.0, "NEW": 0.8, "STABLE": 0.5, "DECREASING": 0.2, "INSUFFICIENT_DATA": 0.35}.get(trend, 0.35)


def risk_score(*, sif_density: float, occurrence_count: int, barrier_failure_rate: float, age_days: float, trend: str, site_count: int) -> float:
    settings = get_settings()
    frequency = min(1.0, occurrence_count / 10)
    recency = math.exp(-settings.precursor_recency_lambda * max(0.0, age_days))
    spread = min(1.0, site_count / 5)
    score = (settings.risk_density_weight * sif_density + settings.risk_frequency_weight * frequency + settings.risk_failure_weight * barrier_failure_rate + settings.risk_recency_weight * recency + settings.risk_trend_weight * trend_factor(trend) + settings.risk_spread_weight * spread)
    return round(min(1.0, max(0.0, score)), 3)


def risk_level(score: float) -> str:
    settings = get_settings()
    if score >= settings.risk_critical_threshold:
        return "CRITICAL"
    if score >= settings.risk_high_threshold:
        return "HIGH"
    if score >= settings.risk_medium_threshold:
        return "MEDIUM"
    return "LOW"
