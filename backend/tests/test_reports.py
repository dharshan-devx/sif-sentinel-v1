from datetime import UTC, datetime


def create_site(client, headers, code="TST"):
    response = client.post("/api/v1/sites", headers=headers, json={"name": "Test Site", "code": code, "location": "Assam", "region": "North East"})
    assert response.status_code == 201
    return response.json()


def test_site_and_report_crud_filtering_and_pagination(client, admin_headers):
    site = create_site(client, admin_headers)
    for idx in range(3):
        payload = {"report_type": "NEAR_MISS", "report_text": f"Unsafe crane lifting near workers incident {idx}", "site_id": site["id"], "location": "Yard", "department": "Operations", "activity": "Lifting", "reported_at": datetime.now(UTC).isoformat(), "source_type": "SYNTHETIC"}
        response = client.post("/api/v1/reports", headers=admin_headers, json=payload)
        assert response.status_code == 201
        if idx == 0:
            report_id = response.json()["report_id"]
    one = client.get(f"/api/v1/reports/{report_id}", headers=admin_headers)
    assert one.status_code == 200
    filtered = client.get("/api/v1/reports", headers=admin_headers, params={"site_id": site["id"], "report_type": "NEAR_MISS", "search": "crane", "page": 1, "page_size": 2})
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 3
    assert len(filtered.json()["items"]) == 2
    changed = client.patch(f"/api/v1/reports/{report_id}", headers=admin_headers, json={"status": "REVIEW_REQUIRED"})
    assert changed.status_code == 200
    deleted = client.delete(f"/api/v1/reports/{report_id}", headers=admin_headers)
    assert deleted.status_code == 200
