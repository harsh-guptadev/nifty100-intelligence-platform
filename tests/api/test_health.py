import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert len(data["db_row_counts"]) == 10
    assert data["db_row_counts"]["companies"] == 92
