import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM companies", conn)
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_company(ticker: str):
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM companies WHERE id=?", conn, params=(ticker,))
    finally:
        conn.close()
    if len(df) > 0:
        return df.iloc[0].to_dict()
    return None

@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: str = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        if ticker and year:
            query = "SELECT * FROM financial_ratios WHERE company_id=? AND year=? ORDER BY year"
            params = (ticker, year)
        elif ticker:
            query = "SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year"
            params = (ticker,)
        elif year:
            query = "SELECT * FROM financial_ratios WHERE year=? ORDER BY company_id"
            params = (year,)
        else:
            query = "SELECT * FROM financial_ratios ORDER BY company_id, year"
            params = ()
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM cashflow WHERE company_id=? ORDER BY year", conn, params=(ticker,))
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM sectors", conn)
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name: str = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        if group_name:
            df = pd.read_sql("SELECT * FROM peer_groups WHERE peer_group_name=?", conn, params=(group_name,))
        else:
            df = pd.read_sql("SELECT * FROM peer_groups", conn)
    finally:
        conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker: str = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        if ticker:
            df = pd.read_sql("SELECT * FROM valuation WHERE company_id=?", conn, params=(ticker,))
        else:
            df = pd.read_sql("SELECT * FROM valuation", conn)
    finally:
        conn.close()
    return df
