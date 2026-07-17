import pandas as pd
import numpy as np

def compute_cagr(start_value: float, end_value: float, n: int) -> tuple[float | None, str | None]:
    """
    Computes Compound Annual Growth Rate (CAGR) over n years.
    Formula: ((end_value / start_value) ** (1 / n) - 1) * 100
    
    Returns (cagr_value, flag) according to the 6 CAGR sign edge cases:
    1. Positive & Positive -> Returns (cagr, None)
    2. Positive & Negative -> Returns (None, 'DECLINE_TO_LOSS')
    3. Negative & Positive -> Returns (None, 'TURNAROUND')
    4. Negative & Negative -> Returns (None, 'BOTH_NEGATIVE')
    5. Zero Base -> Returns (None, 'ZERO_BASE')
    6. Insufficient History -> Returns (None, 'INSUFFICIENT')
    """
    if n <= 0:
        return None, "INSUFFICIENT"
        
    if pd.isna(start_value) or pd.isna(end_value):
        return None, "INSUFFICIENT"
        
    if start_value == 0:
        return None, "ZERO_BASE"
        
    if start_value > 0 and end_value > 0:
        try:
            cagr = ((end_value / start_value) ** (1.0 / n) - 1.0) * 100.0
            return float(cagr), None
        except Exception:
            return None, "ERROR"
    elif start_value > 0 and end_value <= 0:
        return None, "DECLINE_TO_LOSS"
    elif start_value < 0 and end_value >= 0:
        return None, "TURNAROUND"
    else: # start_value < 0 and end_value < 0
        return None, "BOTH_NEGATIVE"
