import pytest
import numpy as np
from src.analytics.cashflow_kpis import (
    compute_fcf,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation
)

def test_fcf():
    assert compute_fcf(100.0, -30.0) == 70.0
    assert compute_fcf(50.0, 10.0) == 60.0
    assert compute_fcf(100.0, np.nan) is None

def test_cfo_quality_score():
    # CFO = [120, 110, 130, 90, 100], PAT = [100, 100, 100, 100, 100] -> sum CFO = 550, sum PAT = 500 -> score = 1.1 -> High Quality
    score, label = compute_cfo_quality_score([120, 110, 130, 90, 100], [100, 100, 100, 100, 100])
    assert score == 1.1
    assert label == "High Quality"
    
    # CFO = [80, 70, 60, 50, 40], PAT = [100, 100, 100, 100, 100] -> score = 0.6 -> Moderate
    score, label = compute_cfo_quality_score([80, 70, 60, 50, 40], [100, 100, 100, 100, 100])
    assert score == 0.6
    assert label == "Moderate"
    
    # CFO = [30, 40, 20, 10, 25], PAT = [100, 100, 100, 100, 100] -> score = 0.25 -> Accrual Risk
    score, label = compute_cfo_quality_score([30, 40, 20, 10, 25], [100, 100, 100, 100, 100])
    assert score == 0.25
    assert label == "Accrual Risk"
    
    # PAT is 0
    score, label = compute_cfo_quality_score([10, 20], [0, 0])
    assert score is None
    assert label is None

def test_capex_intensity():
    # abs(-20) / 1000 * 100 = 2% -> Asset Light
    intensity, label = compute_capex_intensity(-20.0, 1000.0)
    assert intensity == 2.0
    assert label == "Asset Light"
    
    # abs(-50) / 1000 * 100 = 5% -> Moderate
    intensity, label = compute_capex_intensity(-50.0, 1000.0)
    assert intensity == 5.0
    assert label == "Moderate"
    
    # abs(-120) / 1000 * 100 = 12% -> Capital Intensive
    intensity, label = compute_capex_intensity(-120.0, 1000.0)
    assert intensity == 12.0
    assert label == "Capital Intensive"
    
    # Sales = 0
    intensity, label = compute_capex_intensity(-50.0, 0.0)
    assert intensity is None
    assert label is None

def test_fcf_conversion_rate():
    assert compute_fcf_conversion_rate(60.0, 100.0) == 60.0
    assert compute_fcf_conversion_rate(50.0, 0.0) is None

def test_capital_allocation_patterns():
    # (+, -, -) with high PAT (CFO/PAT <= 1) and no dividend -> Reinvestor
    assert classify_capital_allocation(100.0, -40.0, -30.0, pat=200.0) == "Reinvestor"
    
    # (+, -, -) with high CFO/PAT > 1 -> Shareholder Returns
    assert classify_capital_allocation(150.0, -30.0, -60.0, pat=100.0) == "Shareholder Returns"
    
    # (+, -, -) with dividend payout >= 30% -> Shareholder Returns
    assert classify_capital_allocation(100.0, -40.0, -30.0, pat=200.0, dividend_payout_pct=35.0) == "Shareholder Returns"
    
    # (+, +, -) -> Liquidating Assets
    assert classify_capital_allocation(100.0, 20.0, -30.0) == "Liquidating Assets"
    
    # (-, +, +) -> Distress Signal
    assert classify_capital_allocation(-50.0, 20.0, 30.0) == "Distress Signal"
    
    # (-, -, +) -> Growth Funded by Debt
    assert classify_capital_allocation(-50.0, -30.0, 100.0) == "Growth Funded by Debt"
    
    # (+, +, +) -> Cash Accumulator
    assert classify_capital_allocation(100.0, 30.0, 20.0) == "Cash Accumulator"
    
    # (-, -, -) -> Pre-Revenue
    assert classify_capital_allocation(-20.0, -10.0, -5.0) == "Pre-Revenue"
