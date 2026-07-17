import pytest
import pandas as pd
from src.etl.validator import DataValidator

def test_validate_companies_success():
    validator = DataValidator()
    df = pd.DataFrame([
        {"id": "TCS", "company_name": "Tata Consultancy Services", "face_value": 1.0},
        {"id": "INFY", "company_name": "Infosys Ltd", "face_value": 5.0}
    ])
    assert validator.validate_companies(df) is True
    assert len(validator.failures) == 0

def test_validate_companies_duplicate_ticker():
    validator = DataValidator()
    df = pd.DataFrame([
        {"id": "TCS", "company_name": "Tata Consultancy Services", "face_value": 1.0},
        {"id": "TCS", "company_name": "Duplicate TCS", "face_value": 1.0}
    ])
    assert validator.validate_companies(df) is False
    assert len(validator.failures) > 0
    assert validator.failures[0]["rule_id"] == "DQ-01"
    assert validator.failures[0]["severity"] == "CRITICAL"

def test_validate_companies_invalid_ticker_length():
    validator = DataValidator()
    # Ticker length < 2 or > 12
    df = pd.DataFrame([
        {"id": "T", "company_name": "Too Short Ticker", "face_value": 1.0},
        {"id": "VERYLONGNSEICKERNAME", "company_name": "Too Long Ticker", "face_value": 5.0}
    ])
    assert validator.validate_companies(df) is False
    assert len(validator.failures) == 2
    assert validator.failures[0]["rule_id"] == "DQ-08"
    assert validator.failures[1]["rule_id"] == "DQ-08"

def test_validate_time_series_fk_integrity():
    validator = DataValidator()
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0},
        {"company_id": "INVALIDCO", "year": "2023-03", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0}
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "profitandloss", valid_cos)
    assert len(cleaned_df) == 1
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-03"

def test_validate_time_series_year_format():
    validator = DataValidator()
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0},
        {"company_id": "TCS", "year": "PARSE_ERROR", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0},
        {"company_id": "TCS", "year": "2023/03", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0}
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "profitandloss", valid_cos)
    assert len(cleaned_df) == 1
    dq07_failures = [f for f in validator.failures if f["rule_id"] == "DQ-07"]
    assert len(dq07_failures) == 2

def test_validate_time_series_duplicates():
    validator = DataValidator()
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 20.0},
        {"company_id": "TCS", "year": "2023-03", "sales": 120.0, "expenses": 90.0, "operating_profit": 30.0, "opm_percentage": 25.0}
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "profitandloss", valid_cos)
    # Should deduplicate and keep the last one
    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]["sales"] == 120.0
    assert len(validator.failures) == 2  # Both duplicates are logged as failures per specification
    assert validator.failures[0]["rule_id"] == "DQ-02"

def test_validate_profit_and_loss_warnings():
    validator = DataValidator()
    # Mismatch OPM (reported 10%, computed 20%)
    # Negative sales
    # Tax rate range out of bounds
    # Dividend payout > 200%
    # EPS sign inconsistency
    df = pd.DataFrame([
        {
            "company_id": "TCS", "year": "2023-03",
            "sales": 100.0, "expenses": 80.0, "operating_profit": 20.0, "opm_percentage": 10.0,
            "tax_percentage": 70.0, "dividend_payout": 250.0, "net_profit": 15.0, "eps": -1.0
        }
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "profitandloss", valid_cos)
    assert len(cleaned_df) == 1
    # Check that OPM, tax_percentage, dividend_payout, and EPS inconsistencies are flagged
    rule_ids = [f["rule_id"] for f in validator.failures]
    assert "DQ-05" in rule_ids
    assert "DQ-11" in rule_ids
    assert "DQ-12" in rule_ids
    assert "DQ-14" in rule_ids

def test_validate_balance_sheet_warnings():
    validator = DataValidator()
    # Out of balance: Assets 100, Liab+Equity = 50 + 20 + 20 + 20 = 110 (diff 10% > 1%)
    # Negative fixed assets
    df = pd.DataFrame([
        {
            "company_id": "TCS", "year": "2023-03",
            "total_assets": 100.0,
            "equity_capital": 50.0, "reserves": 20.0, "borrowings": 20.0, "other_liabilities": 20.0,
            "fixed_assets": -5.0
        }
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "balancesheet", valid_cos)
    assert len(cleaned_df) == 1
    # Fixed assets coerced to 0.0
    assert cleaned_df.iloc[0]["fixed_assets"] == 0.0
    rule_ids = [f["rule_id"] for f in validator.failures]
    assert "DQ-04" in rule_ids
    assert "DQ-10" in rule_ids

def test_validate_cash_flow_warnings():
    validator = DataValidator()
    # Net cash flow mismatch: reported 10, computed 30 (10 + 10 + 10)
    df = pd.DataFrame([
        {
            "company_id": "TCS", "year": "2023-03",
            "net_cash_flow": 10.0,
            "operating_activity": 10.0, "investing_activity": 10.0, "financing_activity": 10.0
        }
    ])
    valid_cos = {"TCS"}
    cleaned_df, is_valid = validator.validate_time_series(df, "cashflow", valid_cos)
    assert len(cleaned_df) == 1
    # Net cash flow coerced to sum (30.0)
    assert cleaned_df.iloc[0]["net_cash_flow"] == 30.0
    rule_ids = [f["rule_id"] for f in validator.failures]
    assert "DQ-09" in rule_ids
