def test_register_login_and_me(client):
    payload = {"email": "viewer@sif.demo", "password": "test-password-123", "full_name": "Viewer"}
    registered = client.post("/api/v1/auth/register", json=payload)
    assert registered.status_code == 201
    logged_in = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_unauthorized_and_role_protected_site_creation(client):
    assert client.post("/api/v1/sites", json={}).status_code == 401
    client.post("/api/v1/auth/register", json={"email": "limited@sif.demo", "password": "test-password-123", "full_name": "Limited"})
    token = client.post("/api/v1/auth/login", json={"email": "limited@sif.demo", "password": "test-password-123"}).json()["access_token"]
    result = client.post("/api/v1/sites", headers={"Authorization": f"Bearer {token}"}, json={"name": "No Access", "code": "NOA", "location": "Test", "region": "Test"})
    assert result.status_code == 403
