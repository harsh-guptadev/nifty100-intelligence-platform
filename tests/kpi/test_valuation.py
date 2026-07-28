import pytest
import pandas as pd
from src.analytics.valuation import compute_valuation_flag, run_valuation_module

def test_compute_valuation_flag():
    # Caution: P/E > sector_median * 1.5
    row_caution = {"pe_ratio": 35.0, "sector_median_pe": 20.0}
    assert compute_valuation_flag(row_caution) == "Caution"

    # Discount: P/E < sector_median * 0.7
    row_discount = {"pe_ratio": 12.0, "sector_median_pe": 20.0}
    assert compute_valuation_flag(row_discount) == "Discount"

    # Fair: in between
    row_fair = {"pe_ratio": 22.0, "sector_median_pe": 20.0}
    assert compute_valuation_flag(row_fair) == "Fair"

    # Missing values default to Fair
    row_missing = {"pe_ratio": None, "sector_median_pe": 20.0}
    assert compute_valuation_flag(row_missing) == "Fair"

def test_run_valuation_module():
    df = run_valuation_module()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 92
    assert "fcf_yield_pct" in df.columns
    assert "sector_median_pe" in df.columns
    assert "pe_vs_sector_pct" in df.columns
    assert "flag" in df.columns
    assert set(df["flag"].unique()).issubset({"Caution", "Discount", "Fair"})
