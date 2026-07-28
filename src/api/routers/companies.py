import os
import sqlite3
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/companies", tags=["Companies"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("")
def get_companies(
    sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None
):
    conn = get_db()
    try:
        query = """
            SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, c.roe_percentage AS roe_pct, c.roce_percentage AS roce_pct, s.market_cap_category
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE 1=1
        """
        params = []
        if sector:
            query += " AND (LOWER(s.broad_sector) = LOWER(?) OR LOWER(s.sub_sector) = LOWER(?))"
            params.extend([sector, sector])
        if market_cap_category:
            query += " AND LOWER(s.market_cap_category) = LOWER(?)"
            params.append(market_cap_category)
        if search:
            query += " AND (LOWER(c.id) LIKE ? OR LOWER(c.company_name) LIKE ?)"
            params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
            
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{ticker}")
def get_company_profile(ticker: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category, s.index_weight_pct
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE LOWER(c.id) = LOWER(?)
        """, (ticker,))
        comp = cursor.fetchone()
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found")
        
        comp_dict = dict(comp)
        
        # Latest year ratios
        cursor.execute("""
            SELECT * FROM financial_ratios 
            WHERE LOWER(company_id) = LOWER(?) 
            ORDER BY year DESC LIMIT 1
        """, (ticker,))
        rat = cursor.fetchone()
        comp_dict["latest_ratios"] = dict(rat) if rat else {}
        
        return comp_dict
    finally:
        conn.close()

@router.get("/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: Optional[str] = None,
    to_year: Optional[str] = None
):
    conn = get_db()
    try:
        # Check existence
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM profitandloss WHERE LOWER(company_id) = LOWER(?)"
        params = [ticker]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: Optional[str] = None,
    to_year: Optional[str] = None
):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM balancesheet WHERE LOWER(company_id) = LOWER(?)"
        params = [ticker]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[str] = None,
    to_year: Optional[str] = None
):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM cashflow WHERE LOWER(company_id) = LOWER(?)"
        params = [ticker]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[str] = None
):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM financial_ratios WHERE LOWER(company_id) = LOWER(?)"
        params = [ticker]
        if year:
            query += " AND year = ?"
            params.append(year)
        query += " ORDER BY year ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    ticker_upper = ticker.upper()
    pdf_path = f"reports/tearsheets/{ticker_upper}_tearsheet.pdf"
    if not os.path.exists(pdf_path):
        # Try fallback general search
        os.makedirs("reports/tearsheets", exist_ok=True)
        # Check if we can generate one or raise 404
        raise HTTPException(status_code=404, detail=f"Tearsheet PDF for '{ticker_upper}' not found.")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{ticker_upper}_tearsheet.pdf"
    )
