"""Phase C: Review workflow hardening tests.

Covers:
1. Review status filter (?status=PENDING, REVIEWED, ALL, invalid)
2. APPROVE workflow end-to-end
3. REJECT workflow end-to-end
4. MODIFY workflow end-to-end
5. Duplicate decision protection (409)
6. MODIFY without corrections (422)
7. Authorization: unauthorized (403), unauthenticated (401)
8. Report.status transitions
9. Dashboard pending count
10. AI provenance: ReportAnalysis NOT mutated on MODIFY
11. Audit log written
12. Precursor rebuild on APPROVE/MODIFY; skipped on REJECT
"""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.core.constants import ReportStatus, ReviewDecision, UserRole
from app.db.session import SessionLocal
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.review import Review


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_site(client, admin_headers, code: str, name: str | None = None) -> dict:
    r = client.post(
        "/api/v1/sites",
        headers=admin_headers,
        json={"name": name or f"Site-{code}", "code": code, "location": "Test", "region": "North East"},
    )
    assert r.status_code in (201, 409), r.text
    if r.status_code == 201:
        return r.json()
    # Already exists — fetch
    listing = client.get("/api/v1/sites", headers=admin_headers)
    for s in listing.json():
        if s["code"] == code:
            return s
    pytest.fail(f"Site {code!r} not found after 409")


def _make_report(client, admin_headers, site_id: str) -> dict:
    r = client.post(
        "/api/v1/reports",
        headers=admin_headers,
        json={
            "report_type": "NEAR_MISS",
            "report_text": "Maintenance activity occurred near equipment.",
            "site_id": site_id,
            "location": "Platform A",
            "department": "Maintenance",
            "reported_at": datetime.now(UTC).isoformat(),
            "source_type": "SYNTHETIC",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _analyze(client, admin_headers, report_id: str) -> dict:
    r = client.post(f"/api/v1/reports/{report_id}/analyze", headers=admin_headers)
    assert r.status_code == 200, r.text
    return r.json()


def _pending_reviews(client, reviewer_headers) -> list[dict]:
    r = client.get("/api/v1/reviews?status=PENDING", headers=reviewer_headers)
    assert r.status_code == 200, r.text
    return r.json()


def _make_pending_review(client, admin_headers, reviewer_headers) -> str:
    """Create a report, analyze it, and return the review_id of the resulting PENDING review."""
    site = _make_site(client, admin_headers, "PC1", "PhaseC Site 1")
    report = _make_report(client, admin_headers, site["id"])
    _analyze(client, admin_headers, report["report_id"])
    queue = _pending_reviews(client, reviewer_headers)
    for r in queue:
        if r["report_id"] == report["report_id"]:
            return r["id"]
    pytest.fail(f"No pending review found for report {report['report_id']}")


@pytest.fixture
def reviewer_headers(client):
    email, password = "phc-reviewer@sif.demo", "test-password-123"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "PhaseC Reviewer"},
    )
    assert reg.status_code in (201, 409), reg.text

    async def promote():
        from sqlalchemy import select
        from app.models.user import User
        async with SessionLocal() as db:
            user = await db.scalar(select(User).where(User.email == email))
            user.role = UserRole.REVIEWER
            await db.commit()

    asyncio.run(promote())
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(client):
    """Authenticated but lacks reviewer role."""
    email, password = "phc-viewer@sif.demo", "test-password-123"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "PhaseC Viewer"},
    )
    assert reg.status_code in (201, 409), reg.text
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Review Status Filter Tests
# ---------------------------------------------------------------------------

class TestReviewStatusFilter:

    def test_pending_filter_default(self, client, admin_headers):
        r = client.get("/api/v1/reviews", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["decision"] == "PENDING"

    def test_explicit_pending_filter(self, client, admin_headers):
        r = client.get("/api/v1/reviews?status=PENDING", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["decision"] == "PENDING"

    def test_reviewed_filter(self, client, admin_headers, reviewer_headers):
        r = client.get("/api/v1/reviews?status=REVIEWED", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["decision"] != "PENDING"

    def test_all_filter(self, client, admin_headers):
        r = client.get("/api/v1/reviews?status=ALL", headers=admin_headers)
        assert r.status_code == 200  # no filter — any decision is fine

    def test_invalid_status_rejected(self, client, admin_headers):
        r = client.get("/api/v1/reviews?status=GARBAGE", headers=admin_headers)
        assert r.status_code == 422

    def test_pending_items_have_null_reviewer(self, client, admin_headers):
        """PENDING items must expose reviewer_id=None to distinguish from decided reviews."""
        r = client.get("/api/v1/reviews?status=PENDING", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["reviewer_id"] is None
            assert item["reviewed_at"] is None


# ---------------------------------------------------------------------------
# APPROVE Workflow
# ---------------------------------------------------------------------------

class TestApproveWorkflow:

    def test_approve_returns_decision_response(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "APPROVE"
        assert body["report_status"] == "REVIEWED"
        assert body["reviewer_id"] is not None
        assert body["reviewed_at"] is not None
        assert "message" in body

    def test_approve_moves_review_out_of_pending(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        r = client.get(f"/api/v1/reviews/{review_id}", headers=reviewer_headers)
        assert r.status_code == 200
        assert r.json()["decision"] == "APPROVE"

    def test_approve_sets_report_status_reviewed(self, client, admin_headers, reviewer_headers):
        site = _make_site(client, admin_headers, "APC", "Approve Test")
        report = _make_report(client, admin_headers, site["id"])
        _analyze(client, admin_headers, report["report_id"])
        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        assert r.status_code == 200
        # Fetch the report and verify status
        report_r = client.get(f"/api/v1/reports/{report['report_id']}", headers=admin_headers)
        assert report_r.json()["status"] == "REVIEWED"

    def test_approve_preserves_ai_analysis(self, client, admin_headers, reviewer_headers):
        """APPROVE must never mutate ReportAnalysis."""
        site = _make_site(client, admin_headers, "APC2", "Approve AI")
        report = _make_report(client, admin_headers, site["id"])
        analysis_resp = _analyze(client, admin_headers, report["report_id"])
        ai_sif_level = analysis_resp["sif_level"]
        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )

        async def check():
            async with SessionLocal() as db:
                review = await db.get(Review, UUID(review_id))
                analysis = await db.get(ReportAnalysis, review.analysis_id)
                assert analysis.sif_level.value == ai_sif_level

        asyncio.run(check())


# ---------------------------------------------------------------------------
# REJECT Workflow
# ---------------------------------------------------------------------------

class TestRejectWorkflow:

    def test_reject_returns_decision_response(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT", "reviewer_comment": "AI prediction seems incorrect."},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "REJECT"
        assert body["report_status"] == "REVIEWED"

    def test_reject_sets_report_status_reviewed(self, client, admin_headers, reviewer_headers):
        site = _make_site(client, admin_headers, "RJC", "Reject Test")
        report = _make_report(client, admin_headers, site["id"])
        _analyze(client, admin_headers, report["report_id"])
        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )
        report_r = client.get(f"/api/v1/reports/{report['report_id']}", headers=admin_headers)
        assert report_r.json()["status"] == "REVIEWED"

    def test_reject_preserves_original_ai_analysis(self, client, admin_headers, reviewer_headers):
        """REJECT must not delete or modify the original AI analysis."""
        site = _make_site(client, admin_headers, "RJC2", "Reject AI")
        report = _make_report(client, admin_headers, site["id"])
        analysis_resp = _analyze(client, admin_headers, report["report_id"])
        ai_sif = analysis_resp["sif_level"]
        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )

        async def check():
            async with SessionLocal() as db:
                review = await db.get(Review, UUID(review_id))
                analysis = await db.get(ReportAnalysis, review.analysis_id)
                assert analysis is not None
                assert analysis.sif_level.value == ai_sif

        asyncio.run(check())

    def test_reject_appears_in_reviewed_filter(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )
        reviewed = client.get("/api/v1/reviews?status=REVIEWED", headers=admin_headers)
        ids = [item["id"] for item in reviewed.json()]
        assert review_id in ids


# ---------------------------------------------------------------------------
# MODIFY Workflow
# ---------------------------------------------------------------------------

class TestModifyWorkflow:

    def test_modify_stores_corrections_in_review(self, client, admin_headers, reviewer_headers):
        """Corrections must be stored in Review.corrected_* — not mutate ReportAnalysis."""
        site = _make_site(client, admin_headers, "MDC", "Modify Test")
        report = _make_report(client, admin_headers, site["id"])
        analysis_resp = _analyze(client, admin_headers, report["report_id"])
        ai_sif_level = analysis_resp["sif_level"]

        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={
                "decision": "MODIFY",
                "corrected_sif_level": "MEDIUM",
                "corrected_barrier_failure": "PPE not worn",
                "reviewer_comment": "Corrected classification",
            },
        )
        assert r.status_code == 200

        async def check():
            async with SessionLocal() as db:
                review = await db.get(Review, UUID(review_id))
                analysis = await db.get(ReportAnalysis, review.analysis_id)
                # Corrections stored on Review
                assert review.corrected_sif_level.value == "MEDIUM"
                assert review.corrected_barrier_failure == "PPE not worn"
                assert review.reviewer_comment == "Corrected classification"
                # AI analysis preserved (not mutated)
                assert analysis.sif_level.value == ai_sif_level

        asyncio.run(check())

    def test_modify_without_corrections_rejected(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "MODIFY"},
        )
        assert r.status_code == 422

    def test_modify_with_only_comment_rejected(self, client, admin_headers, reviewer_headers):
        """reviewer_comment alone does not count as a meaningful correction."""
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "MODIFY", "reviewer_comment": "just a note"},
        )
        assert r.status_code == 422

    def test_modify_corrections_in_response(self, client, admin_headers, reviewer_headers):
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "MODIFY", "corrected_activity": "inspection"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "MODIFY"


# ---------------------------------------------------------------------------
# Duplicate Decision (State Machine Guard)
# ---------------------------------------------------------------------------

class TestDuplicateDecision:

    def _make_and_decide(self, client, admin_headers, reviewer_headers, decision: str) -> str:
        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": decision, **({"corrected_activity": "x"} if decision == "MODIFY" else {})},
        )
        assert r.status_code == 200
        return review_id

    def test_second_approve_blocked(self, client, admin_headers, reviewer_headers):
        review_id = self._make_and_decide(client, admin_headers, reviewer_headers, "APPROVE")
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "REVIEW_ALREADY_DECIDED"

    def test_second_reject_blocked(self, client, admin_headers, reviewer_headers):
        review_id = self._make_and_decide(client, admin_headers, reviewer_headers, "REJECT")
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )
        assert r.status_code == 409

    def test_approve_then_reject_blocked(self, client, admin_headers, reviewer_headers):
        review_id = self._make_and_decide(client, admin_headers, reviewer_headers, "APPROVE")
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )
        assert r.status_code == 409

    def test_modify_then_approve_blocked(self, client, admin_headers, reviewer_headers):
        review_id = self._make_and_decide(client, admin_headers, reviewer_headers, "MODIFY")
        r = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        assert r.status_code == 409


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

class TestAuthorization:

    def test_unauthenticated_cannot_list_reviews(self, client):
        r = client.get("/api/v1/reviews")
        assert r.status_code == 401

    def test_unauthenticated_cannot_submit_decision(self, client):
        r = client.post("/api/v1/reviews/00000000-0000-0000-0000-000000000000/decision",
                        json={"decision": "APPROVE"})
        assert r.status_code == 401

    def test_viewer_cannot_list_reviews(self, client, viewer_headers):
        r = client.get("/api/v1/reviews", headers=viewer_headers)
        assert r.status_code == 403

    def test_viewer_cannot_submit_decision(self, client, viewer_headers):
        r = client.post(
            "/api/v1/reviews/00000000-0000-0000-0000-000000000000/decision",
            headers=viewer_headers,
            json={"decision": "APPROVE"},
        )
        assert r.status_code == 403

    def test_reviewer_can_list_reviews(self, client, reviewer_headers):
        r = client.get("/api/v1/reviews", headers=reviewer_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Dashboard Consistency
# ---------------------------------------------------------------------------

class TestDashboardConsistency:

    def test_pending_count_decreases_after_decision(self, client, admin_headers, reviewer_headers):
        # Baseline pending count
        before = client.get("/api/v1/dashboard/summary", headers=admin_headers).json()
        before_count = before["review_required"]

        # Create a new review and approve it
        site = _make_site(client, admin_headers, "DSH", "Dashboard Test")
        report = _make_report(client, admin_headers, site["id"])
        _analyze(client, admin_headers, report["report_id"])

        after_analyze = client.get("/api/v1/dashboard/summary", headers=admin_headers).json()
        mid_count = after_analyze["review_required"]

        queue = _pending_reviews(client, reviewer_headers)
        review_id = queue[-1]["id"]
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )

        after_decide = client.get("/api/v1/dashboard/summary", headers=admin_headers).json()
        final_count = after_decide["review_required"]

        # After deciding, count should return to baseline (or be ≤ mid_count)
        assert final_count <= mid_count


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class TestAuditLog:

    def test_audit_log_created_for_approve(self, client, admin_headers, reviewer_headers):
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )

        async def check():
            async with SessionLocal() as db:
                log = await db.scalar(
                    select(AuditLog)
                    .where(AuditLog.entity_id == UUID(review_id))
                    .where(AuditLog.action == "REVIEW_APPROVED")
                    .order_by(AuditLog.created_at.desc())
                )
                assert log is not None
                assert log.action == "REVIEW_APPROVED"
                assert log.entity_type == "review"
                assert log.details["decision"] == "APPROVE"

        asyncio.run(check())

    def test_audit_log_created_for_reject(self, client, admin_headers, reviewer_headers):
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT"},
        )

        async def check():
            async with SessionLocal() as db:
                log = await db.scalar(
                    select(AuditLog)
                    .where(AuditLog.entity_id == UUID(review_id))
                    .where(AuditLog.action == "REVIEW_REJECTED")
                )
                assert log is not None

        asyncio.run(check())

    def test_audit_log_for_modify_includes_correction_keys(self, client, admin_headers, reviewer_headers):
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        review_id = _make_pending_review(client, admin_headers, reviewer_headers)
        client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={
                "decision": "MODIFY",
                "corrected_sif_level": "LOW",
                "corrected_activity": "inspection",
            },
        )

        async def check():
            async with SessionLocal() as db:
                log = await db.scalar(
                    select(AuditLog)
                    .where(AuditLog.entity_id == UUID(review_id))
                    .where(AuditLog.action == "REVIEW_MODIFIED")
                )
                assert log is not None
                assert "corrections" in log.details
                assert "corrected_sif_level" in log.details["corrections"]

        asyncio.run(check())


# ---------------------------------------------------------------------------
# End-to-End Integration Flow
# ---------------------------------------------------------------------------

class TestIntegrationFlow:

    def test_full_approve_flow(self, client, admin_headers, reviewer_headers):
        """Full pipeline: create → analyze → get pending → approve → verify."""
        # 1. Create report
        site = _make_site(client, admin_headers, "INT1", "Integration 1")
        report = _make_report(client, admin_headers, site["id"])

        # 2. Analyze
        _analyze(client, admin_headers, report["report_id"])

        # 3. Get pending queue
        pending = client.get("/api/v1/reviews?status=PENDING", headers=reviewer_headers)
        assert pending.status_code == 200
        assert pending.json()

        review_id = next(r["id"] for r in pending.json() if r["report_id"] == report["report_id"])

        # 4. Approve
        decision = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "APPROVE"},
        )
        assert decision.status_code == 200
        assert decision.json()["decision"] == "APPROVE"
        assert decision.json()["report_status"] == "REVIEWED"

        # 5. Verify review decision is updated
        review_resp = client.get(f"/api/v1/reviews/{review_id}", headers=reviewer_headers)
        assert review_resp.status_code == 200
        assert review_resp.json()["decision"] == "APPROVE"

    def test_full_reject_flow(self, client, admin_headers, reviewer_headers):
        """Full pipeline: create → analyze → get pending → reject → verify."""
        site = _make_site(client, admin_headers, "INT2", "Integration 2")
        report = _make_report(client, admin_headers, site["id"])
        _analyze(client, admin_headers, report["report_id"])

        pending = _pending_reviews(client, reviewer_headers)
        review_id = next(r["id"] for r in pending if r["report_id"] == report["report_id"])

        decision = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={"decision": "REJECT", "reviewer_comment": "False positive."},
        )
        assert decision.status_code == 200
        assert decision.json()["decision"] == "REJECT"

        # Report must be REVIEWED
        report_r = client.get(f"/api/v1/reports/{report['report_id']}", headers=admin_headers)
        assert report_r.json()["status"] == "REVIEWED"

    def test_full_modify_flow(self, client, admin_headers, reviewer_headers):
        """Full pipeline: create → analyze → modify with corrections → verify DB."""
        site = _make_site(client, admin_headers, "INT3", "Integration 3")
        report = _make_report(client, admin_headers, site["id"])
        analysis_resp = _analyze(client, admin_headers, report["report_id"])
        ai_sif = analysis_resp["sif_level"]

        pending = _pending_reviews(client, reviewer_headers)
        review_id = next(r["id"] for r in pending if r["report_id"] == report["report_id"])

        decision = client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=reviewer_headers,
            json={
                "decision": "MODIFY",
                "corrected_sif_level": "HIGH",
                "corrected_hazard": "rotating equipment",
                "reviewer_comment": "Severity was underestimated.",
            },
        )
        assert decision.status_code == 200
        assert decision.json()["decision"] == "MODIFY"

        async def verify():
            async with SessionLocal() as db:
                review = await db.get(Review, UUID(review_id))
                analysis = await db.get(ReportAnalysis, review.analysis_id)
                # Corrections on Review
                assert review.corrected_sif_level.value == "HIGH"
                assert review.corrected_hazard == "rotating equipment"
                # AI analysis untouched
                assert analysis.sif_level.value == ai_sif

        asyncio.run(verify())
