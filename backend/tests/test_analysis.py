import asyncio
from datetime import UTC, datetime

from app.core.constants import ReportStatus
from app.db.session import SessionLocal
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.review import Review
from app.services.nlp.analysis_pipeline import analyze_text
from app.services.nlp.preprocessing import preprocess_text


def test_preprocessing_preserves_source_and_normalizes_unicode():
    result = preprocess_text("  Worker\u00a0entered   confined space. ")
    assert result.original_text == "  Worker\u00a0entered   confined space. "
    assert result.normalized_text == "worker entered confined space."
    assert result.tokens == ["worker", "entered", "confined", "space"]


def test_controlled_pipeline_examples():
    confined = analyze_text("Worker entered confined space without gas testing.")
    assert confined.sif_level.value == "HIGH"
    assert confined.activity == "Confined Space Work"
    assert confined.barrier == "Gas Testing"
    assert confined.life_saving_rule == "Confined Space"
    assert confined.evidence_span == "Worker entered confined space without gas testing."

    energy = analyze_text("Technician started maintenance before energy isolation was verified.")
    assert energy.sif_level.value == "HIGH"
    assert energy.hazard == "Stored Energy"
    assert energy.barrier_failure == "not verified"
    assert energy.life_saving_rule == "Energy Isolation"

    lifting = analyze_text("Worker stood below a suspended load.")
    assert lifting.hazard == "Suspended Load"
    assert lifting.life_saving_rule == "Line of Fire"

    ambiguous = analyze_text("Maintenance activity occurred near equipment.")
    assert ambiguous.review_required is True


def _create_report(client, headers, code: str, text: str) -> str:
    site = client.post("/api/v1/sites", headers=headers, json={"name": code, "code": code, "location": "Assam", "region": "North East"})
    assert site.status_code == 201
    response = client.post("/api/v1/reports", headers=headers, json={"report_type": "NEAR_MISS", "report_text": text, "site_id": site.json()["id"], "location": "Yard", "department": "Operations", "reported_at": datetime.now(UTC).isoformat(), "source_type": "SYNTHETIC"})
    assert response.status_code == 201
    return response.json()["report_id"]


def test_analysis_endpoint_persists_prediction_and_review(client, admin_headers):
    report_id = _create_report(client, admin_headers, "AN1", "Technician started maintenance before energy isolation was verified.")
    response = client.post(f"/api/v1/reports/{report_id}/analyze", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"]
    assert body["life_saving_rule"] == "Energy Isolation"
    assert body["review_required"] is False

    async def verify():
        async with SessionLocal() as db:
            report = await db.scalar(__import__("sqlalchemy").select(Report).where(Report.report_id == report_id))
            assert report.status == ReportStatus.ANALYZED
            assert await db.scalar(__import__("sqlalchemy").select(ReportAnalysis).where(ReportAnalysis.report_id == report.id))
    asyncio.run(verify())

    low_report = _create_report(client, admin_headers, "AN2", "Maintenance activity occurred near equipment.")
    low = client.post(f"/api/v1/reports/{low_report}/analyze", headers=admin_headers)
    assert low.status_code == 200
    assert low.json()["review_required"] is True

    async def verify_review():
        async with SessionLocal() as db:
            report = await db.scalar(__import__("sqlalchemy").select(Report).where(Report.report_id == low_report))
            assert report.status == ReportStatus.REVIEW_REQUIRED
            assert await db.scalar(__import__("sqlalchemy").select(Review).where(Review.report_id == report.id))
    asyncio.run(verify_review())


def test_direct_analysis_and_actual_metrics_api(client, admin_headers):
    direct = client.post("/api/v1/analyze", headers=admin_headers, json={"text": "Worker stood below a suspended load."})
    assert direct.status_code == 200
    assert direct.json()["analysis_id"] is None
    metrics = client.get("/api/v1/models/sif-tfidf-logreg/metrics", headers=admin_headers)
    assert metrics.status_code == 200
    assert "confusion_matrix" in metrics.json()
