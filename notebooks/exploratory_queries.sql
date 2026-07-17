-- Nifty 100 Financial Intelligence Platform - Exploratory SQL Queries
-- Designed for Sprint 1 Verification and Data Quality Audit

-- 1. Total row count for all 10 populated tables (Verification of Loading)
SELECT 'companies' AS table_name, COUNT(*) AS count FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap;

-- 2. Foreign Key validation (Checks for orphaned keys across all tables)
PRAGMA foreign_key_check;

-- 3. Year coverage details per company (Min, Max, and Count of statements)
SELECT company_id, MIN(year) AS start_year, MAX(year) AS end_year, COUNT(*) AS statement_count
FROM profitandloss
GROUP BY company_id
ORDER BY statement_count ASC;

-- 4. Check for companies with less than 5 years of history (potential DQ-16 warning cases)
SELECT company_id, COUNT(*) AS statement_count
FROM profitandloss
GROUP BY company_id
HAVING statement_count < 5;

-- 5. Null count check in profit and loss (verify optional vs required fields)
SELECT 
    COUNT(*) - COUNT(sales) AS null_sales,
    COUNT(*) - COUNT(operating_profit) AS null_op,
    COUNT(*) - COUNT(net_profit) AS null_pat,
    COUNT(*) - COUNT(eps) AS null_eps
FROM profitandloss;

-- 6. Sector representation and weight checks (Sanity check for sectors mapping)
SELECT broad_sector, COUNT(*) AS company_count, ROUND(SUM(index_weight_pct), 2) AS total_sector_weight
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- 7. Document repository analysis: Annual Report link status per company
SELECT company_id, COUNT(Annual_Report) AS report_count, MIN(Year) AS earliest_report, MAX(Year) AS latest_report
FROM documents
GROUP BY company_id
ORDER BY report_count DESC;

-- 8. Verify Balance Sheet Equality (identifies rows flagged by DQ-04 / DQ-15)
SELECT company_id, year, total_assets, 
       (equity_capital + reserves + borrowings + other_liabilities) AS total_liabilities_eq,
       ABS(total_assets - (equity_capital + reserves + borrowings + other_liabilities)) AS asset_liab_diff
FROM balancesheet
WHERE asset_liab_diff > 0.0
ORDER BY asset_liab_diff DESC;

-- 9. Check Cash Flow statement components sum vs net cash flow (identifies rows flagged by DQ-09)
SELECT company_id, year, net_cash_flow, 
       (operating_activity + investing_activity + financing_activity) AS computed_cash_flow,
       ABS(net_cash_flow - (operating_activity + investing_activity + financing_activity)) AS cash_flow_diff
FROM cashflow
WHERE cash_flow_diff > 1.0
ORDER BY cash_flow_diff DESC;

-- 10. List top 5 companies with highest pre-computed ROCE from master company reference
SELECT id, company_name, roce_percentage, roe_percentage
FROM companies
WHERE roce_percentage IS NOT NULL
ORDER BY roce_percentage DESC
LIMIT 5;
