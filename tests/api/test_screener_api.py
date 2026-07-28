import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_screener_valid_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for row in data:
        assert row["return_on_equity_pct"] is not None and row["return_on_equity_pct"] >= 15.0

def test_api_screener_invalid_param_400():
    response = client.get("/api/v1/screener?max_pe=-10")
    assert response.status_code == 400
