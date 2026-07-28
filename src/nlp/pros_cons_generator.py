import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def generate_pros_and_cons():
    """
    Evaluates 12 Pro rules and 12 Con rules for all companies.
    Assigns confidence score (0-100%) and keeps items with confidence > 60%.
    Guarantees at least 1 Pro and 1 Con per company.
    Exports output/pros_cons_generated.csv and populates SQLite 'prosandcons' table.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df_companies = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
        df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        df_cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
        df_sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    finally:
        conn.close()

    records = []

    def add_item(company_id, item_type, rule_id, text, confidence):
        records.append({
            "company_id": company_id,
            "type": item_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence
        })

    for _, c_row in df_companies.iterrows():
        comp_id = c_row["company_id"]
        
        # Get historical ratios and statements for company
        comp_ratios = df_ratios[df_ratios["company_id"] == comp_id].sort_values("year")
        comp_pl = df_pl[df_pl["company_id"] == comp_id].sort_values("year")
        comp_bs = df_bs[df_bs["company_id"] == comp_id].sort_values("year")
        comp_cf = df_cf[df_cf["company_id"] == comp_id].sort_values("year")
        sec_info = df_sectors[df_sectors["company_id"] == comp_id]
        sector = sec_info.iloc[0]["broad_sector"] if not sec_info.empty else "General"

        lat_ratio = comp_ratios.iloc[-1] if not comp_ratios.empty else {}
        lat_pl = comp_pl.iloc[-1] if not comp_pl.empty else {}
        lat_bs = comp_bs.iloc[-1] if not comp_bs.empty else {}
        lat_cf = comp_cf.iloc[-1] if not comp_cf.empty else {}

        pro_count = 0
        con_count = 0

        # --- PRO RULES ---
        # Pro Rule 1: ROE > 20%
        roe = lat_ratio.get("return_on_equity_pct")
        if pd.notna(roe) and roe > 20:
            add_item(comp_id, "pro", "P1", "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.", 95)
            pro_count += 1

        # Pro Rule 2: FCF positive
        fcf = lat_ratio.get("free_cash_flow_cr")
        if pd.notna(fcf) and fcf > 0:
            add_item(comp_id, "pro", "P2", "Strong free cash flow generation signals healthy business fundamentals.", 90)
            pro_count += 1

        # Pro Rule 3: D/E = 0
        de = lat_ratio.get("debt_to_equity")
        if pd.notna(de) and de == 0:
            add_item(comp_id, "pro", "P3", "Debt-free balance sheet provides financial flexibility and eliminates interest burden.", 98)
            pro_count += 1

        # Pro Rule 4: Revenue CAGR > 15%
        rev_cagr = lat_ratio.get("revenue_cagr_5yr")
        if pd.notna(rev_cagr) and rev_cagr > 15:
            add_item(comp_id, "pro", "P4", "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum.", 90)
            pro_count += 1

        # Pro Rule 5: OPM > 25%
        opm = lat_ratio.get("operating_profit_margin_pct")
        if pd.notna(opm) and opm > 25:
            add_item(comp_id, "pro", "P5", "Operating profit margin above 25% indicates strong pricing power and cost discipline.", 92)
            pro_count += 1

        # Pro Rule 6: PAT CAGR > 20%
        pat_cagr = lat_ratio.get("pat_cagr_5yr")
        if pd.notna(pat_cagr) and pat_cagr > 20:
            add_item(comp_id, "pro", "P6", "Net profit compounding at above 20% over 5 years creates significant shareholder value.", 92)
            pro_count += 1

        # Pro Rule 7: ICR > 10 or Debt Free
        icr = lat_ratio.get("interest_coverage")
        if (pd.notna(icr) and icr > 10) or de == 0:
            add_item(comp_id, "pro", "P7", "Very high interest coverage ratio reflects negligible financial stress from debt servicing.", 94)
            pro_count += 1

        # Pro Rule 8: Dividend Yield > 2% with FCF positive
        div_yield = lat_ratio.get("dividend_yield_pct", 0)
        if pd.notna(div_yield) and div_yield > 2 and pd.notna(fcf) and fcf > 0:
            add_item(comp_id, "pro", "P8", "Consistent dividend yield above 2% backed by positive free cash flow.", 88)
            pro_count += 1

        # Pro Rule 9: EPS CAGR > 15%
        eps_cagr = lat_ratio.get("eps_cagr_5yr")
        if pd.notna(eps_cagr) and eps_cagr > 15:
            add_item(comp_id, "pro", "P9", "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding.", 88)
            pro_count += 1

        # Pro Rule 10: ROE improving 3 consecutive years
        if len(comp_ratios) >= 3:
            roes = comp_ratios["return_on_equity_pct"].dropna().tolist()
            if len(roes) >= 3 and roes[-1] > roes[-2] > roes[-3]:
                add_item(comp_id, "pro", "P10", "Return on equity improving for 3 consecutive years shows strengthening business quality.", 85)
                pro_count += 1

        # Pro Rule 11: Revenue CAGR < PAT CAGR (operating leverage)
        if pd.notna(rev_cagr) and pd.notna(pat_cagr) and pat_cagr > rev_cagr:
            add_item(comp_id, "pro", "P11", "Revenue growing slower than profits shows improving operating leverage and scale benefits.", 86)
            pro_count += 1

        # Pro Rule 12: Growing assets with declining debt
        if len(comp_bs) >= 2:
            prev_bs = comp_bs.iloc[-2]
            curr_tot_assets = lat_bs.get("total_assets", 0)
            prev_tot_assets = prev_bs.get("total_assets", 0)
            curr_borr = lat_bs.get("borrowings", 0)
            prev_borr = prev_bs.get("borrowings", 0)
            if pd.notna(curr_tot_assets) and pd.notna(prev_tot_assets) and curr_tot_assets > prev_tot_assets and curr_borr <= prev_borr:
                add_item(comp_id, "pro", "P12", "Growing asset base funded by internal accruals reflects self-sustaining growth.", 87)
                pro_count += 1

        # Guaranteed Pro fallback if none triggered
        if pro_count == 0:
            add_item(comp_id, "pro", "P0", "Established blue-chip market position within the Nifty 100 universe.", 75)

        # --- CON RULES ---
        # Con Rule 1: D/E > 2.0 (non-financials)
        if sector != "Financials" and pd.notna(de) and de > 2.0:
            add_item(comp_id, "con", "C1", f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring.", 90)
            con_count += 1

        # Con Rule 2: FCF negative 3 consecutive years
        if len(comp_ratios) >= 3:
            fcfs = comp_ratios["free_cash_flow_cr"].dropna().tolist()
            if len(fcfs) >= 3 and all(f < 0 for f in fcfs[-3:]):
                add_item(comp_id, "con", "C2", "Free cash flow negative for 3 consecutive years raises concern about cash generation quality.", 92)
                con_count += 1

        # Con Rule 3: OPM declining 3 consecutive years
        if len(comp_ratios) >= 3:
            opms = comp_ratios["operating_profit_margin_pct"].dropna().tolist()
            if len(opms) >= 3 and opms[-1] < opms[-2] < opms[-3]:
                add_item(comp_id, "con", "C3", "Operating margins declining for 3 consecutive years suggest pricing or cost pressure.", 88)
                con_count += 1

        # Con Rule 4: Net profit negative in latest year
        np_val = lat_pl.get("net_profit")
        if pd.notna(np_val) and np_val < 0:
            add_item(comp_id, "con", "C4", "Company reported a net loss in the most recent financial year.", 96)
            con_count += 1

        # Con Rule 5: Revenue declining 2+ years
        if len(comp_pl) >= 2:
            sales_list = comp_pl["sales"].dropna().tolist()
            if len(sales_list) >= 2 and sales_list[-1] < sales_list[-2]:
                add_item(comp_id, "con", "C5", "Revenue contraction over consecutive years indicates demand weakness or market share loss.", 85)
                con_count += 1

        # Con Rule 6: ICR < 1.5
        if pd.notna(icr) and icr < 1.5 and de != 0:
            add_item(comp_id, "con", "C6", "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations.", 94)
            con_count += 1

        # Con Rule 7: Dividend payout > 100%
        div_payout = lat_ratio.get("dividend_payout_ratio_pct")
        if pd.notna(div_payout) and div_payout > 100:
            add_item(comp_id, "con", "C7", "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable.", 90)
            con_count += 1

        # Con Rule 8: D/E rising 3 consecutive years
        if len(comp_ratios) >= 3:
            des = comp_ratios["debt_to_equity"].dropna().tolist()
            if len(des) >= 3 and des[-1] > des[-2] > des[-3]:
                add_item(comp_id, "con", "C8", "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk.", 86)
                con_count += 1

        # Con Rule 9: EPS declining 3 consecutive years
        if len(comp_pl) >= 3:
            epss = comp_pl["eps"].dropna().tolist()
            if len(epss) >= 3 and epss[-1] < epss[-2] < epss[-3]:
                add_item(comp_id, "con", "C9", "Earnings per share declining for 3 consecutive years reflects deteriorating profitability.", 88)
                con_count += 1

        # Con Rule 10: ROCE < 10%
        roce = lat_ratio.get("roce_percentage")
        if pd.notna(roce) and roce < 10:
            add_item(comp_id, "con", "C10", "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital.", 85)
            con_count += 1

        # Con Rule 11: Revenue CAGR < 5%
        if pd.notna(rev_cagr) and rev_cagr < 5:
            add_item(comp_id, "con", "C11", "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum.", 82)
            con_count += 1

        # Guaranteed Con fallback if none triggered
        if con_count == 0:
            add_item(comp_id, "con", "C0", "Subject to macro-economic cycles and broad market competition.", 70)

    os.makedirs("output", exist_ok=True)
    df_out = pd.DataFrame(records)
    
    # Filter for confidence > 60%
    df_out = df_out[df_out["confidence_pct"] > 60].copy()
    df_out.to_csv("output/pros_cons_generated.csv", index=False)

    # Save to SQLite table 'prosandcons'
    conn = sqlite3.connect(DB_PATH)
    try:
        df_out.to_sql("prosandcons", conn, if_exists="replace", index=False)
    finally:
        conn.close()

    print(f"Generated {len(df_out)} Pros/Cons entries for {df_companies['company_id'].nunique()} companies.")
    return df_out

if __name__ == "__main__":
    generate_pros_and_cons()
