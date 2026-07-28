import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_company, get_ratios, get_pl, get_bs, get_cf, get_sectors

st.title("🏢 Company Profile & Financial Deep-Dive")

df_companies = get_companies()
if df_companies.empty:
    st.error("No company data available.")
    st.stop()

# Company Search Box & Selectbox Autocomplete
company_list = df_companies['id'].tolist()
company_name_map = dict(zip(df_companies['id'], df_companies['company_name']))
options = [f"{ticker} - {company_name_map.get(ticker, '')}" for ticker in company_list]

selected_option = st.selectbox("Search Company Ticker or Name", options=options, index=0)
selected_ticker = selected_option.split(" - ")[0]

company_data = get_company(selected_ticker)

if not company_data:
    st.warning("Ticker not found - please try another")
    st.stop()

# Fetch metadata & financial statements
df_sec = get_sectors()
sec_info = df_sec[df_sec['company_id'] == selected_ticker]
sector_name = sec_info.iloc[0]['broad_sector'] if not sec_info.empty else "N/A"
sub_sector_name = sec_info.iloc[0]['sub_sector'] if not sec_info.empty else "N/A"

df_rat = get_ratios(selected_ticker)
df_pl_data = get_pl(selected_ticker)

# Company Card Header
st.subheader(f"{company_data.get('company_name')} ({selected_ticker})")
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.write(f"**Broad Sector:** {sector_name}")
col_info2.write(f"**Sub-Sector:** {sub_sector_name}")
col_info3.write(f"**NSE Ticker:** `{selected_ticker}`")

# 6 Key Metric Tiles (Latest Year)
if not df_rat.empty:
    latest = df_rat.iloc[-1]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("ROE", f"{latest.get('return_on_equity_pct', 0):.1f}%" if pd.notna(latest.get('return_on_equity_pct')) else "N/A")
    col2.metric("ROCE", f"{latest.get('roce_percentage', 0):.1f}%" if pd.notna(latest.get('roce_percentage')) else "N/A")
    col3.metric("NPM", f"{latest.get('net_profit_margin_pct', 0):.1f}%" if pd.notna(latest.get('net_profit_margin_pct')) else "N/A")
    col4.metric("D/E", f"{latest.get('debt_to_equity', 0):.2f}" if pd.notna(latest.get('debt_to_equity')) else "N/A")
    col5.metric("5Yr Rev CAGR", f"{latest.get('revenue_cagr_5yr', 0):.1f}%" if pd.notna(latest.get('revenue_cagr_5yr')) else "N/A")
    col6.metric("FCF (Cr)", f"₹{latest.get('free_cash_flow_cr', 0):.1f}" if pd.notna(latest.get('free_cash_flow_cr')) else "N/A")

st.markdown("---")

# Charts: 10-Year Revenue & PAT + ROE/ROCE Dual Axis
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 10-Year Revenue & Net Profit (₹ Crore)")
    if not df_pl_data.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df_pl_data['year'], y=df_pl_data['sales'], name='Revenue', marker_color='#1f77b4'))
        fig_bar.add_trace(go.Bar(x=df_pl_data['year'], y=df_pl_data['net_profit'], name='Net Profit', marker_color='#2ca02c'))
        fig_bar.update_layout(barmode='group', margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("P&L data unavailable for charts.")

with col_chart2:
    st.subheader("🔄 ROE & ROCE Trends (%)")
    if not df_rat.empty:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_rat['year'], y=df_rat['return_on_equity_pct'], mode='lines+markers', name='ROE (%)', line=dict(color='#ff7f0e', width=3)))
        if 'roce_percentage' in df_rat.columns:
            fig_line.add_trace(go.Scatter(x=df_rat['year'], y=df_rat['roce_percentage'], mode='lines+markers', name='ROCE (%)', line=dict(color='#9467bd', width=3)))
        fig_line.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Ratio trends unavailable for charts.")

st.markdown("---")

# Pros and Cons Badges
st.subheader("💡 Key Highlights & Risk Profile (Pros & Cons)")
pro_col, con_col = st.columns(2)

with pro_col:
    st.markdown("##### ✅ Pros & Strengths")
    pros = []
    if not df_rat.empty:
        lat = df_rat.iloc[-1]
        if lat.get('return_on_equity_pct', 0) and lat.get('return_on_equity_pct', 0) > 15:
            pros.append("High Return on Equity (>15%)")
        if lat.get('debt_to_equity', 1) == 0:
            pros.append("Company is Virtually Debt-Free")
        if lat.get('free_cash_flow_cr', 0) and lat.get('free_cash_flow_cr', 0) > 0:
            pros.append("Consistently Generates Positive Free Cash Flow")
        if lat.get('revenue_cagr_5yr', 0) and lat.get('revenue_cagr_5yr', 0) > 10:
            pros.append("Strong 5-Year Revenue Growth (>10% CAGR)")
    if not pros:
        pros.append("Stable operating historical record")
    for item in pros:
        st.success(f"✔️ {item}")

with con_col:
    st.markdown("##### ❌ Cons & Risks")
    cons = []
    if not df_rat.empty:
        lat = df_rat.iloc[-1]
        if lat.get('debt_to_equity', 0) and lat.get('debt_to_equity', 0) > 2:
            cons.append("High Financial Leverage (D/E > 2.0)")
        if lat.get('interest_coverage', 2) and lat.get('interest_coverage', 2) < 1.5:
            cons.append("Weak Interest Coverage Ratio (<1.5x)")
        if lat.get('net_profit_margin_pct', 10) and lat.get('net_profit_margin_pct', 10) < 5:
            cons.append("Low Profit Margins (<5% Net Margin)")
    if not cons:
        cons.append("No critical balance sheet flags detected")
    for item in cons:
        st.error(f"⚠️ {item}")
