import pytest
import pandas as pd
from src.analytics.ratios import (
    compute_roe, compute_de, compute_icr,
    compute_opm, compute_npm, compute_asset_turnover
)
from src.analytics.cagr import compute_cagr
from src.analytics.cashflow_kpis import compute_cfo_quality_score, compute_fcf

# 20 Distinct Ratio & KPI Unit Tests

def test_kpi_roe_positive_equity():
    assert compute_roe(100.0, 400.0, 100.0) == 20.0

def test_kpi_roe_negative_equity():
    assert compute_roe(100.0, -600.0, 100.0) is None

def test_kpi_roe_zero_equity():
    assert compute_roe(100.0, 0.0, 0.0) is None

def test_kpi_de_debt_free():
    assert compute_de(0.0, 400.0, 100.0) == 0.0

def test_kpi_de_positive_debt():
    assert compute_de(250.0, 400.0, 100.0) == 0.5

def test_kpi_icr_zero_interest():
    assert compute_icr(100.0, 0.0, 0.0) is None

def test_kpi_icr_normal():
    assert compute_icr(80.0, 20.0, 20.0) == 5.0

def test_kpi_high_leverage_flag():
    de_val = compute_de(600.0, 80.0, 20.0)
    assert de_val == 6.0 and de_val > 5.0

def test_kpi_cagr_normal():
    cagr, flag = compute_cagr(100.0, 200.0, 5)
    assert round(cagr, 2) == 14.87 and flag is None

def test_kpi_cagr_turnaround():
    cagr, flag = compute_cagr(-50.0, 100.0, 5)
    assert cagr is None and flag == "TURNAROUND"

def test_kpi_cagr_decline_to_loss():
    cagr, flag = compute_cagr(100.0, -50.0, 5)
    assert cagr is None and flag == "DECLINE_TO_LOSS"

def test_kpi_opm_calculation():
    assert compute_opm(200.0, 1000.0) == 20.0

def test_kpi_npm_calculation():
    assert compute_npm(150.0, 1000.0) == 15.0

def test_kpi_asset_turnover():
    assert compute_asset_turnover(1000.0, 2000.0) == 0.5

def test_kpi_cfo_quality_score():
    score, label = compute_cfo_quality_score([120, 150, 130], [100, 100, 100])
    assert score > 1.0 and label == "High Quality"

def test_kpi_fcf_computation():
    assert compute_fcf(500.0, -200.0) == 300.0

def test_kpi_opm_zero_sales():
    assert compute_opm(100.0, 0.0) is None

def test_kpi_npm_zero_sales():
    assert compute_npm(100.0, 0.0) is None

def test_kpi_de_negative_denominator():
    assert compute_de(100.0, -500.0, 100.0) is None

def test_kpi_cagr_zero_base():
    cagr, flag = compute_cagr(0.0, 100.0, 5)
    assert cagr is None and flag == "ZERO_BASE"
