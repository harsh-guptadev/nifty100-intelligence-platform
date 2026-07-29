import os
import sqlite3
import pandas as pd
from datetime import date
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
DAILY_DIR = "reports/daily"
os.makedirs(DAILY_DIR, exist_ok=True)

def generate_daily_report_pdf(report_date: str = None) -> str:
    """
    Generates an executive Nifty 100 Daily Financial Intelligence Summary PDF report.
    Pulls real database aggregates, top gainers/movers, sector performance, and market highlights.
    Saves to reports/daily/daily_report_{YYYY-MM-DD}.pdf.
    """
    if not report_date:
        report_date = date.today().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql_query("SELECT id, company_name FROM companies", conn)
        df_sec = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector, index_weight_pct FROM sectors", conn)
        df_rat = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year DESC", conn)
        df_mcap = pd.read_sql_query("SELECT * FROM market_cap ORDER BY year DESC", conn)
    finally:
        conn.close()

    # Process latest data aggregates
    latest_rat = df_rat.groupby("company_id", as_index=False).first() if not df_rat.empty else pd.DataFrame()
    latest_mcap = df_mcap.groupby("company_id", as_index=False).first() if not df_mcap.empty else pd.DataFrame()
    
    merged = df_comp.merge(df_sec, left_on="id", right_on="company_id", how="left")
    if not latest_rat.empty:
        merged = merged.merge(latest_rat, left_on="id", right_on="company_id", how="left", suffixes=("", "_rat"))
    if not latest_mcap.empty:
        merged = merged.merge(latest_mcap, left_on="id", right_on="company_id", how="left", suffixes=("", "_mcap"))

    # Top ROE & Top Revenue CAGR lists
    top_roe = merged.sort_values("return_on_equity_pct", ascending=False).head(5) if "return_on_equity_pct" in merged.columns else pd.DataFrame()
    top_growth = merged.sort_values("revenue_cagr_5yr", ascending=False).head(5) if "revenue_cagr_5yr" in merged.columns else pd.DataFrame()

    # Sector summary median ROE & OPM
    sector_summary = merged.groupby("broad_sector")[["return_on_equity_pct", "operating_profit_margin_pct"]].median().reset_index() if "broad_sector" in merged.columns else pd.DataFrame()

    pdf_path = os.path.join(DAILY_DIR, f"daily_report_{report_date}.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.4 * inch, rightMargin=0.4 * inch,
        topMargin=0.4 * inch, bottomMargin=0.4 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18,
        textColor=colors.HexColor('#002B49'), spaceAfter=2
    )
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#475569'), spaceAfter=8)
    section_heading = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#002B49'), spaceAfter=6)
    bold_txt = ParagraphStyle('BText', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10)
    norm_txt = ParagraphStyle('NText', parent=styles['Normal'], fontSize=8, leading=10)

    story = []

    # Title & Header
    story.append(Paragraph("📈 <b>Nifty 100 Daily Financial Intelligence Summary</b>", title_style))
    story.append(Paragraph(f"Date: <b>{report_date}</b> | Universe: <b>92 Nifty 100 Constituents</b> | Coverage: <b>11 Broad Sectors</b>", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#002B49'), spaceAfter=10))

    # Executive Overview KPI Cards (2x3 grid)
    total_companies = len(merged)
    med_roe = merged["return_on_equity_pct"].median() if "return_on_equity_pct" in merged.columns else 0.0
    med_npm = merged["net_profit_margin_pct"].median() if "net_profit_margin_pct" in merged.columns else 0.0
    med_opm = merged["operating_profit_margin_pct"].median() if "operating_profit_margin_pct" in merged.columns else 0.0
    avg_de = merged["debt_to_equity"].median() if "debt_to_equity" in merged.columns else 0.0
    med_cagr = merged["revenue_cagr_5yr"].median() if "revenue_cagr_5yr" in merged.columns else 0.0

    kpi_card_data = [
        [
            Paragraph(f"<b>Tracked Universe</b><br/><font size=12 color='#002B49'><b>{total_companies} Companies</b></font>", norm_txt),
            Paragraph(f"<b>Median ROE</b><br/><font size=12 color='#10B981'><b>{med_roe:.1f}%</b></font>", norm_txt),
            Paragraph(f"<b>Median OPM</b><br/><font size=12 color='#2563EB'><b>{med_opm:.1f}%</b></font>", norm_txt)
        ],
        [
            Paragraph(f"<b>Median Net Margin</b><br/><font size=12 color='#059669'><b>{med_npm:.1f}%</b></font>", norm_txt),
            Paragraph(f"<b>Median Debt/Equity</b><br/><font size=12 color='#D97706'><b>{avg_de:.2f}</b></font>", norm_txt),
            Paragraph(f"<b>5-Yr Rev CAGR</b><br/><font size=12 color='#7C3AED'><b>{med_cagr:.1f}%</b></font>", norm_txt)
        ]
    ]

    kpi_table = Table(kpi_card_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # Top Performers Section (2 columns side by side: Top ROE & Top Growth)
    story.append(Paragraph("⭐ <b>Top Performing Constituents</b>", section_heading))

    roe_rows = [[Paragraph("Ticker", bold_txt), Paragraph("Company", bold_txt), Paragraph("ROE (%)", bold_txt)]]
    for _, r in top_roe.iterrows():
        roe_rows.append([
            Paragraph(str(r.get("id", "")), norm_txt),
            Paragraph(str(r.get("company_name", ""))[:22], norm_txt),
            Paragraph(f"{r.get('return_on_equity_pct', 0):.1f}%", norm_txt)
        ])

    growth_rows = [[Paragraph("Ticker", bold_txt), Paragraph("Company", bold_txt), Paragraph("5Yr Rev CAGR", bold_txt)]]
    for _, r in top_growth.iterrows():
        growth_rows.append([
            Paragraph(str(r.get("id", "")), norm_txt),
            Paragraph(str(r.get("company_name", ""))[:22], norm_txt),
            Paragraph(f"{r.get('revenue_cagr_5yr', 0):.1f}%", norm_txt)
        ])

    t1 = Table(roe_rows, colWidths=[0.8*inch, 1.8*inch, 1.0*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))

    t2 = Table(growth_rows, colWidths=[0.8*inch, 1.8*inch, 1.0*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))

    side_by_side = Table([
        [Paragraph("<b>Top 5 ROE Leaders</b>", bold_txt), Paragraph("<b>Top 5 5-Yr Growth Leaders</b>", bold_txt)],
        [t1, t2]
    ], colWidths=[3.7 * inch, 3.7 * inch])
    side_by_side.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(side_by_side)
    story.append(Spacer(1, 14))

    # Sector Snapshot
    story.append(Paragraph("🏭 <b>Broad Sector Median Performance Snapshot</b>", section_heading))
    sec_rows = [[Paragraph("Broad Sector", bold_txt), Paragraph("Median ROE (%)", bold_txt), Paragraph("Median OPM (%)", bold_txt)]]
    for _, r in sector_summary.iterrows():
        sec_rows.append([
            Paragraph(str(r.get("broad_sector", "")), norm_txt),
            Paragraph(f"{r.get('return_on_equity_pct', 0):.1f}%", norm_txt),
            Paragraph(f"{r.get('operating_profit_margin_pct', 0):.1f}%", norm_txt)
        ])

    sec_table = Table(sec_rows, colWidths=[3.5 * inch, 2.0 * inch, 2.0 * inch])
    sec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(sec_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "<i>⚠ Simulated Data Notice: Market cap, P/E, P/B, and dividend yield figures in this "
        "report are SIMULATED for this project — they are not real market data.</i>",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#64748B'), leading=9)
    ))

    doc.build(story)
    size_kb = os.path.getsize(pdf_path) // 1024
    print(f"Daily Report PDF generated successfully: {pdf_path} ({size_kb} KB)")
    return pdf_path

if __name__ == "__main__":
    generate_daily_report_pdf()
