import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.dashboard.utils.db import get_peers, get_ratios, get_companies
from src.screener.engine import get_screener_data, calculate_composite_score

st.title("🥊 Peer Group Analysis & Percentile Ranking")

df_peers = get_peers()
if df_peers.empty:
    st.error("No peer group data available.")
    st.stop()

# 11 Peer Group Dropdown
group_list = df_peers['peer_group_name'].unique().tolist()
selected_group = st.selectbox("Select Peer Group", options=group_list, index=0)

# Filter companies in selected peer group
group_companies = df_peers[df_peers['peer_group_name'] == selected_group]['company_id'].tolist()
df_comp = get_companies()
group_comp_info = df_comp[df_comp['id'].isin(group_companies)]

st.subheader(f"👥 Companies in `{selected_group}` ({len(group_comp_info)} companies)")

# Select Company for Radar Chart Comparison
selected_company = st.selectbox(
    "Select Benchmark Company for Radar Chart",
    options=group_companies,
    format_func=lambda x: f"{x} - {df_comp[df_comp['id']==x]['company_name'].values[0] if not df_comp[df_comp['id']==x].empty else x}"
)

# Fetch metrics for radar chart
screener_df = get_screener_data()
scored_df = calculate_composite_score(screener_df)

# Latest year group metrics
latest_group_df = scored_df[(scored_df['company_id'].isin(group_companies))].sort_values(by='year').groupby('company_id', as_index=False).last()

metrics = ['ROE', 'ROCE', 'NPM', 'D/E', 'FCF Score', 'PAT CAGR 5Yr', 'Rev CAGR 5Yr', 'Composite Score']
col_map = {
    'ROE': 'return_on_equity_pct',
    'ROCE': 'roce_percentage',
    'NPM': 'net_profit_margin_pct',
    'D/E': 'debt_to_equity',
    'FCF Score': 'free_cash_flow_cr',
    'PAT CAGR 5Yr': 'pat_cagr_5yr',
    'Rev CAGR 5Yr': 'revenue_cagr_5yr',
    'Composite Score': 'composite_quality_score'
}

comp_row = latest_group_df[latest_group_df['company_id'] == selected_company]

if not comp_row.empty:
    comp_vals = []
    group_avg_vals = []
    
    for m in metrics:
        col = col_map[m]
        val = comp_row.iloc[0].get(col, 0)
        val = val if pd.notna(val) else 0
        avg_val = latest_group_df[col].mean() if col in latest_group_df.columns else 0
        avg_val = avg_val if pd.notna(avg_val) else 0
        comp_vals.append(val)
        group_avg_vals.append(avg_val)
        
    # Scale values for radar visual (0-100 normalization)
    comp_scaled = [min(max(float(v), 0), 100) for v in comp_vals]
    avg_scaled = [min(max(float(v), 0), 100) for v in group_avg_vals]

    # Plotly Scatterpolar Radar Chart
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=comp_scaled + [comp_scaled[0]],
        theta=metrics + [metrics[0]],
        fill='toself',
        name=f'{selected_company} (Company)',
        line=dict(color='#1f77b4', width=2)
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=avg_scaled + [avg_scaled[0]],
        theta=metrics + [metrics[0]],
        name='Peer Group Average',
        line=dict(color='#ff7f0e', dash='dash', width=2)
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# Side-by-Side Peer Comparison Table
st.subheader("📊 Side-by-Side KPI & Percentile Comparison Table")

if not latest_group_df.empty:
    disp_cols = ['company_id', 'company_name', 'return_on_equity_pct', 'roce_percentage', 'net_profit_margin_pct', 'debt_to_equity', 'free_cash_flow_cr', 'revenue_cagr_5yr', 'composite_quality_score']
    valid_disp = [c for c in disp_cols if c in latest_group_df.columns]
    
    st.dataframe(
        latest_group_df[valid_disp].style.format({
            'return_on_equity_pct': '{:.1f}%',
            'roce_percentage': '{:.1f}%',
            'net_profit_margin_pct': '{:.1f}%',
            'debt_to_equity': '{:.2f}',
            'free_cash_flow_cr': '₹{:.1f}',
            'revenue_cagr_5yr': '{:.1f}%',
            'composite_quality_score': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True
    )
