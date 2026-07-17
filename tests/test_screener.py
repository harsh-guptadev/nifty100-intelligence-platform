import pytest
import pandas as pd
import numpy as np
from src.screener.engine import (
    load_screener_config,
    get_screener_data,
    compute_sector_relative_scores,
    apply_filters,
    run_preset_screener
)

def test_load_config():
    config = load_screener_config()
    assert "presets" in config
    assert "Quality Compounder" in config["presets"]
    assert "Value Pick" in config["presets"]

def test_apply_filters_financials_de_skip():
    # D/E max filter should skip financials
    criteria = {"debt_to_equity_max": 1.0}
    df = pd.DataFrame([
        {"company_id": "BANK_A", "broad_sector": "Financials", "debt_to_equity": 8.0, "icr_label": None, "interest": 10.0, "interest_coverage": 1.0},
        {"company_id": "BANK_B", "broad_sector": "Financials", "debt_to_equity": 0.5, "icr_label": None, "interest": 10.0, "interest_coverage": 1.0},
        {"company_id": "IND_C", "broad_sector": "Industrials", "debt_to_equity": 2.5, "icr_label": None, "interest": 10.0, "interest_coverage": 1.0},
        {"company_id": "IND_D", "broad_sector": "Industrials", "debt_to_equity": 0.8, "icr_label": None, "interest": 10.0, "interest_coverage": 1.0}
    ])
    
    res = apply_filters(df, criteria)
    # BANK_A should pass because it is Financials (D/E max skip)
    # BANK_B should pass
    # IND_C should fail because D/E = 2.5 > 1.0
    # IND_D should pass
    passed_tickers = set(res["company_id"])
    assert "BANK_A" in passed_tickers
    assert "BANK_B" in passed_tickers
    assert "IND_C" not in passed_tickers
    assert "IND_D" in passed_tickers

def test_apply_filters_icr_debt_free():
    # ICR min filter should treat Debt Free label as infinite (always passes)
    criteria = {"interest_coverage_min": 3.0}
    df = pd.DataFrame([
        {"company_id": "CO_A", "broad_sector": "Energy", "interest_coverage": 1.2, "icr_label": None, "interest": 10.0},
        {"company_id": "CO_B", "broad_sector": "Energy", "interest_coverage": 4.5, "icr_label": None, "interest": 10.0},
        {"company_id": "CO_C", "broad_sector": "Energy", "interest_coverage": None, "icr_label": "Debt Free", "interest": 0.0}
    ])
    
    res = apply_filters(df, criteria)
    passed_tickers = set(res["company_id"])
    assert "CO_A" not in passed_tickers
    assert "CO_B" in passed_tickers
    assert "CO_C" in passed_tickers

def test_run_presets():
    df_data = get_screener_data()
    
    # 1. Quality Compounder
    res_qc = run_preset_screener("Quality Compounder", df_data)
    assert 5 <= len(res_qc) <= 50
    for _, row in res_qc.iterrows():
        assert row["return_on_equity_pct"] > 15.0
        if str(row["broad_sector"]).lower() != "financials":
            assert row["debt_to_equity"] < 1.0
            
    # 2. Value Pick
    res_vp = run_preset_screener("Value Pick", df_data)
    assert 5 <= len(res_vp) <= 50
    for _, row in res_vp.iterrows():
        assert row["pe_ratio"] < 30.0
        assert row["pb_ratio"] < 4.0
        if str(row["broad_sector"]).lower() != "financials":
            assert row["debt_to_equity"] < 2.0
            
    # 3. Growth Accelerator
    res_ga = run_preset_screener("Growth Accelerator", df_data)
    assert 5 <= len(res_ga) <= 50
    for _, row in res_ga.iterrows():
        if str(row["broad_sector"]).lower() != "financials":
            assert row["debt_to_equity"] < 2.0
            
    # 4. Dividend Champion
    res_dc = run_preset_screener("Dividend Champion", df_data)
    assert 5 <= len(res_dc) <= 50
    for _, row in res_dc.iterrows():
        assert row["dividend_yield_pct"] > 2.0
        assert row["dividend_payout_ratio_pct"] < 80.0
        
    # 5. Debt-Free Blue Chip
    res_dfbc = run_preset_screener("Debt-Free Blue Chip", df_data)
    assert 5 <= len(res_dfbc) <= 50
    for _, row in res_dfbc.iterrows():
        if str(row["broad_sector"]).lower() != "financials":
            assert row["debt_to_equity"] == 0.0
        assert row["return_on_equity_pct"] > 12.0
        
    # 6. Turnaround Watch
    res_tw = run_preset_screener("Turnaround Watch", df_data)
    assert 5 <= len(res_tw) <= 50
    for _, row in res_tw.iterrows():
        assert row["free_cash_flow_cr"] > 0
        assert row["revenue_cagr_3yr"] > 10.0

def test_composite_scoring_distribution():
    df_data = get_screener_data()
    df_scored = compute_sector_relative_scores(df_data)
    assert "composite_quality_score" in df_scored.columns
    scores = df_scored["composite_quality_score"].dropna()
    assert len(scores) > 0
    assert scores.min() >= 0.0
    assert scores.max() <= 100.0
