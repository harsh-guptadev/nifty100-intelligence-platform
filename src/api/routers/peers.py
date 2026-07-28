import os
import sqlite3
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Peers"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/peers/{group_name}")
def get_peer_group_details(group_name: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT peer_group_name FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?)", (group_name,))
        match = cursor.fetchone()
        if not match:
            raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
        
        exact_group = match[0]
        
        query = """
            SELECT pp.company_id, pp.metric, pp.value, pp.percentile_rank, pp.year, pg.is_benchmark
            FROM peer_percentiles pp
            JOIN peer_groups pg ON pp.company_id = pg.company_id AND pp.peer_group_name = pg.peer_group_name
            WHERE pp.peer_group_name = ?
            ORDER BY pp.company_id, pp.metric
        """
        cursor.execute(query, (exact_group,))
        rows = cursor.fetchall()
        
        results = {}
        for r in rows:
            cid = r["company_id"]
            if cid not in results:
                results[cid] = {
                    "company_id": cid,
                    "peer_group_name": exact_group,
                    "is_benchmark": bool(r["is_benchmark"]),
                    "metrics": {}
                }
            results[cid]["metrics"][r["metric"]] = {
                "value": r["value"],
                "percentile_rank": r["percentile_rank"]
            }
        return list(results.values())
    finally:
        conn.close()

@router.get("/companies/{ticker}/peers/compare")
def get_peer_radar_comparison(ticker: str):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE LOWER(id) = LOWER(?)", (ticker,))
        comp = cursor.fetchone()
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
            
        exact_ticker = comp[0]
        
        # Get company's peer group
        cursor.execute("SELECT peer_group_name, is_benchmark FROM peer_groups WHERE company_id = ?", (exact_ticker,))
        pg_row = cursor.fetchone()
        peer_group_name = pg_row["peer_group_name"] if pg_row else "Nifty100"
        
        # Fetch 8 axis metrics from peer_percentiles for target company
        cursor.execute("""
            SELECT metric, value, percentile_rank 
            FROM peer_percentiles 
            WHERE company_id = ? AND peer_group_name = ?
        """, (exact_ticker, peer_group_name))
        comp_metrics = cursor.fetchall()
        
        comp_radar = {r["metric"]: r["percentile_rank"] for r in comp_metrics}
        
        # Fetch peer group averages
        cursor.execute("""
            SELECT metric, AVG(percentile_rank) AS avg_rank 
            FROM peer_percentiles 
            WHERE peer_group_name = ? 
            GROUP BY metric
        """, (peer_group_name,))
        avg_metrics = cursor.fetchall()
        peer_avg_radar = {r["metric"]: round(r["avg_rank"], 2) for r in avg_metrics}
        
        # Fetch benchmark company in peer group
        cursor.execute("""
            SELECT company_id FROM peer_groups 
            WHERE peer_group_name = ? AND is_benchmark = 1 LIMIT 1
        """, (peer_group_name,))
        bm_row = cursor.fetchone()
        bm_ticker = bm_row[0] if bm_row else "NIFTY100_AVG"
        
        bm_radar = {}
        if bm_row:
            cursor.execute("""
                SELECT metric, percentile_rank 
                FROM peer_percentiles 
                WHERE company_id = ? AND peer_group_name = ?
            """, (bm_ticker, peer_group_name))
            bm_metrics = cursor.fetchall()
            bm_radar = {r["metric"]: r["percentile_rank"] for r in bm_metrics}

        return {
            "company_id": exact_ticker,
            "peer_group_name": peer_group_name,
            "benchmark_ticker": bm_ticker,
            "company_radar": comp_radar,
            "peer_avg_radar": peer_avg_radar,
            "benchmark_radar": bm_radar
        }
    finally:
        conn.close()
