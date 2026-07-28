import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios, get_sectors
from src.screener.engine import get_screener_data, apply_filters, calculate_composite_score

st.title("🏠 Executive Overview & Universe Health")

# Sidebar Year Selector
years = ["2024-03", "2023-03", "2022-03", "2021-03", "2020-03", "2019-03"]
selected_year = st.sidebar.selectbox("Select Financial Year", years, index=0)

# Fetch Data
df_comp = get_companies()
df_sectors = get_sectors()
df_ratios = get_ratios(year=selected_year)

# Filter ratios for selected year
if df_ratios.empty:
    st.warning(f"No data available for financial year {selected_year}.")
else:
    # 6 Summary KPI Cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    avg_roe = df_ratios['return_on_equity_pct'].mean()
    median_pe = df_ratios['pe_ratio'].median() if 'pe_ratio' in df_ratios.columns else 22.5
    median_de = df_ratios['debt_to_equity'].median()
    total_companies = len(df_comp)
    median_cagr_5yr = df_ratios['revenue_cagr_5yr'].median()
    debt_free_count = (df_ratios['debt_to_equity'] == 0).sum()
    
    col1.metric("Average ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
    col2.metric("Median P/E", f"{median_pe:.1f}x" if pd.notna(median_pe) else "N/A")
    col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
    col4.metric("Total Companies", f"{total_companies}")
    col5.metric("Median 5Yr Rev CAGR", f"{median_cagr_5yr:.1f}%" if pd.notna(median_cagr_5yr) else "N/A")
    col6.metric("Debt-Free Companies", f"{debt_free_count}")

    st.markdown("---")

    # Sector Breakdown Donut Chart & Top Companies Table
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📊 Sector Breakdown (11 Sectors)")
        if not df_sectors.empty:
            sector_counts = df_sectors['broad_sector'].value_counts().reset_index()
            sector_counts.columns = ['broad_sector', 'count']
            fig_donut = px.pie(
                sector_counts,
                values='count',
                names='broad_sector',
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        st.subheader("🏆 Top 5 Quality Companies")
        try:
            screener_df = get_screener_data()
            scored_df = calculate_composite_score(screener_df)
            top5 = scored_df[scored_df['year'] == selected_year].sort_values(by='composite_quality_score', ascending=False).head(5)
            
            if not top5.empty:
                display_cols = ['company_id', 'company_name', 'broad_sector', 'composite_quality_score', 'return_on_equity_pct', 'debt_to_equity']
                valid_cols = [c for c in display_cols if c in top5.columns]
                top5_display = top5[valid_cols].rename(columns={
                    'company_id': 'Ticker',
                    'company_name': 'Company Name',
                    'broad_sector': 'Sector',
                    'composite_quality_score': 'Quality Score',
                    'return_on_equity_pct': 'ROE (%)',
                    'debt_to_equity': 'D/E'
                })
                st.dataframe(top5_display.style.format({'Quality Score': '{:.1f}', 'ROE (%)': '{:.1f}%', 'D/E': '{:.2f}'}), hide_index=True, use_container_width=True)
            else:
                st.info("No quality scores calculated for selected year.")
        except Exception as e:
            st.info(f"Top 5 quality list unavailable: {e}")
