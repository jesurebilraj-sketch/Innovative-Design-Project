"""Test health and root endpoints."""

def test_root_endpoint(client):
    """Verify root endpoint responds with status and version."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "message" in data


def test_health_endpoint(client):
    """Verify health endpoint responds with healthy status."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "skyops-backend"
