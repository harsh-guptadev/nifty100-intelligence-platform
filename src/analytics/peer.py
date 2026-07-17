import os
import sqlite3
import pandas as pd
import numpy as np
from src.screener.engine import get_screener_data, map_cagr_flag_to_numeric, get_db_connection

def get_company_peer_group(company_id: str, conn=None) -> str:
    """Returns the peer group name for a company, or 'No peer group assigned'."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        if row:
            return str(row[0])
        else:
            return "No peer group assigned"
    finally:
        if close_conn:
            conn.close()

def compute_percent_rank(series: pd.Series) -> pd.Series:
    """
    Computes percent rank matching SQL PERCENT_RANK(): (rank - 1) / (n - 1).
    Ranks ties with their minimum rank.
    """
    valid = series.dropna()
    n = len(valid)
    if n <= 1:
        return pd.Series(1.0, index=series.index)
        
    ranks = series.rank(method='min', ascending=True)
    pct_ranks = (ranks - 1.0) / (n - 1.0)
    return pct_ranks

def populate_peer_percentiles() -> int:
    """
    Computes PERCENT_RANK for 10 metrics within each of the 11 peer groups and all years,
    and inserts the results into the peer_percentiles table in SQLite.
    """
    conn = get_db_connection()
    try:
        # Load screener data (includes ROCE, CAGR metrics, etc. for all years)
        df = get_screener_data(conn)
        
        # Load peer groups
        df_pg = pd.read_sql_query("SELECT peer_group_name, company_id FROM peer_groups", conn)
        
        # Merge peer groups
        df = df.merge(df_pg, on="company_id", how="inner")
        
        # Define the 10 metrics to rank
        metrics_mapping = {
            "ROE": "return_on_equity_pct",
            "ROCE": "roce_percentage",
            "Net Profit Margin": "net_profit_margin_pct",
            "D/E": "debt_to_equity",
            "FCF": "free_cash_flow_cr",
            "PAT CAGR 5yr": "pat_cagr_numeric",
            "Revenue CAGR 5yr": "rev_cagr_numeric",
            "EPS CAGR 5yr": "eps_cagr_numeric",
            "Interest Coverage": "interest_coverage",
            "Asset Turnover": "asset_turnover"
        }
        
        # Map CAGR columns to numeric values for percentile ranking
        df['rev_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['revenue_cagr_5yr'], r['revenue_cagr_5yr_flag']), axis=1)
        df['pat_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['pat_cagr_5yr'], r['pat_cagr_5yr_flag']), axis=1)
        df['eps_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['eps_cagr_5yr'], r['eps_cagr_5yr_flag']), axis=1)

        # Clear existing peer_percentiles table
        cursor = conn.cursor()
        cursor.execute("DELETE FROM peer_percentiles;")
        conn.commit()
        
        records_to_insert = []
        
        # Group by peer group and year
        groups = df.groupby(["peer_group_name", "year"])
        
        for (peer_group, year), group in groups:
            for metric_display_name, col_name in metrics_mapping.items():
                series = group[col_name]
                
                # Check for interest coverage Debt Free case
                if metric_display_name == "Interest Coverage":
                    # If icr_label == 'Debt Free', treat as extremely high (infinity)
                    is_df = (group['icr_label'] == 'Debt Free') | (group['interest'].fillna(0.0) == 0.0)
                    series = np.where(is_df, 99999.0, series)
                    series = pd.Series(series, index=group.index)

                # Compute percentile rank
                pct_ranks = compute_percent_rank(series)
                
                # Invert D/E ranking (lower D/E = higher percentile rank)
                if metric_display_name == "D/E":
                    pct_ranks = 1.0 - pct_ranks

                for idx in group.index:
                    comp_id = group.loc[idx, "company_id"]
                    val = group.loc[idx, col_name]
                    # If val is non-numeric, write mapped numeric proxy instead
                    if pd.isna(val) and col_name in ["rev_cagr_numeric", "pat_cagr_numeric", "eps_cagr_numeric"]:
                        val = group.loc[idx, col_name]
                    
                    # Convert values to float or None for SQLite
                    db_val = float(val) if pd.notna(val) else None
                    db_pct = float(pct_ranks.loc[idx]) if pd.notna(pct_ranks.loc[idx]) else None
                    
                    records_to_insert.append((
                        comp_id,
                        peer_group,
                        metric_display_name,
                        db_val,
                        db_pct,
                        year
                    ))
                    
        # Write to DB
        cursor.executemany("""
            INSERT INTO peer_percentiles (
                company_id, peer_group_name, metric, value, percentile_rank, year
            ) VALUES (?, ?, ?, ?, ?, ?);
        """, records_to_insert)
        conn.commit()
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM peer_percentiles;")
        count = cursor.fetchone()[0]
        
    finally:
        conn.close()
        
    return count
