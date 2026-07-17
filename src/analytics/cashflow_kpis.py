import pandas as pd
import numpy as np

def compute_fcf(operating_activity: float, investing_activity: float) -> float | None:
    """
    Free Cash Flow (FCF) = CFO + CFI.
    (Note: CFI is typically negative representing cash outflow, so adding them computes CFO - CapEx).
    """
    if pd.isna(operating_activity) or pd.isna(investing_activity):
        return None
    return float(operating_activity + investing_activity)

def compute_cfo_quality_score(cfo_values: list[float], pat_values: list[float]) -> tuple[float | None, str | None]:
    """
    CFO Quality Score = sum(CFO) / sum(PAT) over available years (up to 5 years).
    Returns (score, label) where:
     - >1.0 = 'High Quality' (or 'High Quality Earnings')
     - 0.5 to 1.0 = 'Moderate'
     - <0.5 = 'Accrual Risk'
    """
    valid_pairs = [(c, p) for c, p in zip(cfo_values, pat_values) if pd.notna(c) and pd.notna(p)]
    if not valid_pairs:
        return None, None
    sum_cfo = sum(c for c, p in valid_pairs)
    sum_pat = sum(p for c, p in valid_pairs)
    if sum_pat == 0 or pd.isna(sum_pat):
        return None, None
    
    score = sum_cfo / sum_pat
    if score > 1.0:
        label = "High Quality"
    elif score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return float(score), label

def compute_capex_intensity(investing_activity: float, sales: float) -> tuple[float | None, str | None]:
    """
    CapEx Intensity = abs(CFI) / sales * 100.
    Returns (intensity, label) where:
     - <3% = 'Asset Light'
     - 3-8% = 'Moderate'
     - >8% = 'Capital Intensive'
    """
    if pd.isna(investing_activity) or pd.isna(sales) or sales == 0:
        return None, None
    intensity = (abs(investing_activity) / sales) * 100
    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return float(intensity), label

def compute_fcf_conversion_rate(fcf: float, operating_profit: float) -> float | None:
    """
    FCF Conversion Rate = FCF / operating_profit * 100.
    """
    if pd.isna(fcf) or pd.isna(operating_profit) or operating_profit == 0:
        return None
    return float((fcf / operating_profit) * 100)

def classify_capital_allocation(cfo: float, cfi: float, cff: float, pat: float = 0.0, dividend_payout_pct: float = 0.0) -> str:
    """
    Classifies capital allocation pattern based on CFO, CFI, and CFF signs:
    - (+, -, -) -> 'Shareholder Returns' if CFO/PAT > 1.0 or dividend payout is high, else 'Reinvestor'
    - (+, +, -) -> 'Liquidating Assets'
    - (-, ?, +) -> 'Distress Signal' (when CFO < 0 and CFF > 0)
    - (-, -, +) -> 'Growth Funded by Debt' (when CFO < 0, CFI < 0, CFF > 0)
    - (+, +, +) -> 'Cash Accumulator'
    - (-, -, -) -> 'Pre-Revenue'
    - Any other -> 'Mixed'
    """
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Mixed"
        
    cfo_sign = "+" if cfo > 0 else "-"
    cfi_sign = "+" if cfi > 0 else "-"
    cff_sign = "+" if cff > 0 else "-"
    
    pattern = (cfo_sign, cfi_sign, cff_sign)
    
    if cfo_sign == "-" and cff_sign == "+":
        # Check if CFI is also negative (Growth Funded by Debt)
        if cfi_sign == "-":
            return "Growth Funded by Debt"
        else:
            return "Distress Signal"
            
    if pattern == ("+", "-", "-"):
        # Sub-classify between Shareholder Returns and Reinvestor
        # If CFO / PAT > 1.0 (with positive PAT) or dividend_payout_pct >= 30%
        if (pat > 0 and (cfo / pat) > 1.0) or dividend_payout_pct >= 30.0:
            return "Shareholder Returns"
        return "Reinvestor"
        
    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"
    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"
    else:
        return "Mixed"
