import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_companies_all():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92

def test_get_company_by_ticker_valid():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["id"].upper() == "TCS"
    assert "company_name" in data

def test_get_company_by_ticker_invalid():
    response = client.get("/api/v1/companies/INVALID_TICKER_123")
    assert response.status_code == 404

def test_get_company_pl_history():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
