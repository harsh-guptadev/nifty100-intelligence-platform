import time
import os
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/health", tags=["Health"])

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
START_TIME = time.time()

TABLES_TO_COUNT = [
    "companies", "profitandloss", "balancesheet", "cashflow", "analysis",
    "documents", "prosandcons", "sectors", "stock_prices", "market_cap"
]

@router.get("")
def health_check():
    row_counts = {}
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database file not found")
        
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        for tbl in TABLES_TO_COUNT:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                row_counts[tbl] = cursor.fetchone()[0]
            except Exception:
                row_counts[tbl] = 0
    finally:
        conn.close()

    uptime = time.time() - START_TIME
    return {
        "status": "ok",
        "db_row_counts": row_counts,
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0"
    }
