import os
import sqlite3
import pytest
from unittest.mock import patch
from src.etl.loader import init_db, get_db_connection

DB_PATH = "data/nifty100.db"

def test_loader_companies_table_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 92

def test_loader_companies_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(companies)")
    cols = [r[1] for r in cursor.fetchall()]
    conn.close()
    assert "id" in cols and "company_name" in cols

def test_loader_pl_table_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM profitandloss")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 900

def test_loader_bs_table_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM balancesheet")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 900

def test_loader_cashflow_table_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cashflow")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 900

def test_loader_financial_ratios_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM financial_ratios")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 1100

def test_loader_sectors_table_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sectors")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 92

def test_loader_market_cap_table_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_cap")
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0

def test_loader_documents_table_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0

def test_loader_foreign_keys_active():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_enabled = cursor.fetchone()[0]
    conn.close()
    assert fk_enabled == 1
