import streamlit as st
import pandas as pd
import os
from src.dashboard.utils.db import get_companies

st.title("📁 Annual Reports & PDF Tear Sheets Center")

df_comp = get_companies()
if df_comp.empty:
    st.error("No company metadata available.")
    st.stop()

# Company Search Box
company_list = df_comp['id'].tolist()
selected_ticker = st.selectbox("Search Company Ticker for Annual Reports & Tearsheets", options=company_list, index=0)

comp_info = df_comp[df_comp['id'] == selected_ticker].iloc[0]

st.subheader(f"📑 Document Repository: {comp_info['company_name']} (`{selected_ticker}`)")

# Available Annual Report Years & BSE PDF Links
st.markdown("##### 📅 Available Annual Financial Statements (BSE Links)")

years_list = ["FY 2024 (2024-03)", "FY 2023 (2023-03)", "FY 2022 (2022-03)", "FY 2021 (2021-03)", "FY 2020 (2020-03)"]

for yr in years_list:
    col_yr, col_status, col_link = st.columns([2, 2, 3])
    col_yr.write(f"**{yr}**")
    
    # Mock / Simulated BSE link check
    bse_url = f"https://www.bseindia.com/bseplus/AnnualReport/{selected_ticker}_{yr[:7]}.pdf"
    
    # Check if URL is simulated / available
    if "2024" in yr or "2023" in yr or "2022" in yr:
        col_status.success("🟢 Available on BSE")
        col_link.markdown(f"[📄 Download Annual Report PDF]({bse_url})")
    else:
        col_status.error("🔴 Report Unavailable")
        col_link.write("—")

st.markdown("---")

# PDF Tearsheet Download Section
st.markdown("##### 📄 Generated Financial Tear Sheets & Radar Visuals")

tearsheet_path = f"reports/tearsheets/{selected_ticker}_tearsheet.pdf"
radar_path = f"reports/radar_charts/{selected_ticker}_radar.png"

col_radar, col_pdf = st.columns(2)

with col_radar:
    st.write("**8-Axis Radar Chart**")
    if os.path.exists(radar_path):
        st.image(radar_path, caption=f"{selected_ticker} Radar Chart", use_column_width=True)
    else:
        st.info("Radar chart image pending generation.")

with col_pdf:
    st.write("**1-Page PDF Tearsheet Report**")
    if os.path.exists(tearsheet_path):
        with open(tearsheet_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label=f"📥 Download {selected_ticker} PDF Tearsheet",
            data=pdf_bytes,
            file_name=f"{selected_ticker}_tearsheet.pdf",
            mime="application/pdf"
        )
    else:
        st.info("PDF Tearsheet will be available after Sprint 5 report generation.")

st.markdown("---")

# Daily Financial Intelligence PDF Report Section
st.markdown("##### 📰 Executive Daily Financial Intelligence Summary Report")

daily_dir = "reports/daily"
daily_pdfs = [f for f in os.listdir(daily_dir) if f.endswith(".pdf")] if os.path.exists(daily_dir) else []

col_daily_info, col_daily_btn = st.columns([3, 2])

with col_daily_info:
    st.write("**Daily Executive Intelligence Report (PDF)**")
    st.caption("Includes market overview KPIs, top ROE & growth leaders, and sector performance snapshots.")

with col_daily_btn:
    if daily_pdfs:
        latest_daily_file = sorted(daily_pdfs)[-1]
        latest_daily_path = os.path.join(daily_dir, latest_daily_file)
        with open(latest_daily_path, "rb") as f:
            daily_bytes = f.read()
        st.download_button(
            label=f"📥 Download Daily Report ({latest_daily_file})",
            data=daily_bytes,
            file_name=latest_daily_file,
            mime="application/pdf"
        )
    else:
        st.info("Run `python -m src.reports.daily_report` to generate today's report.")

