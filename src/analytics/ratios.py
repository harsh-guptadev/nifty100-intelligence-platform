import pandas as pd
import numpy as np

def compute_npm(net_profit: float, sales: float) -> float | None:
    """
    Net Profit Margin (NPM) = net_profit / sales * 100.
    Returns None if sales is 0 or NaN.
    """
    if pd.isna(sales) or sales == 0 or pd.isna(net_profit):
        return None
    return float((net_profit / sales) * 100)

def compute_opm(operating_profit: float, sales: float) -> float | None:
    """
    Operating Profit Margin (OPM) = operating_profit / sales * 100.
    Returns None if sales is 0 or NaN.
    """
    if pd.isna(sales) or sales == 0 or pd.isna(operating_profit):
        return None
    return float((operating_profit / sales) * 100)

def compute_roe(net_profit: float, equity_capital: float, reserves: float) -> float | None:
    """
    Return on Equity (ROE) = net_profit / (equity_capital + reserves) * 100.
    Returns None if denominator is <= 0 or NaN.
    """
    if pd.isna(net_profit) or pd.isna(equity_capital) or pd.isna(reserves):
        return None
    denominator = equity_capital + reserves
    if denominator <= 0:
        return None
    return float((net_profit / denominator) * 100)

def compute_roce(ebit: float, equity_capital: float, reserves: float, borrowings: float) -> float | None:
    """
    Return on Capital Employed (ROCE) = EBIT / (equity_capital + reserves + borrowings) * 100.
    Returns None if denominator is <= 0 or NaN.
    """
    if pd.isna(ebit) or pd.isna(equity_capital) or pd.isna(reserves) or pd.isna(borrowings):
        return None
    denominator = equity_capital + reserves + borrowings
    if denominator <= 0:
        return None
    return float((ebit / denominator) * 100)

def compute_roa(net_profit: float, total_assets: float) -> float | None:
    """
    Return on Assets (ROA) = net_profit / total_assets * 100.
    Returns None if total_assets is 0 or NaN.
    """
    if pd.isna(total_assets) or total_assets == 0 or pd.isna(net_profit):
        return None
    return float((net_profit / total_assets) * 100)

def compute_de(borrowings: float, equity_capital: float, reserves: float) -> float | None:
    """
    Debt-to-Equity (D/E) = borrowings / (equity_capital + reserves).
    Returns 0.0 if borrowings is 0 or NaN (representing debt-free status).
    Returns None if denominator is <= 0 or NaN.
    """
    if pd.isna(borrowings) or borrowings == 0:
        return 0.0
    if pd.isna(equity_capital) or pd.isna(reserves):
        return None
    denominator = equity_capital + reserves
    if denominator <= 0:
        return None
    return float(borrowings / denominator)

def compute_icr(operating_profit: float, other_income: float, interest: float) -> float | None:
    """
    Interest Coverage Ratio (ICR) = (operating_profit + other_income) / interest.
    Returns None if interest is 0 or NaN (meaning "Debt Free").
    """
    if pd.isna(interest) or interest == 0:
        return None
    op_profit_val = operating_profit if pd.notna(operating_profit) else 0.0
    other_inc_val = other_income if pd.notna(other_income) else 0.0
    if pd.isna(operating_profit) and pd.isna(other_income):
        return None
    return float((op_profit_val + other_inc_val) / interest)

def compute_net_debt(borrowings: float, investments: float) -> float:
    """
    Net Debt = borrowings - investments.
    Defaults missing components to 0.0.
    """
    b = borrowings if pd.notna(borrowings) else 0.0
    i = investments if pd.notna(investments) else 0.0
    return float(b - i)

def compute_asset_turnover(sales: float, total_assets: float) -> float | None:
    """
    Asset Turnover = sales / total_assets.
    Returns None if total_assets is 0 or NaN.
    """
    if pd.isna(total_assets) or total_assets == 0 or pd.isna(sales):
        return None
    return float(sales / total_assets)
