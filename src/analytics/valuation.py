import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def compute_valuation_flag(row) -> str:
    """
    Applies valuation flag logic based on P/E vs sector median P/E:
    - Caution: P/E > sector_median * 1.5
    - Discount: P/E < sector_median * 0.7
    - Fair: otherwise
    """
    pe = row.get("pe_ratio")
    sector_pe = row.get("sector_median_pe")
    
    if pd.isna(pe) or pd.isna(sector_pe) or sector_pe <= 0:
        return "Fair"
        
    if pe > sector_pe * 1.5:
        return "Caution"
    elif pe < sector_pe * 0.7:
        return "Discount"
    else:
        return "Fair"

def run_valuation_module() -> pd.DataFrame:
    """
    Computes FCF Yield, sector median P/E, P/E vs sector percentage, and overvaluation flags.
    Generates output/valuation_summary.xlsx and output/valuation_flags.csv.
    Saves results to the 'valuation' table in SQLite.
    """
    conn = get_db_connection()
    try:
        # Load tables
        df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        df_companies = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
        df_sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
        df_mcap = pd.read_sql_query("SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio, ev_ebitda FROM market_cap", conn)
    finally:
        conn.close()

    # Filter/Sort to keep latest year data per company
    df_ratios_latest = df_ratios.sort_values("year").groupby("company_id", as_index=False).last()
    df_mcap_latest = df_mcap.sort_values("year").groupby("company_id", as_index=False).last()

    # Merge company metadata and ratios with market cap data
    df = df_companies.merge(df_sectors, on="company_id", how="left")
    df = df.merge(df_ratios_latest[["company_id", "free_cash_flow_cr"]], on="company_id", how="left")
    df = df.merge(df_mcap_latest, on="company_id", how="left")

    # 1. FCF Yield (%) = (free_cash_flow_cr / market_cap_crore) * 100
    df["fcf_yield_pct"] = np.where(
        (df["market_cap_crore"].notna()) & (df["market_cap_crore"] > 0) & (df["free_cash_flow_cr"].notna()),
        (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100.0,
        np.nan
    )

    # 2. Sector Median P/E
    sector_median_pe = df.groupby("broad_sector")["pe_ratio"].median().to_dict()
    df["sector_median_pe"] = df["broad_sector"].map(sector_median_pe)

    # 3. P/E vs Sector Median (%)
    df["pe_vs_sector_pct"] = np.where(
        (df["pe_ratio"].notna()) & (df["sector_median_pe"].notna()) & (df["sector_median_pe"] > 0),
        (df["pe_ratio"] / df["sector_median_pe"]) * 100.0,
        np.nan
    )

    # 4. Valuation Flag (Caution / Discount / Fair)
    df["flag"] = df.apply(compute_valuation_flag, axis=1)

    # Select final columns
    output_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "market_cap_crore",
        "free_cash_flow_cr",
        "fcf_yield_pct",
        "sector_median_pe",
        "pe_vs_sector_pct",
        "flag"
    ]
    df_summary = df[output_cols].copy()

    # Export Files
    os.makedirs("output", exist_ok=True)
    
    # 1. output/valuation_summary.xlsx
    df_summary.to_excel("output/valuation_summary.xlsx", index=False)
    
    # 2. output/valuation_flags.csv (Only Caution and Discount)
    df_flags = df_summary[df_summary["flag"].isin(["Caution", "Discount"])].copy()
    df_flags.to_csv("output/valuation_flags.csv", index=False)

    # 3. Save to SQLite table 'valuation'
    conn = get_db_connection()
    try:
        df_summary.to_sql("valuation", conn, if_exists="replace", index=False)
    finally:
        conn.close()

    print(f"Valuation module executed successfully. Processed {len(df_summary)} companies.")
    print(f"- Caution: {len(df_summary[df_summary['flag'] == 'Caution'])}")
    print(f"- Discount: {len(df_summary[df_summary['flag'] == 'Discount'])}")
    print(f"- Fair: {len(df_summary[df_summary['flag'] == 'Fair'])}")

    return df_summary

if __name__ == "__main__":
    run_valuation_module()
