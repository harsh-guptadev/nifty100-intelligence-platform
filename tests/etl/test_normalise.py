import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

def test_normalize_year_20_cases():
    # 1. Already normalized
    assert normalize_year("2023-03") == "2023-03"
    assert normalize_year("2020-12") == "2020-12"
    
    # 2. Plain 4-digit years (assume March close)
    assert normalize_year(2023) == "2023-03"
    assert normalize_year("2024") == "2024-03"
    assert normalize_year(2010) == "2010-03"
    
    # 3. FY prefix (assume March close)
    assert normalize_year("FY23") == "2023-03"
    assert normalize_year("FY 24") == "2024-03"
    assert normalize_year("fy20") == "2020-03"
    assert normalize_year("FY2025") == "2025-03"
    
    # 4. Standard Month-Year formats (various delimiters)
    assert normalize_year("Mar-23") == "2023-03"
    assert normalize_year("Mar 23") == "2023-03"
    assert normalize_year("Dec-22") == "2022-12"
    assert normalize_year("Jun-23") == "2023-06"
    assert normalize_year("March-2023") == "2023-03"
    assert normalize_year("December 2022") == "2022-12"
    assert normalize_year("Sep/21") == "2021-09"
    assert normalize_year("jan-24") == "2024-01"
    
    # 5. Edge cases & garbage
    assert normalize_year("garbage") == "PARSE_ERROR"
    assert normalize_year("") == "PARSE_ERROR"
    assert normalize_year(None) == "PARSE_ERROR"
    assert normalize_year("  ") == "PARSE_ERROR"

def test_normalize_ticker_15_cases():
    # 1. Standard tickers
    assert normalize_ticker("TCS") == "TCS"
    assert normalize_ticker("tcs") == "TCS"
    assert normalize_ticker("  TCS  ") == "TCS"
    
    # 2. Tickers with hyphens
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"
    assert normalize_ticker("  BAJAJ-AUTO  ") == "BAJAJ-AUTO"
    
    # 3. Tickers with ampersands
    assert normalize_ticker("M&M") == "M&M"
    assert normalize_ticker("m&m") == "M&M"
    assert normalize_ticker("  M&M  ") == "M&M"
    
    # 4. Numbers in tickers
    assert normalize_ticker("NIFTY100") == "NIFTY100"
    assert normalize_ticker("nifty100") == "NIFTY100"
    
    # 5. Missing / empty / None
    assert normalize_ticker("") == "MISSING"
    assert normalize_ticker(None) == "MISSING"
    assert normalize_ticker("   ") == "MISSING"
    assert normalize_ticker("\n") == "MISSING"
