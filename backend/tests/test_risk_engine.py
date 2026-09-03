

from app.core.config import get_settings
from app.core.constants import SIFLevel
from app.services.risk_engine.calculator import calculate_risk


def test_score_boundaries_and_defaults():
    # Test A, B, F (missing data)
    result = calculate_risk(
        sif_level=None,
        sif_potential=None,
        barrier_status="verified",
        has_lsr=False,
        precursor_priority=None
    )
    settings = get_settings()
    assert result["score"] == settings.risk_score_min
    assert result["priority"] == "LOW"


def test_score_maximum():
    # Test B: max score
    result = calculate_risk(
        sif_level=SIFLevel.HIGH,
        sif_potential=True,
        barrier_status="failed",
        has_lsr=True,
        precursor_priority="CRITICAL"
    )
    assert result["score"] == 100
    assert result["priority"] == "CRITICAL"


def test_component_calculation():
    # Test C, K (SIF relevance), L (LSR relevance), M (precursor)
    result = calculate_risk(
        sif_level=SIFLevel.MEDIUM,  # 20
        sif_potential=True,
        barrier_status="not verified",  # 15
        has_lsr=True,  # 15
        precursor_priority="HIGH"  # 20
    )
    assert result["score"] == 70  # 20 + 15 + 15 + 20
    assert result["priority"] == "HIGH"
    
    components = {c["name"]: c["score"] for c in result["components"]}
    assert components["Consequence"] == 20
    assert components["Control Degradation"] == 15
    assert components["Life-Saving Rule"] == 15
    assert components["Precursor Recurrence"] == 20


def test_control_states():
    # Test G, H, I, J
    
    # Unknown (G)
    res_unknown = calculate_risk(None, False, "unknown", False, None)
    assert res_unknown["score"] == 10  # Because max(1, 10) = 10
    
    # Failed (H)
    res_failed = calculate_risk(None, False, "failed", False, None)
    assert res_failed["score"] == 30 
    
    # Bypassed (I)
    res_bypassed = calculate_risk(None, False, "bypassed", False, None)
    assert res_bypassed["score"] == 30 
    
    # Verified (J)
    res_verified = calculate_risk(None, False, "verified", False, None)
    assert res_verified["score"] == 1
