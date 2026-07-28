import os
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/market-cap", tags=["Valuation"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/{ticker}")
def get_valuation_history(ticker: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        cursor.execute("""
            SELECT year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
            FROM market_cap
            WHERE LOWER(company_id) = LOWER(?) AND year BETWEEN 2019 AND 2024
            ORDER BY year ASC
        """, (ticker,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
