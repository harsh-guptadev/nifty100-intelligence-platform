import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from src.screener.engine import get_screener_data, apply_filters, compute_sector_relative_scores

router = APIRouter(prefix="/screener", tags=["Screener"])
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

_CACHED_SCREENER_DF = None

def _get_cached_latest_screener_df():
    global _CACHED_SCREENER_DF
    if _CACHED_SCREENER_DF is None:
        df = get_screener_data()
        df = compute_sector_relative_scores(df)
        df_valid = df[df['return_on_equity_pct'].notna()]
        if not df_valid.empty:
            latest_indices = df_valid.groupby("company_id")["year"].idxmax()
            missing_cos = set(df['company_id']) - set(df_valid['company_id'])
            if missing_cos:
                df_missing = df[df['company_id'].isin(missing_cos)]
                missing_indices = df_missing.groupby("company_id")["year"].idxmax()
                all_indices = pd.concat([latest_indices, missing_indices])
            else:
                all_indices = latest_indices
            _CACHED_SCREENER_DF = df.loc[all_indices].copy()
        else:
            _CACHED_SCREENER_DF = df[df.groupby("company_id")["year"].transform("max") == df["year"]].copy()
    return _CACHED_SCREENER_DF.copy()

@router.get("")
def run_screener(
    min_roe: Optional[float] = Query(None),
    max_de: Optional[float] = Query(None),
    min_fcf: Optional[float] = Query(None),
    sector: Optional[str] = Query(None),
    min_rev_cagr_5yr: Optional[float] = Query(None),
    min_pat_cagr_5yr: Optional[float] = Query(None),
    max_pe: Optional[float] = Query(None)
):
    if max_pe is not None and max_pe <= 0:
        raise HTTPException(status_code=400, detail="max_pe must be positive")
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative")

    criteria = {}
    if min_roe is not None:
        criteria["return_on_equity_pct_min"] = min_roe
    if max_de is not None:
        criteria["debt_to_equity_max"] = max_de
    if min_fcf is not None:
        criteria["free_cash_flow_cr_min"] = min_fcf
    if sector is not None:
        criteria["broad_sector"] = sector
    if min_rev_cagr_5yr is not None:
        criteria["revenue_cagr_5yr_min"] = min_rev_cagr_5yr
    if min_pat_cagr_5yr is not None:
        criteria["pat_cagr_5yr_min"] = min_pat_cagr_5yr
    if max_pe is not None:
        criteria["pe_ratio_max"] = max_pe

    try:
        df_latest = _get_cached_latest_screener_df()
        results = apply_filters(df_latest, criteria)
        results = results.sort_values(by="composite_quality_score", ascending=False)

        # Drop non-serializable dict column if present
        if "_filter_matches" in results.columns:
            results = results.drop(columns=["_filter_matches"])

        # Convert NaNs & Infs to None cleanly for JSON output
        results_obj = results.astype(object)
        results_obj = results_obj.where(pd.notnull(results_obj), None)
        records = results_obj.to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                    r[k] = None

        return records
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
