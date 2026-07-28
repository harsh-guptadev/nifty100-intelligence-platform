import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Nifty 100 Financial Intelligence Platform")

st.markdown(
    """
    ### Production-Grade Financial Analytics & Screening
    Welcome to the **Nifty 100 Financial Intelligence Platform**.
    
    Use the navigation menu in the left sidebar to explore:
    - **01 Home**: Executive overview, KPI summary, sector breakdown, and top-ranked quality companies.
    - **02 Profile**: Comprehensive single-company deep-dive (P&L, Balance Sheet, Cash Flow, 10-Yr trends, Pros & Cons).
    - **03 Screener**: Multi-criteria stock screening engine with 6 analyst presets and CSV export.
    - **04 Peers**: 8-Axis Polar Radar charts and side-by-side peer group comparisons.
    - **05 Trends**: Multi-metric historical trend overlay with YoY % change annotations.
    - **06 Sectors**: Sector bubble charts and comparative sub-sector medians.
    - **07 Capital**: Treemap visualizer of the 8 capital allocation matrix patterns.
    - **08 Reports**: Annual report links and downloadable PDF financial tearsheets.
    """
)

st.info("👈 Select a page from the sidebar to begin analysis.")
