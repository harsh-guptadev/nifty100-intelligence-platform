import time
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_screener_load_performance():
    start = time.time()
    for _ in range(5):
        resp = client.get("/api/v1/screener?min_roe=10")
        assert resp.status_code == 200
    duration = time.time() - start
    assert duration < 10.0, f"5 screener calls took {duration:.2f}s (expected < 10s)"

def test_company_profile_latency_under_3s():
    tickers = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
    for ticker in tickers:
        start = time.time()
        resp = client.get(f"/api/v1/companies/{ticker}")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 3.0, f"{ticker} profile load took {elapsed:.2f}s (expected < 3s)"
