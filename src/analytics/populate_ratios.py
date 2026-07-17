import sqlite3
import pandas as pd
import numpy as np
import os
from src.analytics.ratios import (
    compute_npm,
    compute_opm,
    compute_roe,
    compute_roce,
    compute_roa,
    compute_de,
    compute_icr,
    compute_net_debt,
    compute_asset_turnover
)
from src.analytics.cagr import compute_cagr
from src.analytics.cashflow_kpis import (
    compute_fcf,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation
)

DB_PATH = 'data/nifty100.db'
EDGE_CASES_LOG = 'output/ratio_edge_cases.log'
CAPITAL_ALLOCATION_CSV = 'output/capital_allocation.csv'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_logging():
    os.makedirs('output', exist_ok=True)
    # Clear logs from previous runs
    if os.path.exists(EDGE_CASES_LOG):
        os.remove(EDGE_CASES_LOG)

def log_anomaly(message: str):
    with open(EDGE_CASES_LOG, 'a', encoding='utf-8') as f:
        f.write(message + "\n")

def populate_all_ratios():
    setup_logging()
    conn = get_db_connection()
    
    # 1. Fetch all companies and their sectors + source ROE/ROCE for cross checks
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.company_name, c.face_value, s.broad_sector, c.roce_percentage, c.roe_percentage
        FROM companies c 
        LEFT JOIN sectors s ON c.id = s.company_id
    """)
    companies = cursor.fetchall()
    
    # We will accumulate temporary computed rows to calculate sector-relative ROCE medians dynamically
    computed_rows = []
    
    # Clear existing financial_ratios table
    cursor.execute("DELETE FROM financial_ratios;")
    conn.commit()
    
    print("=== Processing financial ratios and CAGR engine ===")
    
    for ticker, name, face_value, sector, roce_source, roe_source in companies:
        if not face_value:
            face_value = 1.0 # Default fallback if missing
            
        # Fetch statements
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id=?", conn, params=(ticker,))
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id=?", conn, params=(ticker,))
        df_cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id=?", conn, params=(ticker,))
        
        if df_pl.empty:
            continue
            
        # Align statements by year
        df_merged = df_pl.merge(df_bs, on=['company_id', 'year'], how='outer', suffixes=('', '_bs'))
        df_merged = df_merged.merge(df_cf, on=['company_id', 'year'], how='outer', suffixes=('', '_cf'))
        df_merged = df_merged.sort_values('year').reset_index(drop=True)
        
        # Create lookups for CAGR calculations
        sales_map = {row['year']: row['sales'] for _, row in df_merged.iterrows() if pd.notna(row['sales'])}
        profit_map = {row['year']: row['net_profit'] for _, row in df_merged.iterrows() if pd.notna(row['net_profit'])}
        eps_map = {row['year']: row['eps'] for _, row in df_merged.iterrows() if pd.notna(row['eps'])}
        
        latest_year = df_merged.iloc[-1]['year'] if not df_merged.empty else None
        
        # Process each year for the company
        for idx, row in df_merged.iterrows():
            year = row['year']
            
            # Check for NaN and extract raw variables
            sales = row.get('sales')
            net_profit = row.get('net_profit')
            operating_profit = row.get('operating_profit')
            depreciation = row.get('depreciation', 0.0)
            other_income = row.get('other_income', 0.0)
            interest = row.get('interest', 0.0)
            equity_capital = row.get('equity_capital')
            reserves = row.get('reserves')
            borrowings = row.get('borrowings')
            investments = row.get('investments', 0.0)
            total_assets = row.get('total_assets')
            eps = row.get('eps')
            dividend_payout = row.get('dividend_payout', 0.0)
            operating_activity = row.get('operating_activity')
            investing_activity = row.get('investing_activity')
            financing_activity = row.get('financing_activity')
            
            # 1. Profitability Calculations
            npm = compute_npm(net_profit, sales)
            opm = compute_opm(operating_profit, sales)
            
            # OPM Cross check vs raw OPM
            raw_opm = row.get('opm_percentage')
            if opm is not None and pd.notna(raw_opm):
                if abs(opm - raw_opm) >= 1.0:
                    log_anomaly(
                        f"[OPM Mismatch] {ticker} {year}: Computed OPM={opm:.2f}%, Source OPM={raw_opm:.2f}% (diff={abs(opm-raw_opm):.2f}%) [Category: formula discrepancy]"
                    )
            
            # EBIT calculation
            op_profit_val = operating_profit if pd.notna(operating_profit) else 0.0
            deprec_val = depreciation if pd.notna(depreciation) else 0.0
            ebit = op_profit_val - deprec_val
            
            roe = compute_roe(net_profit, equity_capital, reserves)
            roce = compute_roce(ebit, equity_capital, reserves, borrowings)
            roa = compute_roa(net_profit, total_assets)
            
            # 2. Leverage Calculations
            de = compute_de(borrowings, equity_capital, reserves)
            
            # Suppress high leverage warnings for Financials sector
            high_leverage_flag = 0
            if de is not None and de > 5.0:
                sector_cleaned = sector.strip() if sector else ""
                if sector_cleaned.lower() != "financials":
                    high_leverage_flag = 1
                    log_anomaly(
                        f"[High Leverage Alert] {ticker} {year}: D/E ratio = {de:.2f} (Non-Financials sector)"
                    )
                    
            # Pass raw operating_profit instead of ebit to compute_icr as per spec formula
            icr = compute_icr(operating_profit, other_income, interest)
            icr_label = "Debt Free" if (interest == 0 or pd.isna(interest)) else None
            
            # Flag low ICR risk
            if icr is not None and icr < 1.5:
                log_anomaly(f"[Low ICR Warning] {ticker} {year}: ICR = {icr:.2f} (Below 1.5x safe threshold)")
                
            asset_turnover = compute_asset_turnover(sales, total_assets)
            
            # 3. Cash Flow Calculations
            fcf = compute_fcf(operating_activity, investing_activity)
            capex = abs(investing_activity) if pd.notna(investing_activity) else None
            
            # 4. Book Value per Share Calculation
            bvps = None
            if pd.notna(equity_capital) and pd.notna(reserves) and equity_capital > 0:
                num_shares = equity_capital / face_value
                if num_shares > 0:
                    bvps = (equity_capital + reserves) / num_shares
                    
            # 5. CAGR calculations (Look back 5 years)
            rev_cagr = None
            rev_flag = None
            pat_cagr = None
            pat_flag = None
            eps_cagr = None
            eps_flag = None
            
            try:
                t_year = int(year[:4])
                start_year_str = f"{t_year - 5}{year[4:]}"
                
                # Revenue CAGR
                if start_year_str in sales_map:
                    rev_cagr, rev_flag = compute_cagr(sales_map[start_year_str], sales, 5)
                    if rev_flag:
                        log_anomaly(f"[CAGR Edge Case] {ticker} {year} Revenue 5Y: {rev_flag} (Base={sales_map[start_year_str]}, End={sales}) [Category: version difference]")
                        
                # PAT CAGR
                if start_year_str in profit_map:
                    pat_cagr, pat_flag = compute_cagr(profit_map[start_year_str], net_profit, 5)
                    if pat_flag:
                        log_anomaly(f"[CAGR Edge Case] {ticker} {year} PAT 5Y: {pat_flag} (Base={profit_map[start_year_str]}, End={net_profit}) [Category: version difference]")
                        
                # EPS CAGR
                if start_year_str in eps_map:
                    eps_cagr, eps_flag = compute_cagr(eps_map[start_year_str], eps, 5)
                    if eps_flag:
                        log_anomaly(f"[CAGR Edge Case] {ticker} {year} EPS 5Y: {eps_flag} (Base={eps_map[start_year_str]}, End={eps}) [Category: version difference]")
            except Exception as e:
                pass
                
            # Cross-check latest ROE/ROCE vs pre-computed companies master list
            if year == latest_year:
                if roe is not None and roe_source is not None and pd.notna(roe_source):
                    if abs(roe - roe_source) > 5.0:
                        log_anomaly(f"[ROE Source Mismatch] {ticker} {year}: Computed ROE={roe:.2f}%, Source ROE={roe_source:.2f}% (diff={abs(roe-roe_source):.2f}%) [Category: data source issue]")
                if roce is not None and roce_source is not None and pd.notna(roce_source):
                    if abs(roce - roce_source) > 5.0:
                        log_anomaly(f"[ROCE Source Mismatch] {ticker} {year}: Computed ROCE={roce:.2f}%, Source ROCE={roce_source:.2f}% (diff={abs(roce-roce_source):.2f}%) [Category: data source issue]")

            computed_rows.append({
                'company_id': ticker,
                'company_name': name,
                'year': year,
                'npm': npm,
                'opm': opm,
                'roe': roe,
                'roce': roce,
                'roa': roa,
                'de': de,
                'icr': icr,
                'asset_turnover': asset_turnover,
                'fcf': fcf,
                'capex': capex,
                'eps': eps,
                'bvps': bvps,
                'dividend_payout': dividend_payout,
                'borrowings': borrowings if pd.notna(borrowings) else None,
                'operating_activity': operating_activity if pd.notna(operating_activity) else None,
                'investing_activity': investing_activity if pd.notna(investing_activity) else None,
                'financing_activity': financing_activity if pd.notna(financing_activity) else None,
                'rev_cagr': rev_cagr,
                'rev_flag': rev_flag,
                'pat_cagr': pat_cagr,
                'pat_flag': pat_flag,
                'eps_cagr': eps_cagr,
                'eps_flag': eps_flag,
                'icr_label': icr_label,
                'high_leverage_flag': high_leverage_flag,
                'sector': sector or "Unknown",
                'net_profit': net_profit
            })
            
    # Calculate Dynamic Sector ROCE medians per year for anomaly detection
    df_temp = pd.DataFrame(computed_rows)
    df_valid_roce = df_temp[df_temp['roce'].notna()]
    roce_medians = df_valid_roce.groupby(['sector', 'year'])['roce'].median().to_dict()
    
    ratio_records = []
    capital_allocation_rows = []
    
    # Process final lists, apply ROCE benchmark checks and build capital allocation rows
    for r in computed_rows:
        ticker = r['company_id']
        year = r['year']
        roce = r['roce']
        sector_str = r['sector']
        
        # Apply ROCE benchmark checks
        if roce is not None:
            if sector_str.strip().lower() == "financials":
                benchmark = roce_medians.get((sector_str, year), 7.93)
                if roce < benchmark:
                    log_anomaly(
                        f"[Low ROCE Warning] {ticker} {year}: ROCE = {roce:.2f}% (Below sector-relative benchmark of {benchmark:.2f}%)"
                    )
            else:
                if roce < 10.0:
                    log_anomaly(
                        f"[Low ROCE Warning] {ticker} {year}: ROCE = {roce:.2f}% (Below 10.0% safe threshold)"
                    )
                    
        # Accumulate ratios database records
        ratio_records.append((
            ticker,
            year,
            r['npm'],
            r['opm'],
            r['roe'],
            r['de'],
            r['icr'],
            r['asset_turnover'],
            r['fcf'],
            r['capex'],
            r['eps'],
            r['bvps'],
            r['dividend_payout'],
            r['borrowings'],
            r['operating_activity'],
            r['rev_cagr'],
            r['rev_flag'],
            r['pat_cagr'],
            r['pat_flag'],
            r['eps_cagr'],
            r['eps_flag'],
            r['icr_label'],
            r['high_leverage_flag'],
            None  # composite_quality_score is explicitly deferred to Sprint 3 as documented
        ))
        
        # One row per company-year for capital allocation CSV
        cfo_val = r['operating_activity']
        cfi_val = r['investing_activity']
        cff_val = r['financing_activity']
        
        cfo_sign = "+" if (pd.notna(cfo_val) and cfo_val > 0) else "-"
        cfi_sign = "+" if (pd.notna(cfi_val) and cfi_val > 0) else "-"
        cff_sign = "+" if (pd.notna(cff_val) and cff_val > 0) else "-"
        
        allocation_label = classify_capital_allocation(
            cfo_val, cfi_val, cff_val, pat=r['net_profit'], dividend_payout_pct=r['dividend_payout']
        )
        
        capital_allocation_rows.append({
            "company_id": ticker,
            "year": year,
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": allocation_label
        })
        
    # Write ratios to DB
    cursor.executemany("""
        INSERT INTO financial_ratios (
            company_id, year, net_profit_margin_pct, operating_profit_margin_pct,
            return_on_equity_pct, debt_to_equity, interest_coverage, asset_turnover,
            free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share,
            dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr,
            revenue_cagr_5yr, revenue_cagr_5yr_flag, pat_cagr_5yr, pat_cagr_5yr_flag,
            eps_cagr_5yr, eps_cagr_5yr_flag, icr_label, high_leverage_flag, composite_quality_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, ratio_records)
    conn.commit()
    
    # Verify and print statistics
    cursor.execute("SELECT COUNT(*) FROM financial_ratios;")
    count = cursor.fetchone()[0]
    print(f"Successfully inserted {count} records into 'financial_ratios' table.")
    
    # Save Capital Allocation CSV
    df_alloc = pd.DataFrame(capital_allocation_rows)
    df_alloc.to_csv(CAPITAL_ALLOCATION_CSV, index=False)
    print(f"Successfully exported capital allocation classifications to: {CAPITAL_ALLOCATION_CSV}")
    
    conn.close()

if __name__ == "__main__":
    populate_all_ratios()
