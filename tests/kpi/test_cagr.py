import pytest
import numpy as np
from src.analytics.cagr import compute_cagr

def test_cagr_normal():
    # Normal case: start=100, end=161.051, n=5 years (expected ~10% growth)
    val, flag = compute_cagr(100.0, 161.051, 5)
    assert val is not None
    assert abs(val - 10.0) < 0.01
    assert flag is None

def test_cagr_decline_to_loss():
    # Start is positive, end is negative/zero
    val, flag = compute_cagr(100.0, -10.0, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"
    
    val, flag = compute_cagr(100.0, 0.0, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    # Start is negative, end is positive
    val, flag = compute_cagr(-50.0, 100.0, 5)
    assert val is None
    assert flag == "TURNAROUND"

def test_cagr_both_negative():
    # Both start and end are negative
    val, flag = compute_cagr(-50.0, -20.0, 5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    # Start is exactly 0
    val, flag = compute_cagr(0.0, 100.0, 5)
    assert val is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient_history():
    # Insufficient years (n <= 0)
    val, flag = compute_cagr(100.0, 150.0, 0)
    assert val is None
    assert flag == "INSUFFICIENT"
    
    val, flag = compute_cagr(100.0, 150.0, -2)
    assert val is None
    assert flag == "INSUFFICIENT"
    
    # Missing values (NaN)
    val, flag = compute_cagr(np.nan, 150.0, 5)
    assert val is None
    assert flag == "INSUFFICIENT"
    
    val, flag = compute_cagr(100.0, None, 5)
    assert val is None
    assert flag == "INSUFFICIENT"
