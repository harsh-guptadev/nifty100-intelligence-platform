import os
import sqlite3
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sectors", tags=["Sectors"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("")
def get_sectors_summary():
    conn = get_db()
    try:
        df_sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        df_rat = pd.read_sql("""
            SELECT fr.company_id, fr.return_on_equity_pct, fr.debt_to_equity, mc.pe_ratio
            FROM financial_ratios fr
            LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND mc.year = 2024
            WHERE fr.year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
        """, conn)
        
        merged = df_sec.merge(df_rat, on="company_id", how="inner")
        
        sectors_list = []
        for sector, grp in merged.groupby("broad_sector"):
            sectors_list.append({
                "broad_sector": sector,
                "company_count": len(grp),
                "median_roe": float(grp["return_on_equity_pct"].median()) if not grp["return_on_equity_pct"].dropna().empty else None,
                "median_pe": float(grp["pe_ratio"].median()) if not grp["pe_ratio"].dropna().empty else None,
                "median_de": float(grp["debt_to_equity"].median()) if not grp["debt_to_equity"].dropna().empty else None,
            })
        return sectors_list
    finally:
        conn.close()

@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT broad_sector FROM sectors WHERE LOWER(broad_sector) = LOWER(?)", (sector,))
        match = cursor.fetchone()
        if not match:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")
        
        exact_sector = match[0]
        
        query = """
            SELECT c.id AS company_id, c.company_name, s.broad_sector, s.sub_sector,
                   fr.return_on_equity_pct, fr.debt_to_equity, fr.operating_profit_margin_pct,
                   fr.net_profit_margin_pct, fr.free_cash_flow_cr, fr.revenue_cagr_5yr
            FROM companies c
            JOIN sectors s ON c.id = s.company_id
            LEFT JOIN financial_ratios fr ON c.id = fr.company_id 
                 AND fr.year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = c.id)
            WHERE s.broad_sector = ?
        """
        cursor.execute(query, (exact_sector,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
