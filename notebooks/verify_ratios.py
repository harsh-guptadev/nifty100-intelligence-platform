import sqlite3
import pandas as pd

def check():
    conn = sqlite3.connect('data/nifty100.db')
    cursor = conn.cursor()
    
    # 3 companies to spot check: ABB, TCS, MARUTI (since HDFCBANK is Financials and has D/E suppressed)
    tickers = ['ABB', 'TCS', 'MARUTI']
    
    print("=== Spot-Checking Ratio Engine Outputs (Latest Year 2024-03) ===")
    
    for ticker in tickers:
        # Get computed values
        cursor.execute("""
            SELECT return_on_equity_pct, revenue_cagr_5yr 
            FROM financial_ratios 
            WHERE company_id=? AND year='2024-03'
        """, (ticker,))
        row = cursor.fetchone()
        if not row:
            print(f"No ratios found for {ticker}")
            continue
        comp_roe, comp_cagr = row
        
        # Manually compute ROE from raw DB tables for 2024-03
        cursor.execute("SELECT net_profit FROM profitandloss WHERE company_id=? AND year='2024-03'", (ticker,))
        net_profit = cursor.fetchone()[0]
        
        cursor.execute("SELECT equity_capital, reserves FROM balancesheet WHERE company_id=? AND year='2024-03'", (ticker,))
        eq, res = cursor.fetchone()
        
        man_roe = (net_profit / (eq + res)) * 100
        
        # Manually compute Revenue CAGR 5Y (2019-03 to 2024-03)
        cursor.execute("SELECT sales FROM profitandloss WHERE company_id=? AND year='2019-03'", (ticker,))
        sales_2019 = cursor.fetchone()[0]
        cursor.execute("SELECT sales FROM profitandloss WHERE company_id=? AND year='2024-03'", (ticker,))
        sales_2024 = cursor.fetchone()[0]
        
        man_cagr = ((sales_2024 / sales_2019) ** (1/5) - 1) * 100
        
        print(f"\nTicker: {ticker}")
        print(f" - ROE: Computed = {comp_roe:.4f}%, Hand-calculated = {man_roe:.4f}% | Diff = {abs(comp_roe - man_roe):.6f}%")
        print(f" - Revenue CAGR 5Y: Computed = {comp_cagr:.4f}%, Hand-calculated = {man_cagr:.4f}% | Diff = {abs(comp_cagr - man_cagr):.6f}%")
        
    conn.close()

if __name__ == "__main__":
    check()
