import os
import sqlite3
import pytest
from unittest.mock import patch
from src.etl.loader import init_db, get_db_connection

TEST_DB_PATH = "data/test_nifty100.db"

@pytest.fixture
def clean_test_db():
    # Remove test DB if exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield
    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@patch('src.etl.loader.DB_PATH', TEST_DB_PATH)
def test_init_db_creates_tables(clean_test_db):
    init_db()
    assert os.path.exists(TEST_DB_PATH)
    
    # Query sqlite_master to verify all 13 tables exist
    expected_tables = {
        "companies", "profitandloss", "balancesheet", "cashflow", 
        "analysis", "documents", "prosandcons", "sectors", 
        "stock_prices", "market_cap", "financial_ratios", "peer_groups",
        "peer_percentiles"
    }
    
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()
        
    # Check that each expected table was created
    for table in expected_tables:
        assert table in tables, f"Table {table} was not created in the database."

@patch('src.etl.loader.DB_PATH', TEST_DB_PATH)
def test_db_connection_foreign_keys(clean_test_db):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_enabled = cursor.fetchone()[0]
    conn.close()
    assert fk_enabled == 1, "Foreign key constraints are not enabled."
