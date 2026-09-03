from typing import Any

from app.core.config import get_settings
from app.core.constants import BarrierStatus, SIFLevel


def calculate_risk(
    sif_level: SIFLevel | None,
    sif_potential: bool | None,
    barrier_status: str | BarrierStatus | None,
    has_lsr: bool,
    precursor_priority: str | None,
) -> dict[str, Any]:
    """
    Deterministically calculates a 1-100 risk score based on structured evidence.
    """
    settings = get_settings()
    components = []
    total_score = 0

    # 1. Consequence Component (Max 30)
    consequence_score = 0
    consequence_reason = "No significant consequence identified"
    if sif_level == SIFLevel.HIGH:
        consequence_score = 30
        consequence_reason = "High potential for Serious Injury or Fatality"
    elif sif_level == SIFLevel.MEDIUM:
        consequence_score = 20
        consequence_reason = "Medium potential for Serious Injury or Fatality"
    elif sif_level == SIFLevel.LOW:
        consequence_score = 10
        consequence_reason = "Low potential for Serious Injury or Fatality"
    elif sif_potential is True:
        consequence_score = 15
        consequence_reason = "General SIF potential identified"

    if consequence_score > 0:
        components.append({
            "name": "Consequence",
            "score": consequence_score,
            "reason": consequence_reason
        })
        total_score += consequence_score

    # 2. Control Degradation Component (Max 30)
    control_score = 0
    control_reason = "Controls appear intact or no failure identified"
    b_status = barrier_status.value if isinstance(barrier_status, BarrierStatus) else barrier_status
    if b_status in ("failed", "bypassed", "not performed"):
        control_score = 30
        control_reason = f"Critical control degradation ({b_status})"
    elif b_status == "ineffective":
        control_score = 20
        control_reason = "Control identified as ineffective"
    elif b_status == "not verified":
        control_score = 15
        control_reason = "Control verification failed"
    elif b_status == "unknown":
        control_score = 10
        control_reason = "Control state is unknown or ambiguous"

    if control_score > 0:
        components.append({
            "name": "Control Degradation",
            "score": control_score,
            "reason": control_reason
        })
        total_score += control_score

    # 3. LSR Relevance Component (Max 15)
    if has_lsr:
        components.append({
            "name": "Life-Saving Rule",
            "score": 15,
            "reason": "Direct mapping to Life-Saving Rules"
        })
        total_score += 15

    # 4. Precursor Recurrence Component (Max 25)
    precursor_score = 0
    precursor_reason = "No recurring precursor pattern"
    if precursor_priority:
        priority_upper = precursor_priority.upper()
        if priority_upper == "CRITICAL":
            precursor_score = 25
            precursor_reason = "Matches CRITICAL recurring precursor pattern"
        elif priority_upper == "HIGH":
            precursor_score = 20
            precursor_reason = "Matches HIGH recurring precursor pattern"
        elif priority_upper == "MEDIUM":
            precursor_score = 10
            precursor_reason = "Matches MEDIUM recurring precursor pattern"
        elif priority_upper == "LOW":
            precursor_score = 5
            precursor_reason = "Matches LOW recurring precursor pattern"

    if precursor_score > 0:
        components.append({
            "name": "Precursor Recurrence",
            "score": precursor_score,
            "reason": precursor_reason
        })
        total_score += precursor_score

    # Normalize score
    final_score = min(settings.risk_score_max, max(settings.risk_score_min, total_score))
    if final_score == 0:
        final_score = settings.risk_score_min

    # Map to Priority
    if final_score >= settings.risk_critical_threshold:
        priority = "CRITICAL"
    elif final_score >= settings.risk_high_threshold:
        priority = "HIGH"
    elif final_score >= settings.risk_medium_threshold:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {
        "score": final_score,
        "priority": priority,
        "components": components,
        "version": settings.risk_engine_version
    }
