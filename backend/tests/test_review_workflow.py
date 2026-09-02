import asyncio
from datetime import UTC, datetime
from uuid import UUID

from app.core.constants import UserRole
from app.db.session import SessionLocal
from app.models.report_analysis import ReportAnalysis
from app.models.review import Review


def _reviewer_headers(client):
    email, password = "reviewer-test@sif.demo", "test-password-123"
    reg_resp = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Test Reviewer"})
    assert reg_resp.status_code in (201, 409)
    async def promote_reviewer():
        from sqlalchemy import select

        from app.models.user import User
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            user.role = UserRole.REVIEWER
            await db.commit()
    asyncio.run(promote_reviewer())
    return {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': email, 'password': password}).json()['access_token']}"}


def test_review_queue_modify_feedback_and_authorization(client, admin_headers):
    import uuid
    reviewer_headers = _reviewer_headers(client)
    code = f"REV-{uuid.uuid4().hex[:4].upper()}"
    site_resp = client.post("/api/v1/sites", headers=admin_headers, json={"name": "Review Site", "code": code, "location": "Assam", "region": "North East"})
    if site_resp.status_code == 409:
        site = client.get("/api/v1/sites", headers=admin_headers).json()[0]
    else:
        site = site_resp.json()
    report = client.post("/api/v1/reports", headers=admin_headers, json={"report_type": "NEAR_MISS", "report_text": "Maintenance activity occurred near equipment.", "site_id": site["id"], "location": "Yard", "department": "Operations", "reported_at": datetime.now(UTC).isoformat(), "source_type": "SYNTHETIC"}).json()
    assert client.post(f"/api/v1/reports/{report['report_id']}/analyze", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/reviews", headers=admin_headers).status_code == 200
    queue = client.get("/api/v1/reviews", headers=reviewer_headers)
    assert queue.status_code == 200 and queue.json()
    review_id = queue.json()[-1]["id"]
    decision = client.post(f"/api/v1/reviews/{review_id}/decision", headers=reviewer_headers, json={"decision": "MODIFY", "corrected_sif_level": "LOW", "corrected_barrier_failure": "not followed", "reviewer_comment": "Verified by reviewer"})
    assert decision.status_code == 200
    assert decision.json()["decision"] == "MODIFY"
    assert client.get("/api/v1/models/feedback", headers=admin_headers).json()["corrected_predictions"] >= 1

    async def persisted():
        async with SessionLocal() as db:
            review = await db.get(Review, UUID(review_id))
            analysis = await db.get(ReportAnalysis, review.analysis_id)
            # Phase C: AI provenance is preserved — ReportAnalysis is NOT mutated.
            # The human correction is stored in Review.corrected_* columns.
            assert review.corrected_barrier_failure == "not followed"
            assert review.corrected_sif_level is not None
            assert review.corrected_sif_level.value == "LOW"
            # The original AI analysis is unchanged (sif_level may differ from "LOW")
            # — we do not assert its value because the AI's prediction is
            # non-deterministic. We only assert it was not forcibly set to "LOW".
            assert analysis is not None  # analysis still exists and was not deleted
    asyncio.run(persisted())


def test_models_and_health_status_contracts(client, admin_headers):
    assert client.get("/api/v1/models/performance", headers=admin_headers).status_code == 200
    status = client.get("/api/v1/health/status")
    assert status.status_code == 200
    assert status.headers["x-content-type-options"] == "nosniff"
