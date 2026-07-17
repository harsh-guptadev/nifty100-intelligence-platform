import sqlite3

def verify():
    conn = sqlite3.connect('data/nifty100.db')
    cursor = conn.cursor()
    
    companies = ['ABB', 'ADANIENSOL', 'TCS', 'HDFCBANK', 'MARUTI']
    print("=== Manual Ingestion Verification (5 Random Companies) ===")
    
    for ticker in companies:
        cursor.execute("SELECT company_name FROM companies WHERE id=?", (ticker,))
        name_row = cursor.fetchone()
        name = name_row[0] if name_row else "NOT FOUND"
        
        cursor.execute("SELECT broad_sector, sub_sector FROM sectors WHERE company_id=?", (ticker,))
        sector_row = cursor.fetchone()
        sector = f"{sector_row[0]} ({sector_row[1]})" if sector_row else "NOT FOUND"
        
        cursor.execute("SELECT COUNT(*) FROM profitandloss WHERE company_id=?", (ticker,))
        pl_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM balancesheet WHERE company_id=?", (ticker,))
        bs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cashflow WHERE company_id=?", (ticker,))
        cf_count = cursor.fetchone()[0]
        
        print(f"\nTicker: {ticker}")
        print(f" - Legal Name: {name}")
        print(f" - GICS Sector: {sector}")
        print(f" - Statements Loaded: P&L: {pl_count} years, Balancesheet: {bs_count} years, Cashflow: {cf_count} years")
        
    conn.close()

if __name__ == "__main__":
    verify()
