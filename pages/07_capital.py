import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_companies
from src.analytics.cashflow_kpis import classify_capital_allocation
from src.analytics.ratios import get_db_connection

st.title("🧩 Capital Allocation Map & Treemap Visualizer")

# Load capital allocation patterns
try:
    conn = get_db_connection()
    df_cf = pd.read_sql("SELECT company_id, year, cfo_cr, cfi_cr, cff_cr FROM cashflow", conn)
    conn.close()
except Exception:
    df_cf = pd.DataFrame()

if df_cf.empty:
    st.error("Cash flow pattern data unavailable.")
    st.stop()

# Classify latest year for each company
df_latest_cf = df_cf.sort_values('year').groupby('company_id', as_index=False).last()

records = []
for _, r in df_latest_cf.iterrows():
    pattern, label = classify_capital_allocation(r['cfo_cr'], r['cfi_cr'], r['cff_cr'])
    records.append({
        'company_id': r['company_id'],
        'pattern': pattern,
        'pattern_label': label,
        'count': 1
    })

df_cap = pd.DataFrame(records)

# Treemap of all 92 companies grouped by 8 capital allocation patterns
st.subheader("🗺️ Treemap of Companies Grouped by Capital Allocation Strategy")
st.caption("Clicking a pattern tile filters the list of constituent companies below.")

fig_tree = px.treemap(
    df_cap,
    path=['pattern_label', 'company_id'],
    values='count',
    color='pattern_label',
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig_tree.update_layout(margin=dict(t=20, b=20, l=20, r=20))
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# Pattern Selection & Company Table
selected_label = st.selectbox(
    "Select Capital Allocation Pattern to Inspect Companies",
    options=df_cap['pattern_label'].unique().tolist(),
    index=0
)

filtered_companies = df_cap[df_cap['pattern_label'] == selected_label]
df_comp = get_companies()
comp_details = df_comp[df_comp['id'].isin(filtered_companies['company_id'])]

st.write(f"### Companies classified as **{selected_label}** ({len(comp_details)} companies)")
st.dataframe(comp_details[['id', 'company_name', 'face_value']].rename(columns={'id': 'Ticker', 'company_name': 'Company Name', 'face_value': 'Face Value'}), hide_index=True, use_container_width=True)
