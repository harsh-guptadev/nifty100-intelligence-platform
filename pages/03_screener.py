import streamlit as st
import pandas as pd
from src.screener.engine import get_screener_data, apply_filters, calculate_composite_score

st.title("🔍 Multi-Criteria Stock Screener Engine")

screener_df = get_screener_data()
screener_df = calculate_composite_score(screener_df)

# Sidebar Presets & Metric Sliders
st.sidebar.header("🎯 Analyst Presets")

preset_quality = st.sidebar.button("Quality Compounders")
preset_value = st.sidebar.button("Value Pick")
preset_growth = st.sidebar.button("Growth Accelerator")
preset_dividend = st.sidebar.button("Dividend Champions")
preset_debt_free = st.sidebar.button("Debt-Free Blue Chips")
preset_turnaround = st.sidebar.button("Turnaround Watch")

# Default Slider Values
slider_defaults = {
    'roe_min': 0.0,
    'de_max': 10.0,
    'fcf_min': -5000.0,
    'rev_cagr_min': -50.0,
    'pat_cagr_min': -50.0,
    'opm_min': -20.0,
    'pe_max': 200.0,
    'pb_max': 50.0,
    'div_yield_min': 0.0,
    'icr_min': 0.0
}

# Auto-fill preset logic
if preset_quality:
    slider_defaults.update({'roe_min': 15.0, 'de_max': 1.0, 'fcf_min': 0.0, 'rev_cagr_min': 10.0})
elif preset_value:
    slider_defaults.update({'pe_max': 20.0, 'pb_max': 3.0, 'de_max': 2.0, 'div_yield_min': 1.0})
elif preset_growth:
    slider_defaults.update({'pat_cagr_min': 20.0, 'rev_cagr_min': 15.0, 'de_max': 2.0})
elif preset_dividend:
    slider_defaults.update({'div_yield_min': 2.0, 'fcf_min': 0.0})
elif preset_debt_free:
    slider_defaults.update({'de_max': 0.0, 'roe_min': 12.0})
elif preset_turnaround:
    slider_defaults.update({'rev_cagr_min': 10.0, 'fcf_min': 0.0})

st.sidebar.header("⚙️ Metric Sliders")
roe_min = st.sidebar.slider("ROE Min (%)", 0.0, 50.0, float(slider_defaults['roe_min']))
de_max = st.sidebar.slider("D/E Max", 0.0, 10.0, float(slider_defaults['de_max']))
fcf_min = st.sidebar.slider("FCF Min (₹ Cr)", -5000.0, 10000.0, float(slider_defaults['fcf_min']))
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5Yr Min (%)", -20.0, 50.0, float(slider_defaults['rev_cagr_min']))
pat_cagr_min = st.sidebar.slider("PAT CAGR 5Yr Min (%)", -20.0, 50.0, float(slider_defaults['pat_cagr_min']))
opm_min = st.sidebar.slider("OPM Min (%)", -10.0, 50.0, float(slider_defaults['opm_min']))
pe_max = st.sidebar.slider("P/E Max", 0.0, 150.0, float(slider_defaults['pe_max']))
pb_max = st.sidebar.slider("P/B Max", 0.0, 30.0, float(slider_defaults['pb_max']))
div_yield_min = st.sidebar.slider("Dividend Yield Min (%)", 0.0, 10.0, float(slider_defaults['div_yield_min']))
icr_min = st.sidebar.slider("ICR Min", 0.0, 20.0, float(slider_defaults['icr_min']))

# Build Filters Dictionary
custom_filters = {
    'return_on_equity_pct_min': roe_min,
    'debt_to_equity_max': de_max,
    'free_cash_flow_cr_min': fcf_min,
    'revenue_cagr_5yr_min': rev_cagr_min,
    'pat_cagr_5yr_min': pat_cagr_min,
    'operating_profit_margin_pct_min': opm_min,
    'pe_ratio_max': pe_max,
    'pb_ratio_max': pb_max,
    'dividend_yield_min': div_yield_min,
    'interest_coverage_min': icr_min
}

# Apply Filters & Latest Year
df_latest = screener_df.sort_values(by='year').groupby('company_id', as_index=False).last()
filtered_df = apply_filters(df_latest, custom_filters)
filtered_df = filtered_df.sort_values(by='composite_quality_score', ascending=False)

# Results Header & Count Label
st.success(f"🎯 **{len(filtered_df)} companies match your filter criteria**")

if not filtered_df.empty:
    display_cols = [
        'company_id', 'company_name', 'broad_sector', 'composite_quality_score',
        'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr',
        'revenue_cagr_5yr', 'pat_cagr_5yr', 'operating_profit_margin_pct'
    ]
    valid_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(
        filtered_df[valid_cols].style.format({
            'composite_quality_score': '{:.1f}',
            'return_on_equity_pct': '{:.1f}%',
            'debt_to_equity': '{:.2f}',
            'free_cash_flow_cr': '₹{:.1f}',
            'revenue_cagr_5yr': '{:.1f}%',
            'pat_cagr_5yr': '{:.1f}%',
            'operating_profit_margin_pct': '{:.1f}%'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # CSV Export Button
    csv_data = filtered_df[valid_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Screener Results CSV",
        data=csv_data,
        file_name="screener_results.csv",
        mime="text/csv"
    )
else:
    st.info("No companies meet all the selected filter criteria. Try relaxing your slider bounds.")
