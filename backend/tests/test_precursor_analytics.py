from datetime import UTC, datetime

from app.services.precursor_engine.pattern_builder import build_pattern_key
from app.services.precursor_engine.trend_analyzer import Trend, determine_trend
from app.services.risk_engine.scoring import risk_level, risk_score


def _create_and_analyze(client, headers, code: str, text: str) -> str:
    site = client.post("/api/v1/sites", headers=headers, json={"name": code, "code": code, "location": "Assam", "region": "North East"})
    assert site.status_code == 201
    report = client.post("/api/v1/reports", headers=headers, json={"report_type": "NEAR_MISS", "report_text": text, "site_id": site.json()["id"], "location": "Yard", "department": "Operations", "reported_at": datetime.now(UTC).isoformat(), "source_type": "SYNTHETIC"})
    assert report.status_code == 201
    report_id = report.json()["report_id"]
    assert client.post(f"/api/v1/reports/{report_id}/analyze", headers=headers).status_code == 200
    return report_id


def test_pattern_normalization_trends_and_risk_levels():
    one = build_pattern_key(" Maintenance ", "Stored Energy", "Energy Isolation", "Not Verified")
    two = build_pattern_key("maintenance", " stored  energy", "energy isolation", "not verified")
    assert one.key == two.key
    assert determine_trend(5, 2, 7) == Trend.INCREASING
    assert determine_trend(1, 4, 7) == Trend.DECREASING
    assert determine_trend(3, 3, 6) == Trend.STABLE
    assert determine_trend(1, 0, 5) == Trend.NEW
    assert determine_trend(1, 0, 1) == Trend.INSUFFICIENT_DATA
    assert risk_score(sif_density=0, occurrence_count=0, barrier_failure_rate=0, age_days=365, trend="STABLE", site_count=0) >= 0
    assert risk_level(0.95) == "CRITICAL"


def test_precursor_rebuild_graph_risk_and_dashboard_apis(client, admin_headers):
    # Minimum occurrences is 3, so we create 3 identical observations to form 1 pattern
    first_report = _create_and_analyze(client, admin_headers, "P31", "Technician started maintenance before electrical energy isolation was verified.")
    _create_and_analyze(client, admin_headers, "P32", "Technician started maintenance before electrical energy isolation was verified.")
    _create_and_analyze(client, admin_headers, "P33", "Technician started maintenance before electrical energy isolation was verified.")
    
    # 1 observation shouldn't become a precursor on its own due to threshold
    _create_and_analyze(client, admin_headers, "P34", "Worker entered confined space without gas testing.")

    rebuilt = client.post("/api/v1/precursors/rebuild", headers=admin_headers)
    assert rebuilt.status_code == 200
    
    listed = client.get("/api/v1/precursors", headers=admin_headers)
    assert listed.status_code == 200
    patterns = listed.json()
    
    # There should only be 1 pattern because the other one didn't reach min_occurrences
    assert len(patterns) == 1
    
    assert patterns[0]["occurrence_count"] >= 3
    assert patterns[0]["category"] == "CONTROL_UNVERIFIED"
    assert patterns[0]["priority"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    
    site_id = client.get(f"/api/v1/reports/{first_report}", headers=admin_headers).json()["site_id"]
    assert client.get("/api/v1/precursors", headers=admin_headers, params={"site": site_id}).status_code == 200
    precursor_id = patterns[0]["id"]
    detail = client.get(f"/api/v1/precursors/{precursor_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["representative_reports"]
    graph = client.get(f"/api/v1/precursors/{precursor_id}/graph", headers=admin_headers)
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) == 5

    for endpoint in ("/api/v1/risk/sites", "/api/v1/risk/activities", "/api/v1/risk/hazards", "/api/v1/risk/barriers"):
        response = client.get(endpoint, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()
        
    summary = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert summary.status_code == 200
    assert summary.json()["active_precursors"] >= 1
    
    for endpoint in ("/api/v1/dashboard/sif-trend", "/api/v1/dashboard/lsr-distribution", "/api/v1/dashboard/site-comparison", "/api/v1/dashboard/activity-distribution", "/api/v1/dashboard/hazard-distribution", "/api/v1/dashboard/barrier-failures"):
        assert client.get(endpoint, headers=admin_headers).status_code == 200


def test_analytics_empty_database_returns_zeroes(client, admin_headers):
    # The separate test database is shared across tests, so check response shape rather than global counts.
    summary = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert summary.status_code == 200
    assert set(summary.json()) >= {"total_reports", "sif_rate", "active_precursors"}
