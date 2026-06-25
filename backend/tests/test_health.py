from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "data" in json_data
    assert json_data["data"]["status"] == "healthy"
    assert "uptime_seconds" in json_data["data"]


def test_dashboard():
    response = client.get("/api/v1/system/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DevPortal" in response.text

