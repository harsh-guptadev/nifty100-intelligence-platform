import pytest
import pandas as pd
from src.etl.validator import DataValidator

def test_dq01_company_pk_uniqueness():
    validator = DataValidator()
    df = pd.DataFrame([{"id": "TCS", "company_name": "TCS 1"}, {"id": "TCS", "company_name": "TCS 2"}])
    is_valid = validator.validate_companies(df)
    failures = validator.get_failures_df()
    assert not is_valid
    assert "DQ-01" in failures["rule_id"].values
    assert failures[failures["rule_id"] == "DQ-01"]["severity"].iloc[0] == "CRITICAL"

def test_dq02_annual_pk_uniqueness():
    validator = DataValidator()
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100},
        {"company_id": "TCS", "year": "2023-03", "sales": 120}
    ])
    cleaned_df, _ = validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-02" in failures["rule_id"].values

def test_dq03_fk_integrity():
    validator = DataValidator()
    df = pd.DataFrame([{"company_id": "UNKNOWN", "year": "2023-03", "sales": 100}])
    cleaned_df, _ = validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-03" in failures["rule_id"].values
    assert failures[failures["rule_id"] == "DQ-03"]["severity"].iloc[0] == "CRITICAL"

def test_dq04_bs_balance_variance():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03",
        "total_assets": 1000.0, "equity_capital": 100.0,
        "reserves": 200.0, "borrowings": 100.0, "other_liabilities": 100.0 # total liab = 500 (50% variance)
    }])
    validator.validate_time_series(df, "balancesheet", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-04" in failures["rule_id"].values
    assert failures[failures["rule_id"] == "DQ-04"]["severity"].iloc[0] == "WARNING"

def test_dq05_opm_cross_check():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03",
        "sales": 1000.0, "operating_profit": 200.0, "opm_percentage": 50.0 # computed is 20%
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-05" in failures["rule_id"].values
    assert failures[failures["rule_id"] == "DQ-05"]["severity"].iloc[0] == "WARNING"

def test_dq06_positive_sales():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03", "sales": -50.0
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-06" in failures["rule_id"].values
    assert failures[failures["rule_id"] == "DQ-06"]["severity"].iloc[0] == "WARNING"

def test_dq07_year_format():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "INVALID_YEAR", "sales": 100.0
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-07" in failures["rule_id"].values

def test_dq08_ticker_format():
    validator = DataValidator()
    df = pd.DataFrame([{"id": "A", "company_name": "A"}])
    validator.validate_companies(df)
    failures = validator.get_failures_df()
    assert "DQ-08" in failures["rule_id"].values

def test_dq09_net_cash_check():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03",
        "net_cash_flow": 500.0, "operating_activity": 100.0,
        "investing_activity": -50.0, "financing_activity": -20.0 # sum = 30
    }])
    validator.validate_time_series(df, "cashflow", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-09" in failures["rule_id"].values

def test_dq10_non_negative_fixed_assets():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03", "fixed_assets": -10.0
    }])
    validator.validate_time_series(df, "balancesheet", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-10" in failures["rule_id"].values

def test_dq11_tax_rate_range():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03", "tax_percentage": 85.0
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-11" in failures["rule_id"].values

def test_dq12_dividend_payout_cap():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03", "dividend_payout": 300.0
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-12" in failures["rule_id"].values

def test_dq14_eps_sign_consistency():
    validator = DataValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03", "net_profit": 100.0, "eps": -2.0
    }])
    validator.validate_time_series(df, "profitandloss", {"TCS"})
    failures = validator.get_failures_df()
    assert "DQ-14" in failures["rule_id"].values

def test_dq16_coverage_check():
    validator = DataValidator()
    ts_dfs = {
        "profitandloss": pd.DataFrame([{"company_id": "TCS", "year": "2023-03"}])
    }
    validator.validate_coverage(ts_dfs)
    failures = validator.get_failures_df()
    assert "DQ-16" in failures["rule_id"].values
