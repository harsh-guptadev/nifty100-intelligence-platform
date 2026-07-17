import pytest
import sqlite3
import pandas as pd
from src.analytics.peer import compute_percent_rank, get_company_peer_group, populate_peer_percentiles
from src.screener.engine import get_db_connection

def test_compute_percent_rank():
    # Simple list
    s = pd.Series([10.0, 20.0, 30.0, 40.0])
    ranks = compute_percent_rank(s)
    # Expected SQL PERCENT_RANK: (rank - 1) / (n - 1)
    # Ranks: [1, 2, 3, 4] -> Percentile: [0.0, 0.3333, 0.6666, 1.0]
    assert list(ranks) == [0.0, 1.0/3, 2.0/3, 1.0]

def test_get_company_peer_group():
    # Verify EICHERMOT is in Automobiles
    pg = get_company_peer_group("EICHERMOT")
    assert pg == "Automobiles"
    # Verify invalid company returns 'No peer group assigned'
    pg_invalid = get_company_peer_group("INVALIDCO")
    assert pg_invalid == "No peer group assigned"

def test_it_services_roe_ranking():
    # Within IT Services peer group, the company with highest ROE should have highest ROE rank (1.0)
    conn = get_db_connection()
    try:
        # Fetch latest year percentile rankings for IT Services group
        df_pct = pd.read_sql_query("""
            SELECT company_id, percentile_rank, value 
            FROM peer_percentiles 
            WHERE peer_group_name = 'IT Services' AND metric = 'ROE'
            ORDER BY value DESC
        """, conn)
    finally:
        conn.close()
        
    assert not df_pct.empty
    
    # The highest ROE value should correspond to a percentile_rank of 1.0
    highest_roe_rank = df_pct.iloc[0]["percentile_rank"]
    assert highest_roe_rank == 1.0
