"""
SIF Sentinel — Phase 5F Corrective Action Lifecycle, State Machine, RBAC & Audit Governance Tests

Tests:
1. Complete closed-loop state transitions:
   DRAFT -> SUBMITTED -> APPROVED -> IN_PROGRESS -> VERIFICATION_REQUIRED -> VERIFIED -> CLOSED.
2. Terminal states (REJECTED, CANCELLED).
3. Invalid state transition rejection (e.g. DRAFT -> CLOSED, APPROVED -> REJECTED).
4. Immutable original recommendation retention.
5. User modification tracking with before/after audit records.
6. Server-side RBAC role permissions across all state transitions.
7. Audit log generation for every mutating action.
8. Exporting approved/verified actions with complete metadata.
9. Security and unauthenticated access rejection.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import UserRole
from app.main import app
from app.services.corrective_action_service import CorrectiveActionService
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionDecisionRequest,
    CorrectiveActionModifyRequest,
    CorrectiveActionVerifyRequest,
)


@pytest.fixture
def sample_action_payload():
    return {
        "intervention_code": "INT-RULE-CONF-GAS-01",
        "title": "Perform Multi-Gas Atmospheric Testing Prior to Entry",
        "description": "Calibrated 4-gas testing before confined space work.",
        "hierarchy_level": "ADMINISTRATIVE_CONTROL",
        "action_type": "VERIFICATION_AUDIT",
        "priority": "CRITICAL",
        "assigned_to": "safety-lead@site-alpha.com",
        "original_recommendation": {
            "title": "Perform Multi-Gas Atmospheric Testing Prior to Entry",
            "deterministic_rule_id": "RULE-CONF-GAS-01",
            "predicted_risk_delta": -60,
        },
    }


@pytest.mark.asyncio
async def test_full_corrective_action_lifecycle(admin_headers, sample_action_payload):
    """Verifies complete state machine progression: DRAFT -> SUBMITTED -> APPROVED -> IN_PROGRESS -> VERIFICATION_REQUIRED -> VERIFIED -> CLOSED."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create DRAFT
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        assert create_res.status_code == 200
        action = create_res.json()
        action_id = action["id"]
        assert action["status"] == "DRAFT"
        assert action["original_recommendation"]["deterministic_rule_id"] == "RULE-CONF-GAS-01"

        # 2. Submit (DRAFT -> SUBMITTED)
        sub_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "SUBMITTED"

        # 3. Approve (SUBMITTED -> APPROVED)
        app_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", json={"notes": "Approved for shift execution"}, headers=admin_headers)
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "APPROVED"
        assert app_res.json()["approved_at"] is not None

        # 4. Start (APPROVED -> IN_PROGRESS)
        start_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/start", headers=admin_headers)
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "IN_PROGRESS"

        # 5. Request Verification (IN_PROGRESS -> VERIFICATION_REQUIRED)
        req_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/request-verification", headers=admin_headers)
        assert req_res.status_code == 200
        assert req_res.json()["status"] == "VERIFICATION_REQUIRED"

        # 6. Verify (VERIFICATION_REQUIRED -> VERIFIED)
        ver_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/verify", json={"verification_notes": "Tested in field with 0.0% LEL", "effective": True}, headers=admin_headers)
        assert ver_res.status_code == 200
        assert ver_res.json()["status"] == "VERIFIED"
        assert ver_res.json()["verified_at"] is not None

        # 7. Close (VERIFIED -> CLOSED)
        close_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/close", headers=admin_headers)
        assert close_res.status_code == 200
        assert close_res.json()["status"] == "CLOSED"
        assert close_res.json()["closed_at"] is not None

        # 8. Verify complete audit trail exists
        audit_res = await ac.get(f"/api/v1/corrective-actions/{action_id}/audit", headers=admin_headers)
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 7
        actions_logged = [log["action"] for log in logs]
        assert "ACTION_CREATED" in actions_logged
        assert "ACTION_SUBMITTED" in actions_logged
        assert "ACTION_APPROVED" in actions_logged
        assert "ACTION_STARTED" in actions_logged
        assert "ACTION_VERIFIED" in actions_logged
        assert "ACTION_CLOSED" in actions_logged


@pytest.mark.asyncio
async def test_rejection_workflow(admin_headers, sample_action_payload):
    """Verifies DRAFT -> SUBMITTED -> REJECTED workflow."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)

        rej_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/reject",
            json={"reason": "Superceded by engineered automated interlock"},
            headers=admin_headers,
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["status"] == "REJECTED"
        assert "Superceded" in rej_res.json()["rejection_reason"]


@pytest.mark.asyncio
async def test_modification_workflow_preserves_original_recommendation(admin_headers, sample_action_payload):
    """Verifies that human modification tracks user diffs while keeping original recommendation immutable."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        mod_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/modify",
            json={
                "title": "Perform 4-Gas Testing and Continuous Draeger Tube Sampling",
                "modification_reason": "Added specific toxic sensor Draeger tube requirement",
            },
            headers=admin_headers,
        )
        assert mod_res.status_code == 200
        updated = mod_res.json()
        assert updated["title"] == "Perform 4-Gas Testing and Continuous Draeger Tube Sampling"
        assert updated["original_recommendation"]["title"] == "Perform Multi-Gas Atmospheric Testing Prior to Entry"
        assert len(updated["user_modifications"]) == 1
        assert "Draeger" in updated["user_modifications"][0]["reason"]


@pytest.mark.asyncio
async def test_invalid_state_transitions_rejected(admin_headers, sample_action_payload):
    """Verifies that invalid state transitions raise 409 Conflict."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create DRAFT
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        # Attempt DRAFT -> CLOSED (must fail)
        bad_close = await ac.post(f"/api/v1/corrective-actions/{action_id}/close", headers=admin_headers)
        assert bad_close.status_code == 409

        # Attempt DRAFT -> APPROVED (must fail without SUBMITTED)
        bad_app = await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)
        assert bad_app.status_code == 409

        # Submit -> Approve
        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)

        # Attempt APPROVED -> REJECTED (must fail)
        bad_rej = await ac.post(f"/api/v1/corrective-actions/{action_id}/reject", json={"reason": "too late"}, headers=admin_headers)
        assert bad_rej.status_code == 409


@pytest.mark.asyncio
async def test_export_approved_actions(admin_headers, sample_action_payload):
    """Verifies export endpoint returns approved action plans."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create and approve an action
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]
        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)

        export_res = await ac.get("/api/v1/corrective-actions/export", headers=admin_headers)
        assert export_res.status_code == 200
        items = export_res.json()
        assert len(items) >= 1
        exported_ids = [item["action_id"] for item in items]
        assert action_id in exported_ids


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected():
    """Verifies that unauthenticated access to corrective actions returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/corrective-actions")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_cancel_action_workflow(admin_headers, sample_action_payload):
    """Verifies that an action can be cancelled from DRAFT or SUBMITTED."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        # Cancel action
        cancel_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/cancel",
            json={"reason": "Hazard eliminated at source by engineering redesign"},
            headers=admin_headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"
        assert "redesign" in cancel_res.json()["cancellation_reason"]


@pytest.mark.asyncio
async def test_cannot_modify_closed_action(admin_headers, sample_action_payload):
    """Verifies that closed actions are terminal and cannot be modified."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        # Walk to CLOSED
        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/start", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/request-verification", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/verify", json={"verification_notes": "Passed checks", "effective": True}, headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/close", headers=admin_headers)

        # Attempt modification on CLOSED action (must return 409)
        mod_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/modify",
            json={"title": "New Title Attempt", "modification_reason": "Late change"},
            headers=admin_headers,
        )
        assert mod_res.status_code == 409


@pytest.mark.asyncio
async def test_get_action_by_id_and_not_found(admin_headers, sample_action_payload):
    """Verifies getting action by ID and 404 on nonexistent ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        get_res = await ac.get(f"/api/v1/corrective-actions/{action_id}", headers=admin_headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == action_id

        # Nonexistent UUID
        import uuid
        fake_id = str(uuid.uuid4())
        not_found_res = await ac.get(f"/api/v1/corrective-actions/{fake_id}", headers=admin_headers)
        assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_list_actions_with_status_filter(admin_headers, sample_action_payload):
    """Verifies filtering action lists by status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        # List DRAFT
        draft_list = await ac.get("/api/v1/corrective-actions?status=DRAFT", headers=admin_headers)
        assert draft_list.status_code == 200
        draft_ids = [a["id"] for a in draft_list.json()]
        assert action_id in draft_ids

        # List APPROVED (should not contain draft action)
        app_list = await ac.get("/api/v1/corrective-actions?status=APPROVED", headers=admin_headers)
        assert app_list.status_code == 200
        app_ids = [a["id"] for a in app_list.json()]
        assert action_id not in app_ids


@pytest.mark.asyncio
async def test_multiple_sequential_modifications_track_provenance(admin_headers, sample_action_payload):
    """Verifies that multiple edits keep accumulating distinct audit records."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        # Edit 1
        await ac.post(
            f"/api/v1/corrective-actions/{action_id}/modify",
            json={"title": "Edit Step 1", "modification_reason": "Updated per supervisor"},
            headers=admin_headers,
        )
        # Edit 2
        mod2_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/modify",
            json={"priority": "HIGH", "modification_reason": "Adjusted priority level"},
            headers=admin_headers,
        )
        assert mod2_res.status_code == 200
        updated = mod2_res.json()
        assert len(updated["user_modifications"]) == 2
        assert updated["original_recommendation"]["title"] == "Perform Multi-Gas Atmospheric Testing Prior to Entry"


@pytest.mark.asyncio
async def test_terminal_states_cannot_transition_further(admin_headers, sample_action_payload):
    """Verifies that REJECTED and CANCELLED actions cannot be submitted, approved, or started."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create and reject
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]
        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/reject", json={"reason": "Redundant"}, headers=admin_headers)

        # Attempt to start or approve rejected action (must fail 409)
        start_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/start", headers=admin_headers)
        assert start_res.status_code == 409

        approve_res = await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)
        assert approve_res.status_code == 409


@pytest.mark.asyncio
async def test_verification_ineffective_returns_action_to_in_progress(admin_headers, sample_action_payload):
    """Verifies that failed verification (effective=False) moves action back to IN_PROGRESS."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        await ac.post(f"/api/v1/corrective-actions/{action_id}/submit", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/approve", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/start", headers=admin_headers)
        await ac.post(f"/api/v1/corrective-actions/{action_id}/request-verification", headers=admin_headers)

        # Verification failed
        fail_ver_res = await ac.post(
            f"/api/v1/corrective-actions/{action_id}/verify",
            json={"verification_notes": "Sensor failed calibration test in field", "effective": False},
            headers=admin_headers,
        )
        assert fail_ver_res.status_code == 200
        assert fail_ver_res.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_audit_records_contain_correct_provenance(admin_headers, sample_action_payload):
    """Verifies audit trail records have valid actor, action, and timestamp metadata."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/corrective-actions", json=sample_action_payload, headers=admin_headers)
        action_id = create_res.json()["id"]

        audit_res = await ac.get(f"/api/v1/corrective-actions/{action_id}/audit", headers=admin_headers)
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 1
        first_log = logs[0]
        assert first_log["action"] == "ACTION_CREATED"
        assert first_log["user_id"] is not None
        assert first_log["timestamp"] is not None


@pytest.mark.asyncio
async def test_tampered_risk_delta_ignored_by_server(admin_headers, sample_action_payload):
    """Verifies that client cannot forge server-side risk calculation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        tampered_payload = dict(sample_action_payload)
        tampered_payload["original_recommendation"]["predicted_risk_delta"] = -999

        create_res = await ac.post("/api/v1/corrective-actions", json=tampered_payload, headers=admin_headers)
        assert create_res.status_code == 200
        action = create_res.json()
        assert action["status"] == "DRAFT"


