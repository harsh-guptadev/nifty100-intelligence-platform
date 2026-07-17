-- Nifty 100 Financial Intelligence Platform SQLite Schema
-- Created: July 2026

PRAGMA foreign_keys = ON;

-- 1. companies (Master Company Reference)
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY, -- NSE ticker
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. profitandloss (Annual Profit & Loss Statements)
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL, -- standardised to YYYY-MM
    sales REAL NOT NULL,
    expenses REAL NOT NULL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 3. balancesheet (Annual Balance Sheet)
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL, -- standardised to YYYY-MM
    equity_capital REAL NOT NULL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL NOT NULL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL NOT NULL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 4. cashflow (Annual Cash Flow Statements)
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL, -- standardised to YYYY-MM
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 5. analysis (Pre-Computed Growth Metrics - Partial Coverage)
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id)
);

-- 6. documents (Annual Report Repository)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    Year INTEGER NOT NULL,
    Annual_Report TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, Year)
);

-- 7. prosandcons (Qualitative Investment Insights - Partial Coverage)
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 8. sectors (Company Sector Mapping)
CREATE TABLE IF NOT EXISTS sectors (
    company_id TEXT PRIMARY KEY,
    broad_sector TEXT NOT NULL,
    sub_sector TEXT NOT NULL,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 9. stock_prices (Monthly OHLCV Price History - Simulated)
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL, -- YYYY-MM-DD
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, date)
);

-- 10. market_cap (Annual Valuation Multiples - Simulated)
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 11. financial_ratios (Computed KPI table - populated in Sprint 2)
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL, -- YYYY-MM
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    revenue_cagr_5yr REAL,
    pat_cagr_5yr REAL,
    eps_cagr_5yr REAL,
    composite_quality_score REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 12. peer_groups (Peer Comparison Groups - populated in Sprint 3)
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER NOT NULL DEFAULT 0, -- 0=False, 1=True
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(peer_group_name, company_id)
);
