import pytest
import pandas as pd
import numpy as np
from src.analytics.ratios import (
    compute_npm,
    compute_opm,
    compute_roe,
    compute_roce,
    compute_roa,
    compute_de,
    compute_icr,
    compute_net_debt,
    compute_asset_turnover
)

def test_npm():
    # Normal case
    assert compute_npm(10, 100) == 10.0
    # Zero sales denominator
    assert compute_npm(10, 0) is None
    # None/NaN inputs
    assert compute_npm(None, 100) is None
    assert compute_npm(10, np.nan) is None

def test_opm():
    # Normal case
    assert compute_opm(20, 100) == 20.0
    # Zero sales
    assert compute_opm(20, 0) is None
    # NaN
    assert compute_opm(np.nan, 100) is None

def test_roe():
    # Normal case
    assert compute_roe(15, 50, 50) == 15.0
    # Negative/zero equity+reserves denominator
    assert compute_roe(15, -10, 5) is None
    assert compute_roe(15, 0, 0) is None
    # NaN
    assert compute_roe(15, 50, np.nan) is None

def test_roce():
    # Normal case
    assert compute_roce(25, 40, 40, 20) == 25.0
    # Zero/negative capital employed denominator
    assert compute_roce(25, -50, 20, 10) is None
    # NaN
    assert compute_roce(np.nan, 40, 40, 20) is None

def test_roa():
    # Normal case
    assert compute_roa(5, 100) == 5.0
    # Zero assets
    assert compute_roa(5, 0) is None
    # NaN
    assert compute_roa(5, np.nan) is None

def test_de():
    # Normal case
    assert compute_de(50, 50, 50) == 0.5
    # Debt free case (borrowings = 0)
    assert compute_de(0, 50, 50) == 0.0
    assert compute_de(np.nan, 50, 50) == 0.0
    # Zero/negative equity denominator
    assert compute_de(10, 0, 0) is None
    assert compute_de(10, -20, 10) is None

def test_icr():
    # Normal case
    assert compute_icr(15, 5, 4) == 5.0
    # Interest = 0 (Debt Free -> returns None)
    assert compute_icr(15, 5, 0) is None
    assert compute_icr(15, 5, np.nan) is None
    # Missing EBIT and other income
    assert compute_icr(np.nan, np.nan, 10) is None

def test_net_debt():
    # Normal case
    assert compute_net_debt(100, 40) == 60.0
    # Net cash positive (borrowings < investments)
    assert compute_net_debt(20, 50) == -30.0
    # NaNs handled as 0.0
    assert compute_net_debt(None, 40) == -40.0
    assert compute_net_debt(100, np.nan) == 100.0

def test_asset_turnover():
    # Normal case
    assert compute_asset_turnover(150, 100) == 1.5
    # Zero assets
    assert compute_asset_turnover(150, 0) is None
