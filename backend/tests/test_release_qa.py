"""Final release API-contract and security smoke tests."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog


def test_openapi_exposes_all_release_domains(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in (
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/reports",
        "/api/v1/reviews",
        "/api/v1/precursors",
        "/api/v1/risk/sites",
        "/api/v1/interventions",
    ):
        assert path in paths


def test_malformed_bearer_token_is_a_sanitized_401(client):
    response = client.get("/api/v1/reports", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert "traceback" not in str(body).lower()


def test_report_to_intervention_review_to_audit_flow(client, admin_headers):
    code = f"REL-{uuid4().hex[:8]}"
    site = client.post(
        "/api/v1/sites",
        headers=admin_headers,
        json={"name": code, "code": code, "location": "Synthetic", "region": "Demo"},
    )
    assert site.status_code == 201
    report = client.post(
        "/api/v1/reports",
        headers=admin_headers,
        json={
            "report_type": "NEAR_MISS",
            "report_text": "Technician started maintenance before energy isolation was verified.",
            "site_id": site.json()["id"],
            "location": "Synthetic demonstration area",
            "department": "Maintenance",
            "reported_at": datetime.now(UTC).isoformat(),
            "source_type": "SYNTHETIC",
        },
    )
    assert report.status_code == 201
    report_id = report.json()["report_id"]
    analysis = client.post(f"/api/v1/reports/{report_id}/analyze", headers=admin_headers)
    assert analysis.status_code == 200
    interventions = client.get(
        "/api/v1/interventions", headers=admin_headers, params={"report_id": report_id}
    )
    assert interventions.status_code == 200
    recommendation = interventions.json()[0]
    reviewed = client.post(
        f"/api/v1/interventions/{recommendation['id']}/review",
        headers=admin_headers,
        json={"decision": "ACCEPTED", "reviewer_comments": "Synthetic demo review"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "ACCEPTED"

    async def verify_audit():
        async with SessionLocal() as db:
            audit = await db.scalar(
                select(AuditLog).where(AuditLog.action == "INTERVENTION_ACCEPTED")
            )
            assert audit is not None

    asyncio.run(verify_audit())
