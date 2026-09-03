from app.services.nlp.analysis_pipeline import analyze_text


def test_verified_control_does_not_fail():
    """
    Test that an explicitly verified control ('isolation was verified')
    does not get flagged as a failure just because the keyword 'isolation' exists.
    """
    text = "Before maintenance, the energy isolation was verified by the competent person."
    result = analyze_text(text)
    
    assert result.barrier == "Energy Isolation"
    assert result.barrier_status == "EFFECTIVE"
    assert "explicitly verified" in result.explanation
    # It should not flag a SIF rule failure since the barrier was effective
    # But it might be low or non-SIF depending on classifier. 
    # At a minimum, it shouldn't confidently flag the rule as failed.
    # Without strong failure signals, rule mapping should be none or low confidence.
    
def test_unverified_control_fails():
    """
    Test that a negated verification ('isolation was not verified')
    is correctly flagged as a failure.
    """
    text = "During maintenance, the energy isolation was not verified, leading to a shock."
    result = analyze_text(text)
    
    assert result.barrier == "Energy Isolation"
    assert result.barrier_status == "FAILED"
    assert result.barrier_failure == "not verified"
    assert "NOT verified" in result.explanation
    
def test_missing_control_fails():
    """
    Test that a missing control ('without isolation') is correctly flagged.
    """
    text = "The worker proceeded with maintenance without energy isolation."
    result = analyze_text(text)
    
    assert result.barrier == "Energy Isolation"
    assert result.barrier_status == "FAILED"
    assert result.barrier_failure == "not performed"
    assert "without Energy Isolation" in result.explanation
    
def test_ambiguous_control_forces_review():
    """
    Test that a control mentioned with ambiguous/unknown verification status
    forces a manual review.
    """
    text = "The lockout procedure was discussed prior to maintenance, but the worker proceeded."
    result = analyze_text(text)
    
    assert result.barrier == "Lockout Tagout"
    assert result.barrier_status == "UNKNOWN"
    assert result.review_required is True
    assert "ambiguous or unknown verification state" in result.explanation
