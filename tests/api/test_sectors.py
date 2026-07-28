import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_sectors_summary():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10

def test_api_sector_companies_valid():
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert row["broad_sector"] == "Information Technology"

def test_api_sector_companies_invalid_404():
    response = client.get("/api/v1/sectors/NON_EXISTENT_SECTOR_999/companies")
    assert response.status_code == 404
