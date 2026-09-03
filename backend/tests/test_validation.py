"""Phase B: Input validation boundary tests.

Covers:
- POST /api/v1/reports  — report creation
- PATCH /api/v1/reports/{id} — partial update
- POST /api/v1/analyze  — direct text analysis

All limit checks are driven from settings so that changing
report_text_min_length / report_text_max_length in config automatically
adjusts the expected behaviour here.

NLP bypass test uses unittest.mock to confirm that invalid input never
reaches analyze_text() inside the pipeline.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

settings = get_settings()
MIN = settings.report_text_min_length   # currently 10
MAX = settings.report_text_max_length   # currently 20_000


def _report_payload(**overrides) -> dict:
    base = {
        "report_type": "NEAR_MISS",
        "report_text": "Worker entered confined space without gas testing.",
        "location": "Field Area",
        "department": "Operations",
        "reported_at": datetime.now(UTC).isoformat(),
        "source_type": "SYNTHETIC",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def site_id(client, admin_headers):
    """Create a validation-test site and return its UUID.

    Tolerates 409 (SITE_CODE_EXISTS) so this fixture is safe when tests
    run alongside others that share the same session-scoped database.
    """
    r = client.post(
        "/api/v1/sites",
        headers=admin_headers,
        json={"name": "Validation Test Site", "code": "VAL", "location": "Assam", "region": "North East"},
    )
    assert r.status_code in (201, 409), r.text
    if r.status_code == 201:
        return r.json()["id"]
    # Site already exists — fetch it from the list endpoint
    listing = client.get("/api/v1/sites", headers=admin_headers)
    assert listing.status_code == 200, listing.text
    for site in listing.json():
        if site["code"] == "VAL":
            return site["id"]
    pytest.fail("VAL site not found after 409 conflict")



# ---------------------------------------------------------------------------
# POST /reports — report creation
# ---------------------------------------------------------------------------

class TestReportCreateValidation:

    def test_valid_text_accepted(self, client, admin_headers, site_id):
        payload = _report_payload(site_id=site_id)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 201

    def test_empty_string_rejected(self, client, admin_headers, site_id):
        payload = _report_payload(site_id=site_id, report_text="")
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 422

    def test_whitespace_only_rejected(self, client, admin_headers, site_id):
        for bad in (" ", "   ", "\n", "\t", " \n \t "):
            payload = _report_payload(site_id=site_id, report_text=bad)
            r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
            assert r.status_code == 422, f"Expected 422 for {bad!r}, got {r.status_code}"

    def test_below_minimum_rejected(self, client, admin_headers, site_id):
        # MIN-1 stripped chars → should fail
        short = "x" * (MIN - 1)
        payload = _report_payload(site_id=site_id, report_text=short)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 422

    def test_exactly_minimum_accepted(self, client, admin_headers, site_id):
        # Exactly MIN stripped chars → should pass
        at_min = "x" * MIN
        payload = _report_payload(site_id=site_id, report_text=at_min)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 201

    def test_exactly_maximum_accepted(self, client, admin_headers, site_id):
        at_max = "x" * MAX
        payload = _report_payload(site_id=site_id, report_text=at_max)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 201

    def test_one_over_maximum_rejected(self, client, admin_headers, site_id):
        over = "x" * (MAX + 1)
        payload = _report_payload(site_id=site_id, report_text=over)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 422

    def test_very_large_input_rejected(self, client, admin_headers, site_id):
        huge = "x" * 200_000
        payload = _report_payload(site_id=site_id, report_text=huge)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 422

    def test_validation_error_has_no_stack_trace(self, client, admin_headers, site_id):
        payload = _report_payload(site_id=site_id, report_text="  ")
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 422
        body = r.json()
        # error envelope is present
        assert "error" in body
        # no traceback/internal path leakage
        text = r.text.lower()
        assert "traceback" not in text
        assert "file \"" not in text


# ---------------------------------------------------------------------------
# POST /analyze — direct text analysis
# ---------------------------------------------------------------------------

class TestAnalyzeDirectValidation:

    def test_valid_text_accepted(self, client, admin_headers):
        r = client.post(
            "/api/v1/analyze",
            headers=admin_headers,
            json={"text": "Technician started maintenance without energy isolation."},
        )
        assert r.status_code == 200

    def test_empty_string_rejected(self, client, admin_headers):
        r = client.post("/api/v1/analyze", headers=admin_headers, json={"text": ""})
        assert r.status_code == 422

    def test_whitespace_only_rejected(self, client, admin_headers):
        r = client.post("/api/v1/analyze", headers=admin_headers, json={"text": "   \n\t  "})
        assert r.status_code == 422

    def test_below_minimum_rejected(self, client, admin_headers):
        r = client.post("/api/v1/analyze", headers=admin_headers, json={"text": "x" * (MIN - 1)})
        assert r.status_code == 422

    def test_oversized_rejected(self, client, admin_headers):
        r = client.post("/api/v1/analyze", headers=admin_headers, json={"text": "x" * (MAX + 1)})
        assert r.status_code == 422

    def test_nlp_not_called_for_invalid_input(self, client, admin_headers):
        """Invalid input must be rejected before the NLP pipeline is reached."""
        with patch(
            "app.services.analysis.analysis_service.analyze_text"
        ) as mock_nlp:
            r = client.post(
                "/api/v1/analyze",
                headers=admin_headers,
                json={"text": "   "},  # whitespace-only
            )
        assert r.status_code == 422
        mock_nlp.assert_not_called()

    def test_nlp_not_called_for_oversized_input(self, client, admin_headers):
        """Oversized text must be rejected before the NLP pipeline is reached."""
        with patch(
            "app.services.analysis.analysis_service.analyze_text"
        ) as mock_nlp:
            r = client.post(
                "/api/v1/analyze",
                headers=admin_headers,
                json={"text": "x" * (MAX + 100)},
            )
        assert r.status_code == 422
        mock_nlp.assert_not_called()


# ---------------------------------------------------------------------------
# PATCH /reports/{id} — partial update
# ---------------------------------------------------------------------------

class TestReportPatchValidation:

    @pytest.fixture
    def existing_report_id(self, client, admin_headers, site_id):
        payload = _report_payload(site_id=site_id)
        r = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert r.status_code == 201
        return r.json()["report_id"]

    def test_valid_text_patch_accepted(self, client, admin_headers, existing_report_id):
        r = client.patch(
            f"/api/v1/reports/{existing_report_id}",
            headers=admin_headers,
            json={"report_text": "Updated: worker bypassed interlock on rotating equipment."},
        )
        assert r.status_code == 200

    def test_patch_without_report_text_accepted(self, client, admin_headers, existing_report_id):
        """Partial update omitting report_text must not be rejected."""
        r = client.patch(
            f"/api/v1/reports/{existing_report_id}",
            headers=admin_headers,
            json={"department": "Maintenance"},
        )
        assert r.status_code == 200

    def test_empty_string_patch_rejected(self, client, admin_headers, existing_report_id):
        r = client.patch(
            f"/api/v1/reports/{existing_report_id}",
            headers=admin_headers,
            json={"report_text": ""},
        )
        assert r.status_code == 422

    def test_whitespace_only_patch_rejected(self, client, admin_headers, existing_report_id):
        r = client.patch(
            f"/api/v1/reports/{existing_report_id}",
            headers=admin_headers,
            json={"report_text": "    \n   "},
        )
        assert r.status_code == 422

    def test_oversized_patch_rejected(self, client, admin_headers, existing_report_id):
        r = client.patch(
            f"/api/v1/reports/{existing_report_id}",
            headers=admin_headers,
            json={"report_text": "x" * (MAX + 1)},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Configuration boundary test
# ---------------------------------------------------------------------------

class TestConfigurationBoundaries:
    """Verify that validation behaviour is driven by settings, not magic numbers."""

    def test_min_length_setting_is_respected(self, client, admin_headers, site_id):
        """Text of exactly MIN chars should pass; MIN-1 should fail."""
        at_min = "a" * MIN
        r_pass = client.post(
            "/api/v1/reports",
            headers=admin_headers,
            json=_report_payload(site_id=site_id, report_text=at_min),
        )
        assert r_pass.status_code == 201

        if MIN > 1:
            below_min = "a" * (MIN - 1)
            r_fail = client.post(
                "/api/v1/reports",
                headers=admin_headers,
                json=_report_payload(site_id=site_id, report_text=below_min),
            )
            assert r_fail.status_code == 422

    def test_max_length_setting_is_respected(self, client, admin_headers, site_id):
        """Text of exactly MAX chars should pass; MAX+1 should fail."""
        at_max = "b" * MAX
        r_pass = client.post(
            "/api/v1/reports",
            headers=admin_headers,
            json=_report_payload(site_id=site_id, report_text=at_max),
        )
        assert r_pass.status_code == 201

        over_max = "b" * (MAX + 1)
        r_fail = client.post(
            "/api/v1/reports",
            headers=admin_headers,
            json=_report_payload(site_id=site_id, report_text=over_max),
        )
        assert r_fail.status_code == 422

    def test_original_text_preserved_not_stripped(self, client, admin_headers, site_id):
        """Validation must not mutate stored text — leading/trailing spaces are preserved."""
        # Text with surrounding whitespace is still meaningful content inside.
        # Stripping is for validation logic only; storage uses the original.
        meaningful = "  Worker slipped near the valve.  "
        r = client.post(
            "/api/v1/reports",
            headers=admin_headers,
            json=_report_payload(site_id=site_id, report_text=meaningful),
        )
        assert r.status_code == 201
        assert r.json()["report_text"] == meaningful
