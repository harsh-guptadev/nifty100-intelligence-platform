import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_sectors, get_companies
from src.screener.engine import get_screener_data

st.title("🏭 Sector & Sub-Sector Deep-Dive Analysis")
st.caption(
    "⚠️ **Simulated Data Notice:** Market cap, P/E, P/B, and dividend yield figures "
    "are **SIMULATED** for this project — not real market data."
)


df_sec = get_sectors()
if df_sec.empty:
    st.error("No sector data available.")
    st.stop()

# Sector Dropdown
broad_sectors = df_sec['broad_sector'].unique().tolist()
selected_sector = st.selectbox("Select Broad Sector", options=broad_sectors, index=0)

# Fetch latest company screener metrics
screener_df = get_screener_data()
latest_df = screener_df.sort_values(by='year').groupby('company_id', as_index=False).last()

sector_companies = df_sec[df_sec['broad_sector'] == selected_sector]
sec_df = latest_df[latest_df['company_id'].isin(sector_companies['company_id'])]

# Merge sub-sector metadata
sec_df = sec_df.merge(df_sec[['company_id', 'sub_sector']], on='company_id', how='left')

st.subheader(f"📊 Sector Bubble Chart: `{selected_sector}` ({len(sec_df)} companies)")
st.caption("X = Revenue (₹ Cr), Y = ROE (%), Bubble Size = Market Cap / Net Profit, Color = Sub-Sector")

if not sec_df.empty:
    sec_df['bubble_size'] = sec_df['sales'].apply(lambda x: max(float(x), 10.0) if pd.notna(x) else 10.0)
    
    fig_bubble = px.scatter(
        sec_df,
        x="sales",
        y="return_on_equity_pct",
        size="bubble_size",
        color="sub_sector",
        hover_name="company_id",
        text="company_id",
        size_max=45,
        labels={"sales": "Revenue (₹ Crore)", "return_on_equity_pct": "ROE (%)"}
    )
    fig_bubble.update_traces(textposition='top center')
    fig_bubble.update_layout(margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# Sector Median KPI Bar Chart Below
st.subheader("📊 Sector Median KPI Comparison Across All 11 Sectors")

df_merged_all = latest_df.merge(df_sec[['company_id', 'broad_sector']], on='company_id', how='left')
sector_medians = df_merged_all.groupby('broad_sector')[['return_on_equity_pct', 'operating_profit_margin_pct', 'debt_to_equity']].median().reset_index()

fig_median_bar = px.bar(
    sector_medians,
    x='broad_sector',
    y='return_on_equity_pct',
    title='Median ROE (%) Across Broad Sectors',
    color='return_on_equity_pct',
    color_continuous_scale='Viridis',
    labels={'broad_sector': 'Broad Sector', 'return_on_equity_pct': 'Median ROE (%)'}
)
fig_median_bar.update_layout(margin=dict(t=40, b=30, l=30, r=30))
st.plotly_chart(fig_median_bar, use_container_width=True)
