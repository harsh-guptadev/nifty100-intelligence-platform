import pytest
from src.etl.normaliser import normalize_year, normalize_ticker

# 20 Unit Tests for normalize_year
def test_normalize_year_already_formatted_1():
    assert normalize_year("2023-03") == "2023-03"

def test_normalize_year_already_formatted_2():
    assert normalize_year("2020-12") == "2020-12"

def test_normalize_year_int():
    assert normalize_year(2023) == "2023-03"

def test_normalize_year_str_digit():
    assert normalize_year("2024") == "2024-03"

def test_normalize_year_past_int():
    assert normalize_year(2010) == "2010-03"

def test_normalize_year_fy_short():
    assert normalize_year("FY23") == "2023-03"

def test_normalize_year_fy_space():
    assert normalize_year("FY 24") == "2024-03"

def test_normalize_year_fy_lower():
    assert normalize_year("fy20") == "2020-03"

def test_normalize_year_fy_full():
    assert normalize_year("FY2025") == "2025-03"

def test_normalize_year_mar_dash():
    assert normalize_year("Mar-23") == "2023-03"

def test_normalize_year_mar_space():
    assert normalize_year("Mar 23") == "2023-03"

def test_normalize_year_dec_dash():
    assert normalize_year("Dec-22") == "2022-12"

def test_normalize_year_jun_dash():
    assert normalize_year("Jun-23") == "2023-06"

def test_normalize_year_march_full():
    assert normalize_year("March-2023") == "2023-03"

def test_normalize_year_december_full():
    assert normalize_year("December 2022") == "2022-12"

def test_normalize_year_sep_slash():
    assert normalize_year("Sep/21") == "2021-09"

def test_normalize_year_jan_lower():
    assert normalize_year("jan-24") == "2024-01"

def test_normalize_year_garbage():
    assert normalize_year("garbage") == "PARSE_ERROR"

def test_normalize_year_empty():
    assert normalize_year("") == "PARSE_ERROR"

def test_normalize_year_none():
    assert normalize_year(None) == "PARSE_ERROR"

# Ticker Normalization Tests
def test_normalize_ticker_cases():
    assert normalize_ticker("TCS") == "TCS"
    assert normalize_ticker("  BAJAJ-AUTO  ") == "BAJAJ-AUTO"
    assert normalize_ticker("m&m") == "M&M"
    assert normalize_ticker("") == "MISSING"
