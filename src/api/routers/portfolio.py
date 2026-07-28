import os
import sqlite3
import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

@router.get("/stats")
def get_portfolio_stats():
    # If portfolio_stats.csv exists, return it, else compute dynamically
    csv_path = "output/portfolio_stats.csv"
    if os.path.exists(csv_path):
        df_stats = pd.read_csv(csv_path)
        return df_stats.to_dict(orient="records")
        
    conn = sqlite3.connect(DB_PATH)
    try:
        df_rat = pd.read_sql("SELECT * FROM financial_ratios", conn)
        latest_ratios = df_rat.sort_values("year").groupby("company_id").last().reset_index()
        
        kpi_cols = [
            "return_on_equity_pct", "operating_profit_margin_pct", "net_profit_margin_pct",
            "debt_to_equity", "interest_coverage", "asset_turnover", "earnings_per_share",
            "book_value_per_share", "revenue_cagr_5yr", "free_cash_flow_cr"
        ]
        
        stats_records = []
        for metric in kpi_cols:
            series = pd.to_numeric(latest_ratios[metric], errors="coerce").dropna()
            if not series.empty:
                stats_records.append({
                    "metric": metric,
                    "P10": series.quantile(0.10),
                    "P25": series.quantile(0.25),
                    "P50": series.quantile(0.50),
                    "P75": series.quantile(0.75),
                    "P90": series.quantile(0.90),
                    "Mean": series.mean(),
                    "Std": series.std()
                })
        return stats_records
    finally:
        conn.close()
