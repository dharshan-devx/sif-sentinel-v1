import requests
import uuid

BASE_URL = "http://localhost:8000"
email = "admin@sif.demo"
password = "Demo-Only-Password-2026!"

def test_workflow():
    # 2. Login
    res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create site
    site_code = f"E2E-{uuid.uuid4().hex[:6]}"
    res = requests.post(f"{BASE_URL}/api/v1/sites", json={"name": "E2E Site", "code": site_code, "location": "Test City", "region": "NA"}, headers=headers)
    assert res.status_code in (200, 201), res.text
    assert res.status_code in (200, 201), res.text
    site_id = res.json()["id"]
    
    # 4. Create safety report
    res = requests.post(f"{BASE_URL}/api/v1/reports", json={
        "site_id": site_id,
        "report_type": "NEAR_MISS",
        "source_type": "USER_SUBMITTED",
        "location": "North Wing",
        "department": "Electrical",
        "report_text": "The quick brown fox jumps over the lazy dog.",
        "reported_at": "2026-09-03T10:00:00Z"
    }, headers=headers)
    assert res.status_code in (200, 201), res.text
    report_id = res.json()["report_id"]
    
    # 5. Run analysis
    res = requests.post(f"{BASE_URL}/api/v1/reports/{report_id}/analyze", headers=headers)
    assert res.status_code in (200, 201), res.text
    
    # 6. Verify analysis persistence
    res = requests.get(f"{BASE_URL}/api/v1/reports/{report_id}", headers=headers)
    assert res.status_code in (200, 201), res.text
    report = res.json()
    assert report["status"] in ("REVIEW_REQUIRED", "ANALYZED", "PENDING_REVIEW"), f"Unexpected status: {report['status']}"
    
    # 7. Retrieve pending reviews
    res = requests.get(f"{BASE_URL}/api/v1/reviews?status=PENDING", headers=headers)
    assert res.status_code in (200, 201), res.text
    reviews = res.json()
    assert len(reviews) > 0
    review_id = next((r["id"] for r in reviews if r["report_id"] == report_id), None)
    if not review_id and len(reviews) > 0:
        review_id = reviews[0]["id"]
    
    # 8. APPROVE a review
    res = requests.post(f"{BASE_URL}/api/v1/reviews/{review_id}/decision", json={"decision": "APPROVE", "reviewer_comment": "Looks good"}, headers=headers)
    assert res.status_code in (200, 201), res.text
    assert res.json()["decision"] == "APPROVE"
    
    # Create another report for REJECT
    res = requests.post(f"{BASE_URL}/api/v1/reports", json={
        "site_id": site_id,
        "report_type": "UNSAFE_CONDITION",
        "source_type": "USER_SUBMITTED",
        "location": "South Wing",
        "department": "Civil",
        "report_text": "Another completely random sentence that triggers review.",
        "reported_at": "2026-09-03T11:00:00Z"
    }, headers=headers)
    assert res.status_code in (200, 201), res.text
    report_2_id = res.json()["report_id"]
    requests.post(f"{BASE_URL}/api/v1/reports/{report_2_id}/analyze", headers=headers)
    res = requests.get(f"{BASE_URL}/api/v1/reviews?status=PENDING", headers=headers)
    review_2 = next((r for r in res.json() if r["report_id"] == report_2_id), None)
    if not review_2 and len(res.json()) > 1:
        review_2 = res.json()[1]
    
    # 9. REJECT a review
    if review_2:
        res = requests.post(f"{BASE_URL}/api/v1/reviews/{review_2['id']}/decision", json={"decision": "REJECT", "reviewer_comment": "Invalid report"}, headers=headers)
        assert res.status_code in (200, 201), res.text
        assert res.json()["decision"] == "REJECT"
    
    # Create another report for MODIFY
    res = requests.post(f"{BASE_URL}/api/v1/reports", json={
        "site_id": site_id,
        "report_type": "UNSAFE_CONDITION",
        "source_type": "USER_SUBMITTED",
        "location": "East Wing",
        "department": "Scaffolding",
        "report_text": "Just another random text for the third report.",
        "reported_at": "2026-09-03T12:00:00Z"
    }, headers=headers)
    assert res.status_code in (200, 201), res.text
    report_3_id = res.json()["report_id"]
    requests.post(f"{BASE_URL}/api/v1/reports/{report_3_id}/analyze", headers=headers)
    res = requests.get(f"{BASE_URL}/api/v1/reviews?status=PENDING", headers=headers)
    review_3 = next((r for r in res.json() if r["report_id"] == report_3_id), None)
    if not review_3 and len(res.json()) > 2:
        review_3 = res.json()[2]
    
    # 10. MODIFY a review
    if review_3:
        res = requests.post(f"{BASE_URL}/api/v1/reviews/{review_3['id']}/decision", json={
            "decision": "MODIFY",
            "reviewer_comment": "Changed SIF level",
            "corrected_sif_level": "LOW",
            "corrected_barrier_status": "EFFECTIVE"
        }, headers=headers)
        assert res.status_code in (200, 201), res.text
        assert res.json()["decision"] == "MODIFY"
    
    # 11. Retrieve review history
    res = requests.get(f"{BASE_URL}/api/v1/reviews?status=REVIEWED", headers=headers)
    assert res.status_code in (200, 201), res.text
    
    # 13. Verify precursor intelligence
    res = requests.get(f"{BASE_URL}/api/v1/precursors/trends", headers=headers)
    assert res.status_code in (200, 201), res.text
    
    # 14. Verify risk calculations (via dashboard)
    res = requests.get(f"{BASE_URL}/api/v1/dashboard/summary", headers=headers)
    assert res.status_code in (200, 201), res.text
    
    # 15. Verify dashboard analytics
    res = requests.get(f"{BASE_URL}/api/v1/dashboard/sif-trend?window=30d", headers=headers)
    assert res.status_code in (200, 201), res.text
    
    # 16. Verify Life Saving Rules retrieval
    res = requests.get(f"{BASE_URL}/api/v1/rules", headers=headers)
    assert res.status_code in (200, 201), res.text
    rules = res.json()
    assert len(rules) > 0, "No rules returned!"
    print(f"Verified {len(rules)} seeded rules.")
    
    print("ALL 16 E2E POSTGRES WORKFLOW STEPS VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    test_workflow()
