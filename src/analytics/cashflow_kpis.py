import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def compute_fcf(cfo: float, cfi: float) -> float | None:
    if pd.isna(cfo) or pd.isna(cfi):
        return None
    return float(cfo + cfi)

def compute_cfo_quality_score(cfo_series, pat_series) -> tuple:
    """
    CFO Quality Score = 5-year average of (CFO / PAT).
    High Quality (>1.0), Moderate (0.5-1.0), Accrual Risk (<0.5)
    Returns (None, None) if no valid ratios can be computed.
    """
    valid_ratios = []
    for cfo, pat in zip(cfo_series, pat_series):
        try:
            if pd.notna(cfo) and pd.notna(pat) and float(pat) != 0:
                valid_ratios.append(float(cfo) / float(pat))
        except Exception:
            continue

    if not valid_ratios:
        return None, None

    avg_score = float(np.mean(valid_ratios[-5:]))

    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label

def compute_capex_intensity(cfi: float, sales: float) -> tuple:
    """
    CapEx Intensity = abs(investing_activity) / sales * 100.
    Asset Light (<3%), Moderate (3-8%), Capital Intensive (>8%)
    Returns (None, None) if sales=0 or inputs invalid.
    """
    if pd.isna(cfi) or pd.isna(sales) or sales <= 0:
        return None, None

    intensity = (abs(float(cfi)) / float(sales)) * 100.0

    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return float(intensity), label

def compute_fcf_conversion_rate(fcf: float, op_profit: float) -> float | None:
    if pd.isna(fcf) or pd.isna(op_profit) or op_profit == 0:
        return None
    return float((fcf / op_profit) * 100.0)

def classify_capital_allocation(cfo: float, cfi: float, cff: float, pat: float = None, dividend_payout_pct: float = None) -> str:
    """
    8-pattern capital allocation classifier.
    Returns pattern label string directly.
    Shareholder Returns: (+,-,-) with CFO/PAT > 1 OR dividend_payout_pct >= 30.
    """
    s_cfo = 1 if (pd.notna(cfo) and cfo > 0) else -1
    s_cfi = 1 if (pd.notna(cfi) and cfi > 0) else -1
    s_cff = 1 if (pd.notna(cff) and cff > 0) else -1

    pattern = (s_cfo, s_cfi, s_cff)

    if pattern == (1, -1, -1):
        # Check for Shareholder Returns
        is_shareholder = False
        if pat is not None and pd.notna(pat) and pat != 0 and cfo is not None:
            if float(cfo) / float(pat) > 1.0:
                is_shareholder = True
        if dividend_payout_pct is not None and pd.notna(dividend_payout_pct) and float(dividend_payout_pct) >= 30:
            is_shareholder = True
        return "Shareholder Returns" if is_shareholder else "Reinvestor"
    elif pattern == (1, 1, -1):
        return "Liquidating Assets"
    elif pattern == (-1, 1, 1):
        return "Distress Signal"
    elif pattern == (-1, -1, 1):
        return "Growth Funded by Debt"
    elif pattern == (1, 1, 1):
        return "Cash Accumulator"
    elif pattern == (-1, -1, -1):
        return "Pre-Revenue"
    else:
        return "Mixed"


def _classify_for_output(cfo: float, cfi: float, cff: float) -> tuple:
    """Internal wrapper returning (pattern_str, label) for batch use."""
    label = classify_capital_allocation(cfo, cfi, cff)
    s_cfo = '+' if (pd.notna(cfo) and cfo > 0) else '-'
    s_cfi = '+' if (pd.notna(cfi) and cfi > 0) else '-'
    s_cff = '+' if (pd.notna(cff) and cff > 0) else '-'
    pattern = f"({s_cfo},{s_cfi},{s_cff})"
    return pattern, label

def run_cashflow_intelligence_module():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
        df_cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        df_sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
        df_ratios = pd.read_sql_query("SELECT company_id, year, free_cash_flow_cr, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios", conn)
    finally:
        conn.close()

    records = []
    distress_alerts = []
    pattern_changes = []

    for _, c_row in df_comp.iterrows():
        comp_id = c_row["company_id"]
        
        comp_cf = df_cf[df_cf["company_id"] == comp_id].sort_values("year")
        comp_pl = df_pl[df_pl["company_id"] == comp_id].sort_values("year")
        comp_bs = df_bs[df_bs["company_id"] == comp_id].sort_values("year")
        comp_rat = df_ratios[df_ratios["company_id"] == comp_id].sort_values("year")
        sec_info = df_sectors[df_sectors["company_id"] == comp_id]
        sector = sec_info.iloc[0]["broad_sector"] if not sec_info.empty else "General"

        if comp_cf.empty:
            continue

        lat_cf = comp_cf.iloc[-1]
        lat_pl = comp_pl.iloc[-1] if not comp_pl.empty else {}
        lat_bs = comp_bs.iloc[-1] if not comp_bs.empty else {}
        lat_rat = comp_rat.iloc[-1] if not comp_rat.empty else {}

        # 1. CFO Quality Score
        cfo_score, cfo_label = compute_cfo_quality_score(comp_cf["operating_activity"], comp_pl["net_profit"] if not comp_pl.empty else [])
        cfo_label = cfo_label or "Accrual Risk"

        # 2. CapEx Intensity
        capex_pct, capex_label = compute_capex_intensity(lat_cf.get("investing_activity"), lat_pl.get("sales"))

        # 3. Distress Signal (CFO < 0 AND CFF > 0 in latest year)
        distress_flag = bool(lat_cf.get("operating_activity", 0) < 0 and lat_cf.get("financing_activity", 0) > 0)
        if distress_flag:
            distress_alerts.append({
                "company_id": comp_id,
                "sector": sector,
                "cfo_cr": lat_cf.get("operating_activity"),
                "cff_cr": lat_cf.get("financing_activity"),
                "net_profit": lat_pl.get("net_profit")
            })

        # 4. Deleveraging Flag (CFF < 0 AND borrowings declining YoY)
        prev_bs = comp_bs.iloc[-2] if len(comp_bs) >= 2 else {}
        curr_borr = lat_bs.get("borrowings", 0)
        prev_borr = prev_bs.get("borrowings", 0)
        deleveraging_flag = bool(lat_cf.get("financing_activity", 0) < 0 and pd.notna(curr_borr) and pd.notna(prev_borr) and curr_borr < prev_borr)

        # 5. Capital Allocation Pattern & Changes
        _, cap_label = _classify_for_output(lat_cf.get("operating_activity"), lat_cf.get("investing_activity"), lat_cf.get("financing_activity"))
        
        if len(comp_cf) >= 2:
            prev_cf = comp_cf.iloc[-2]
            _, prev_cap_label = _classify_for_output(prev_cf.get("operating_activity"), prev_cf.get("investing_activity"), prev_cf.get("financing_activity"))
            if prev_cap_label != cap_label:
                pattern_changes.append({
                    "company_id": comp_id,
                    "previous_year": prev_cf.get("year"),
                    "previous_pattern": prev_cap_label,
                    "latest_year": lat_cf.get("year"),
                    "latest_pattern": cap_label
                })

        records.append({
            "company_id": comp_id,
            "sector": sector,
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": capex_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": lat_rat.get("free_cash_flow_cr"),
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": cap_label
        })

    os.makedirs("output", exist_ok=True)

    # 1. output/cashflow_intelligence.xlsx
    df_ci = pd.DataFrame(records)
    df_ci.to_excel("output/cashflow_intelligence.xlsx", index=False)

    # 2. output/distress_alerts.csv
    df_da = pd.DataFrame(distress_alerts)
    df_da.to_csv("output/distress_alerts.csv", index=False)

    # 3. output/pattern_changes.csv
    df_pc = pd.DataFrame(pattern_changes)
    df_pc.to_csv("output/pattern_changes.csv", index=False)

    print(f"Cashflow Intelligence completed for {len(df_ci)} companies.")
    print(f"- Distress Alerts: {len(df_da)}")
    print(f"- Pattern Changes: {len(df_pc)}")
    return df_ci

if __name__ == "__main__":
    run_cashflow_intelligence_module()
