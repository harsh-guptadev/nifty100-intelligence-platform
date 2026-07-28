import os
import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/companies", tags=["Documents"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/{ticker}/documents")
def get_company_documents(ticker: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        cursor.execute("""
            SELECT id, company_id, Year, Annual_Report 
            FROM documents 
            WHERE LOWER(company_id) = LOWER(?) 
            ORDER BY Year DESC
        """, (ticker,))
        rows = cursor.fetchall()
        
        docs = []
        for r in rows:
            url = r["Annual_Report"]
            is_valid = bool(url and (url.startswith("http://") or url.startswith("https://")))
            docs.append({
                "id": r["id"],
                "company_id": r["company_id"],
                "year": r["Year"],
                "annual_report_url": url,
                "is_url_valid": is_valid
            })
        return docs
    finally:
        conn.close()
