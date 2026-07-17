import os
import yaml
import sqlite3
import pandas as pd
import numpy as np
from src.analytics.cagr import compute_cagr

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def load_screener_config(config_path="config/screener_config.yaml") -> dict:
    """Loads screener configurations from YAML file."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_screener_data(conn=None) -> pd.DataFrame:
    """
    Pulls raw and calculated metrics for all companies and years, 
    joining tables: companies, sectors, financial_ratios, market_cap, profitandloss, balancesheet, cashflow.
    Calculates ROCE, Revenue CAGR 3yr, FCF CAGR 5yr, and other needed intermediate metrics.
    """
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
        
    try:
        # Load tables
        df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        df_companies = pd.read_sql_query("SELECT id, company_name FROM companies", conn)
        df_sectors = pd.read_sql_query("SELECT * FROM sectors", conn)
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        df_cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
        df_mcap = pd.read_sql_query("SELECT * FROM market_cap", conn)
    finally:
        if close_conn:
            conn.close()

    # Rename key columns in PL, BS, CF to avoid overlaps
    df_pl = df_pl.rename(columns={'id': 'pl_row_id'})
    df_bs = df_bs.rename(columns={'id': 'bs_row_id'})
    df_cf = df_cf.rename(columns={'id': 'cf_row_id'})
    df_mcap = df_mcap.rename(columns={'id': 'mcap_row_id'})

    # Merge core datasets
    df = df_ratios.merge(df_companies, left_on="company_id", right_on="id", how="left")
    df = df.merge(df_sectors, on="company_id", how="left")
    df = df.merge(df_pl, on=["company_id", "year"], how="left")
    df = df.merge(df_bs, on=["company_id", "year"], how="left")
    df = df.merge(df_cf, on=["company_id", "year"], how="left")
    df = df.merge(df_mcap, on=["company_id", "year"], how="left")

    # Compute ROCE: EBIT / (equity_capital + reserves + borrowings) * 100
    # EBIT = operating_profit - depreciation
    op_profit = df['operating_profit'].fillna(0.0)
    depr = df['depreciation'].fillna(0.0)
    ebit = op_profit - depr
    capital_employed = df['equity_capital'].fillna(0.0) + df['reserves'].fillna(0.0) + df['borrowings'].fillna(0.0)
    df['roce_percentage'] = np.where(capital_employed > 0, (ebit / capital_employed) * 100.0, np.nan)

    # Sort to compute rolling/CAGR values
    df = df.sort_values(by=["company_id", "year"]).reset_index(drop=True)

    # Calculate 3yr Revenue CAGR and 5yr FCF CAGR, plus YoY D/E declining flag
    # We will build maps to look up values historically
    sales_map = {}
    fcf_map = {}
    de_map = {}
    
    for idx, row in df.iterrows():
        comp = row['company_id']
        yr = row['year']
        sales_map[(comp, yr)] = row.get('sales')
        fcf_map[(comp, yr)] = row.get('free_cash_flow_cr')
        de_map[(comp, yr)] = row.get('debt_to_equity')

    rev_cagr_3yr_list = []
    fcf_cagr_5yr_list = []
    fcf_cagr_5yr_flag_list = []
    de_declining_yoy_list = []

    for idx, row in df.iterrows():
        comp = row['company_id']
        yr = row['year']
        
        # 1. 3yr Revenue CAGR
        try:
            curr_yr = int(yr[:4])
            start_yr_str_3 = f"{curr_yr - 3}{yr[4:]}"
            base_sales = sales_map.get((comp, start_yr_str_3))
            end_sales = row.get('sales')
            if pd.notna(base_sales) and pd.notna(end_sales) and base_sales > 0 and end_sales > 0:
                cagr3 = ((end_sales / base_sales) ** (1.0 / 3) - 1.0) * 100.0
                rev_cagr_3yr_list.append(cagr3)
            else:
                rev_cagr_3yr_list.append(np.nan)
        except Exception:
            rev_cagr_3yr_list.append(np.nan)

        # 2. 5yr FCF CAGR
        try:
            start_yr_str_5 = f"{curr_yr - 5}{yr[4:]}"
            base_fcf = fcf_map.get((comp, start_yr_str_5))
            end_fcf = row.get('free_cash_flow_cr')
            cval, cflag = compute_cagr(base_fcf, end_fcf, 5)
            fcf_cagr_5yr_list.append(cval)
            fcf_cagr_5yr_flag_list.append(cflag)
        except Exception:
            fcf_cagr_5yr_list.append(np.nan)
            fcf_cagr_5yr_flag_list.append("ERROR")

        # 3. D/E Declining YoY
        try:
            start_yr_str_1 = f"{curr_yr - 1}{yr[4:]}"
            prev_de = de_map.get((comp, start_yr_str_1))
            curr_de = row.get('debt_to_equity')
            if pd.notna(prev_de) and pd.notna(curr_de):
                de_declining_yoy_list.append(curr_de < prev_de)
            else:
                de_declining_yoy_list.append(False)
        except Exception:
            de_declining_yoy_list.append(False)

    df['revenue_cagr_3yr'] = rev_cagr_3yr_list
    df['fcf_cagr_5yr'] = fcf_cagr_5yr_list
    df['fcf_cagr_5yr_flag'] = fcf_cagr_5yr_flag_list
    df['de_declining_yoy'] = de_declining_yoy_list

    return df

def winsorize_and_scale(series: pd.Series, lower_quantile: float = 0.1, upper_quantile: float = 0.9, invert: bool = False) -> pd.Series:
    """
    Winsorizes a numeric series by capping at P10/P90, then scales to 0-100.
    Inverts if invert=True (lower is better, e.g., D/E).
    """
    valid = series.dropna()
    if len(valid) == 0:
        return pd.Series(0.0, index=series.index)
        
    p10 = valid.quantile(lower_quantile)
    p90 = valid.quantile(upper_quantile)
    
    if p90 == p10:
        return pd.Series(100.0, index=series.index)
        
    capped = series.clip(lower=p10, upper=p90)
    
    if invert:
        scaled = (p90 - capped) / (p90 - p10) * 100.0
    else:
        scaled = (capped - p10) / (p90 - p10) * 100.0
        
    return scaled

# CAGR proxy choices rationale:
# - TURNAROUND (+15.0): A transition from loss to profit is a strong positive signal.
#   A +15% growth rate proxy rewards the company's turnaround performance.
# - DECLINE_TO_LOSS (-15.0): Shifting from positive profit/revenue to loss is a severe decline.
#   A -15% proxy penalizes this negative trend appropriately.
# - BOTH_NEGATIVE (-10.0): Staying negative across both periods is a persistent drag on growth.
#   A -10% proxy reflects this negative performance.
# - ZERO_BASE (0.0): Base value of zero makes growth undefined; a neutral 0% proxy is used.
def map_cagr_flag_to_numeric(val: float, flag: str) -> float:
    """Maps non-numeric CAGR flags to numeric proxies for winsorization."""
    if pd.notna(val):
        return float(val)
    if pd.isna(flag) or str(flag).strip() == "":
        return 0.0
    
    flag_str = str(flag).upper().strip()
    if flag_str == "TURNAROUND":
        return 15.0
    elif flag_str == "DECLINE_TO_LOSS":
        return -15.0
    elif flag_str == "BOTH_NEGATIVE":
        return -10.0
    elif flag_str == "ZERO_BASE":
        return 0.0
    return 0.0

def compute_sector_relative_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes winsorized and scaled composite quality score per sector & year.
    Returns DataFrame with updated scores.
    """
    df = df.copy()
    
    # 1. Map CAGR flags to numeric proxies
    df['rev_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['revenue_cagr_5yr'], r['revenue_cagr_5yr_flag']), axis=1)
    df['pat_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['pat_cagr_5yr'], r['pat_cagr_5yr_flag']), axis=1)
    df['fcf_cagr_numeric'] = df.apply(lambda r: map_cagr_flag_to_numeric(r['fcf_cagr_5yr'], r['fcf_cagr_5yr_flag']), axis=1)

    # 2. Compute CFO/PAT ratio
    # If PAT > 0: cfo / pat
    # If PAT <= 0: 1.0 if cfo > 0 else 0.0
    cfo = df['cash_from_operations_cr'].fillna(0.0)
    pat = df['net_profit'].fillna(0.0)
    df['cfo_pat_ratio'] = np.where(pat > 0, cfo / pat, np.where(cfo > 0, 1.0, 0.0))

    # 3. FCF positive flag: 100 if FCF > 0 else 0
    fcf = df['free_cash_flow_cr'].fillna(0.0)
    df['fcf_positive_score'] = np.where(fcf > 0, 100.0, 0.0)

    # 4. Group by year and broad_sector to winsorize and scale
    df['roe_score'] = np.nan
    df['roce_score'] = np.nan
    df['npm_score'] = np.nan
    df['fcf_cagr_score'] = np.nan
    df['cfo_pat_score'] = np.nan
    df['rev_cagr_score'] = np.nan
    df['pat_cagr_score'] = np.nan
    df['de_score'] = np.nan
    df['icr_score'] = np.nan

    groups = df.groupby(['year', 'broad_sector'])
    for name, group in groups:
        indices = group.index
        
        # Profitability
        df.loc[indices, 'roe_score'] = winsorize_and_scale(group['return_on_equity_pct'])
        df.loc[indices, 'roce_score'] = winsorize_and_scale(group['roce_percentage'])
        df.loc[indices, 'npm_score'] = winsorize_and_scale(group['net_profit_margin_pct'])
        
        # Cash Quality
        df.loc[indices, 'fcf_cagr_score'] = winsorize_and_scale(group['fcf_cagr_numeric'])
        df.loc[indices, 'cfo_pat_score'] = winsorize_and_scale(group['cfo_pat_ratio'])
        
        # Growth
        df.loc[indices, 'rev_cagr_score'] = winsorize_and_scale(group['rev_cagr_numeric'])
        df.loc[indices, 'pat_cagr_score'] = winsorize_and_scale(group['pat_cagr_numeric'])
        
        # Leverage
        df.loc[indices, 'de_score'] = winsorize_and_scale(group['debt_to_equity'], invert=True)
        df.loc[indices, 'icr_score'] = winsorize_and_scale(group['interest_coverage'])

    # Fill NaNs with 0
    score_cols = ['roe_score', 'roce_score', 'npm_score', 'fcf_cagr_score', 'cfo_pat_score', 'rev_cagr_score', 'pat_cagr_score', 'de_score', 'icr_score']
    for col in score_cols:
        df[col] = df[col].fillna(0.0)

    # Apply Overrides
    # ICR Override: if icr_label == 'Debt Free' or interest coverage is null/infinite, icr_score = 100.0
    is_debt_free = (df['icr_label'] == 'Debt Free') | (df['interest_coverage'].isna()) | (df['interest'].fillna(0.0) == 0.0)
    df.loc[is_debt_free, 'icr_score'] = 100.0

    # Calculate Composite Score:
    # 35% Profitability: (ROE 15% + ROCE 10% + NPM 10%)
    # 30% Cash Quality: (FCF CAGR 15% + CFO/PAT ratio 10% + FCF positive flag 5%)
    # 20% Growth: (Revenue CAGR 10% + PAT CAGR 10%)
    # 15% Leverage: (D/E score 10% + ICR score 5%)
    df['composite_quality_score'] = (
        0.15 * df['roe_score'] + 0.10 * df['roce_score'] + 0.10 * df['npm_score'] +
        0.15 * df['fcf_cagr_score'] + 0.10 * df['cfo_pat_score'] + 0.05 * df['fcf_positive_score'] +
        0.10 * df['rev_cagr_score'] + 0.10 * df['pat_cagr_score'] +
        0.10 * df['de_score'] + 0.05 * df['icr_score']
    )

    return df

def update_composite_scores_in_db() -> int:
    """Computes composite quality scores and writes them back to the financial_ratios table."""
    conn = get_db_connection()
    try:
        df_raw = get_screener_data(conn)
        df_scored = compute_sector_relative_scores(df_raw)
        
        cursor = conn.cursor()
        updated_count = 0
        for _, row in df_scored.iterrows():
            comp_id = row['company_id']
            yr = row['year']
            score = float(row['composite_quality_score'])
            
            cursor.execute(
                "UPDATE financial_ratios SET composite_quality_score = ? WHERE company_id = ? AND year = ?",
                (score, comp_id, yr)
            )
            updated_count += 1
            
        conn.commit()
    finally:
        conn.close()
    return updated_count

def apply_filters(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """
    Applies custom or preset criteria filters to the financial ratios DataFrame.
    Returns filtered DataFrame.
    """
    filtered = df.copy()
    
    # Track which columns we are filtering by to evaluate Green/Red fills later
    # Format of filter_matches: {index: {col_name: True/False}}
    filter_matches = {idx: {} for idx in filtered.index}

    for key, val in criteria.items():
        if val is None:
            continue
            
        # 1. ROE min
        if key == "return_on_equity_pct_min":
            matched = filtered['return_on_equity_pct'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['return_on_equity_pct'] = matched.loc[idx]
            filtered = filtered[matched]

        # 2. D/E max (financials skipped)
        elif key == "debt_to_equity_max":
            is_fin = filtered['broad_sector'].fillna("").str.lower() == "financials"
            matched = (filtered['debt_to_equity'].fillna(999.0) <= val) | is_fin
            for idx in filtered.index:
                filter_matches[idx]['debt_to_equity'] = matched.loc[idx]
            filtered = filtered[matched]

        # 3. FCF min
        elif key == "free_cash_flow_cr_min":
            matched = filtered['free_cash_flow_cr'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['free_cash_flow_cr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 4. Revenue CAGR 5yr min
        elif key == "revenue_cagr_5yr_min":
            # Map flags first to evaluate min check
            mapped_rev = filtered.apply(lambda r: map_cagr_flag_to_numeric(r['revenue_cagr_5yr'], r['revenue_cagr_5yr_flag']), axis=1)
            matched = mapped_rev >= val
            for idx in filtered.index:
                filter_matches[idx]['revenue_cagr_5yr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 5. PAT CAGR 5yr min
        elif key == "pat_cagr_5yr_min":
            mapped_pat = filtered.apply(lambda r: map_cagr_flag_to_numeric(r['pat_cagr_5yr'], r['pat_cagr_5yr_flag']), axis=1)
            matched = mapped_pat >= val
            for idx in filtered.index:
                filter_matches[idx]['pat_cagr_5yr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 6. OPM min
        elif key == "operating_profit_margin_pct_min":
            matched = filtered['operating_profit_margin_pct'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['operating_profit_margin_pct'] = matched.loc[idx]
            filtered = filtered[matched]

        # 7. P/E max
        elif key == "pe_ratio_max":
            matched = filtered['pe_ratio'].fillna(999.0) <= val
            for idx in filtered.index:
                filter_matches[idx]['pe_ratio'] = matched.loc[idx]
            filtered = filtered[matched]

        # 8. P/B max
        elif key == "pb_ratio_max":
            matched = filtered['pb_ratio'].fillna(999.0) <= val
            for idx in filtered.index:
                filter_matches[idx]['pb_ratio'] = matched.loc[idx]
            filtered = filtered[matched]

        # 9. Dividend Yield min
        elif key == "dividend_yield_pct_min":
            matched = filtered['dividend_yield_pct'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['dividend_yield_pct'] = matched.loc[idx]
            filtered = filtered[matched]

        # 10. ICR min
        elif key == "interest_coverage_min":
            is_df = (filtered['icr_label'] == 'Debt Free') | (filtered['interest'].fillna(0.0) == 0.0)
            matched = (filtered['interest_coverage'].fillna(-999.0) >= val) | is_df
            for idx in filtered.index:
                filter_matches[idx]['interest_coverage'] = matched.loc[idx]
            filtered = filtered[matched]

        # 11. Market Cap min
        elif key == "market_cap_crore_min":
            matched = filtered['market_cap_crore'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['market_cap_crore'] = matched.loc[idx]
            filtered = filtered[matched]

        # 12. Net Profit min
        elif key == "net_profit_min":
            matched = filtered['net_profit'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['net_profit'] = matched.loc[idx]
            filtered = filtered[matched]

        # 13. EPS CAGR min
        elif key == "eps_cagr_5yr_min":
            mapped_eps = filtered.apply(lambda r: map_cagr_flag_to_numeric(r['eps_cagr_5yr'], r['eps_cagr_5yr_flag']), axis=1)
            matched = mapped_eps >= val
            for idx in filtered.index:
                filter_matches[idx]['eps_cagr_5yr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 14. Asset Turnover min
        elif key == "asset_turnover_min":
            matched = filtered['asset_turnover'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['asset_turnover'] = matched.loc[idx]
            filtered = filtered[matched]

        # 15. Sales min
        elif key == "sales_min":
            matched = filtered['sales'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['sales'] = matched.loc[idx]
            filtered = filtered[matched]

        # 16. Revenue CAGR 3yr min (Turnaround Watch specific)
        elif key == "revenue_cagr_3yr_min":
            matched = filtered['revenue_cagr_3yr'].fillna(-999.0) >= val
            for idx in filtered.index:
                filter_matches[idx]['revenue_cagr_3yr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 17. FCF positive latest (Turnaround Watch specific)
        elif key == "fcf_positive_latest":
            matched = filtered['free_cash_flow_cr'].fillna(-999.0) > 0
            for idx in filtered.index:
                filter_matches[idx]['free_cash_flow_cr'] = matched.loc[idx]
            filtered = filtered[matched]

        # 18. D/E declining YoY (Turnaround Watch specific)
        elif key == "de_declining_yoy":
            matched = filtered['de_declining_yoy'] == True
            for idx in filtered.index:
                filter_matches[idx]['de_declining_yoy'] = matched.loc[idx]
            filtered = filtered[matched]

        # 19. Dividend Payout Max (Dividend Champion specific)
        elif key == "dividend_payout_ratio_pct_max":
            matched = filtered['dividend_payout_ratio_pct'].fillna(999.0) <= val
            for idx in filtered.index:
                filter_matches[idx]['dividend_payout_ratio_pct'] = matched.loc[idx]
            filtered = filtered[matched]

    # Save validation highlights mapping onto the DataFrame itself
    filtered = filtered.copy()
    filtered['_filter_matches'] = [filter_matches[idx] for idx in filtered.index]

    return filtered

def run_preset_screener(preset_name: str, df: pd.DataFrame = None) -> pd.DataFrame:
    """Runs a preset screener by name, returning the sorted results for the latest year."""
    config = load_screener_config()
    presets = config.get("presets", {})
    if preset_name not in presets:
        raise ValueError(f"Preset '{preset_name}' not found in screener config.")
        
    criteria = presets[preset_name]
    
    if df is None:
        df = get_screener_data()
        df = compute_sector_relative_scores(df)

    # Filter to only the LATEST year per company
    # The latest year is the maximum year with non-null return_on_equity_pct, falling back to absolute latest year
    df_valid = df[df['return_on_equity_pct'].notna()]
    if not df_valid.empty:
        latest_indices = df_valid.groupby("company_id")["year"].idxmax()
        missing_cos = set(df['company_id']) - set(df_valid['company_id'])
        if missing_cos:
            df_missing = df[df['company_id'].isin(missing_cos)]
            missing_indices = df_missing.groupby("company_id")["year"].idxmax()
            all_indices = pd.concat([latest_indices, missing_indices])
        else:
            all_indices = latest_indices
        df_latest = df.loc[all_indices].copy()
    else:
        df_latest = df[df.groupby("company_id")["year"].transform("max") == df["year"]].copy()

    # Apply filters
    results = apply_filters(df_latest, criteria)

    # Sort by composite_quality_score descending
    results = results.sort_values(by="composite_quality_score", ascending=False)
    return results
