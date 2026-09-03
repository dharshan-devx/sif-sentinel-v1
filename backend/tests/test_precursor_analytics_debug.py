from datetime import UTC, datetime
from app.services.precursor_engine.pattern_builder import build_pattern_key
from app.services.precursor_engine.trend_analyzer import Trend, determine_trend
from app.services.risk_engine.scoring import aggregate_risk_level, aggregate_risk_score

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

def test_precursor_rebuild_graph_risk_and_dashboard_apis(client, admin_headers):
    first_report = _create_and_analyze(client, admin_headers, "P31", "Technician started maintenance before electrical energy isolation was verified.")
    _create_and_analyze(client, admin_headers, "P32", "Technician started maintenance before electrical energy isolation was verified.")
    _create_and_analyze(client, admin_headers, "P33", "Technician started maintenance before electrical energy isolation was verified.")
    _create_and_analyze(client, admin_headers, "P34", "Worker entered confined space without gas testing.")
