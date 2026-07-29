import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.title("📈 Multi-Metric Trend Analysis & Historical Overlay")
st.caption(
    "⚠️ **Simulated Data Notice:** Stock price history and any price-derived metrics "
    "are sourced from **SIMULATED** data for this project — not real market data."
)


df_comp = get_companies()
if df_comp.empty:
    st.error("No company data available.")
    st.stop()

# Company Search Box
company_list = df_comp['id'].tolist()
selected_ticker = st.selectbox("Select Company for Trend Analysis", options=company_list, index=0)

df_rat = get_ratios(selected_ticker)
df_pl_data = get_pl(selected_ticker)

if df_rat.empty:
    st.warning("No ratio trend data available for this company.")
    st.stop()

# Multi-Metric Selector (Up to 3 Metrics)
available_metrics = {
    'ROE (%)': 'return_on_equity_pct',
    'Net Profit Margin (%)': 'net_profit_margin_pct',
    'Debt to Equity': 'debt_to_equity',
    'Revenue (₹ Cr)': 'sales',
    'Net Profit (₹ Cr)': 'net_profit',
    'Free Cash Flow (₹ Cr)': 'free_cash_flow_cr'
}

selected_metric_names = st.multiselect(
    "Select Up to 3 Metrics to Overlay",
    options=list(available_metrics.keys()),
    default=['ROE (%)', 'Net Profit Margin (%)']
)

if not selected_metric_names:
    st.info("Please select at least one metric to display trends.")
    st.stop()

# Merge P&L sales/profit with ratios if needed
df_merged = df_rat.copy()
if not df_pl_data.empty:
    df_merged = df_merged.merge(df_pl_data[['year', 'sales', 'net_profit']], on='year', how='left')

# 10-Year Line Chart with YoY % change annotations
fig_trend = go.Figure()

for m_name in selected_metric_names[:3]:
    col = available_metrics[m_name]
    if col in df_merged.columns:
        series = df_merged[col]
        years = df_merged['year']
        
        # Calculate YoY % change
        pct_change = series.pct_change() * 100
        
        text_labels = [
            f"{val:.1f}<br>({chg:+.1f}%)" if pd.notna(val) and pd.notna(chg) else f"{val:.1f}" if pd.notna(val) else ""
            for val, chg in zip(series, pct_change)
        ]
        
        fig_trend.add_trace(go.Scatter(
            x=years,
            y=series,
            mode='lines+markers+text',
            name=m_name,
            text=text_labels,
            textposition="top center"
        ))

fig_trend.update_layout(
    title=f"10-Year Historical Trends with YoY % Change ({selected_ticker})",
    xaxis_title="Financial Year",
    yaxis_title="Metric Value",
    margin=dict(t=50, b=30, l=30, r=30),
    legend=dict(orientation="h", y=1.1)
)

st.plotly_chart(fig_trend, use_container_width=True)
