import os
import sqlite3
import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
PORTFOLIO_DIR = "reports/portfolio"
os.makedirs(PORTFOLIO_DIR, exist_ok=True)


def _trend_arrow(curr, prev) -> str:
    """Returns ↑, ↓ or → based on YoY change within 2% threshold."""
    if pd.isna(curr) or pd.isna(prev) or prev == 0:
        return "→"
    pct_chg = ((curr - prev) / abs(prev)) * 100
    if pct_chg > 2:
        return "↑"
    elif pct_chg < -2:
        return "↓"
    return "→"


def generate_portfolio_summary_pdf() -> str:
    """
    Generates a single PDF with one page per company (sorted alphabetically by ticker).
    Each page shows: company name, sector, top 6 KPIs, and YoY trend arrows.
    Saves to reports/portfolio/portfolio_summary.pdf.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql_query(
            "SELECT id AS company_id, company_name FROM companies ORDER BY id", conn
        )
        df_sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
        df_rat = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    finally:
        conn.close()

    df_comp = df_comp.merge(df_sec, on="company_id", how="left")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PortTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=14,
        textColor=colors.HexColor('#002B49'), spaceAfter=4
    )
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, spaceAfter=2)
    normal = ParagraphStyle('Norm', parent=styles['Normal'], fontSize=8, leading=10)

    pdf_path = os.path.join(PORTFOLIO_DIR, "portfolio_summary.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )

    story = []

    kpi_cols = [
        ("return_on_equity_pct", "ROE (%)"),
        ("net_profit_margin_pct", "NPM (%)"),
        ("debt_to_equity", "D/E"),
        ("revenue_cagr_5yr", "5Yr Rev CAGR (%)"),
        ("free_cash_flow_cr", "FCF (₹ Cr)"),
        ("operating_profit_margin_pct", "OPM (%)"),
    ]

    for i, (_, c_row) in enumerate(df_comp.iterrows()):
        comp_id = c_row["company_id"]
        comp_name = c_row.get("company_name", comp_id)
        sector = c_row.get("broad_sector", "General")

        comp_rat = df_rat[df_rat["company_id"] == comp_id].sort_values("year")
        if comp_rat.empty:
            continue

        lat = comp_rat.iloc[-1]
        prev = comp_rat.iloc[-2] if len(comp_rat) >= 2 else None

        # Header
        story.append(Paragraph(f"{comp_name} <font size='10' color='#64748B'>({comp_id})</font>", title_style))
        story.append(Paragraph(f"<b>Sector:</b> {sector}  |  <b>Latest Year:</b> {lat.get('year', 'N/A')}", sub_style))
        story.append(Spacer(1, 6))

        # 6 KPI table with trend arrows
        kpi_rows = [["Metric", "Value", "YoY Trend"]]
        for col, label in kpi_cols:
            curr_val = lat.get(col)
            prev_val = prev.get(col) if prev is not None else None
            arrow = _trend_arrow(curr_val, prev_val)
            val_str = f"{curr_val:.1f}" if pd.notna(curr_val) else "N/A"
            kpi_rows.append([label, val_str, arrow])

        kpi_table = Table(kpi_rows, colWidths=[3.5 * inch, 2 * inch, 2 * inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F4F8')]),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(kpi_table)

        # Page break after every company except last
        if i < len(df_comp) - 1:
            story.append(PageBreak())

    doc.build(story)
    size_kb = os.path.getsize(pdf_path) // 1024
    print(f"Portfolio summary PDF generated: {pdf_path} ({size_kb} KB)")
    return pdf_path


if __name__ == "__main__":
    generate_portfolio_summary_pdf()
