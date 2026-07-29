import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
SECTOR_DIR = "reports/sector"
os.makedirs(SECTOR_DIR, exist_ok=True)


def generate_sector_report(sector_name: str) -> str:
    """
    Generates a single-sector PDF report summarising median KPIs and listing all companies.
    Saves to reports/sector/{sector_name}_report.pdf.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df_sec = pd.read_sql_query(
            "SELECT company_id FROM sectors WHERE broad_sector=?", conn,
            params=(sector_name,)
        )
        ids = df_sec["company_id"].tolist()
        if not ids:
            conn.close()
            return None

        placeholders = ",".join("?" * len(ids))
        df_comp = pd.read_sql_query(
            f"SELECT id AS company_id, company_name FROM companies WHERE id IN ({placeholders})",
            conn, params=ids
        )
        df_rat = pd.read_sql_query(
            f"SELECT * FROM financial_ratios WHERE company_id IN ({placeholders})",
            conn, params=ids
        )
    finally:
        conn.close()

    # Latest year ratios per company
    latest_rat = df_rat.sort_values("year").groupby("company_id", as_index=False).last()
    merged = df_comp.merge(latest_rat, on="company_id", how="left")

    # Safe sector name for filename
    safe_sector = sector_name.replace(" ", "_").replace("/", "_")
    pdf_path = os.path.join(SECTOR_DIR, f"{safe_sector}_report.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'SectorTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=16,
        textColor=colors.HexColor('#002B49'), spaceAfter=6
    )
    sub_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, spaceAfter=4
    )
    normal = ParagraphStyle('N', parent=styles['Normal'], fontSize=8, leading=10)

    story = []

    # Title
    story.append(Paragraph(f"Sector Deep-Dive Report — {sector_name}", title_style))
    story.append(Paragraph(f"Companies in sector: {len(merged)}", normal))
    story.append(Spacer(1, 10))

    # Median KPI Summary table
    story.append(Paragraph("📊 Sector Median KPIs (Latest Year)", sub_style))

    kpi_cols = ["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
                "operating_profit_margin_pct", "revenue_cagr_5yr", "free_cash_flow_cr"]

    kpi_medians = {}
    for col in kpi_cols:
        if col in merged.columns:
            kpi_medians[col] = merged[col].dropna().median()

    med_rows = [["KPI", "Sector Median"]]
    kpi_labels = {
        "return_on_equity_pct": "Return on Equity (%)",
        "net_profit_margin_pct": "Net Profit Margin (%)",
        "debt_to_equity": "Debt to Equity",
        "operating_profit_margin_pct": "Operating Profit Margin (%)",
        "revenue_cagr_5yr": "5-Year Revenue CAGR (%)",
        "free_cash_flow_cr": "Free Cash Flow (₹ Cr)"
    }
    for col, val in kpi_medians.items():
        med_rows.append([kpi_labels.get(col, col), f"{val:.2f}" if pd.notna(val) else "N/A"])

    med_table = Table(med_rows, colWidths=[4 * inch, 3 * inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 12))

    # Company listing table
    story.append(Paragraph(f"📋 All Companies in {sector_name}", sub_style))

    comp_cols = ["company_id", "company_name", "return_on_equity_pct", "net_profit_margin_pct",
                 "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr",
                 "operating_profit_margin_pct"]
    valid_cols = [c for c in comp_cols if c in merged.columns]
    header_labels = {
        "company_id": "Ticker", "company_name": "Company",
        "return_on_equity_pct": "ROE %", "net_profit_margin_pct": "NPM %",
        "debt_to_equity": "D/E", "revenue_cagr_5yr": "Rev CAGR",
        "free_cash_flow_cr": "FCF Cr", "operating_profit_margin_pct": "OPM %"
    }

    comp_rows = [[Paragraph(header_labels.get(c, c), ParagraphStyle('H', fontName='Helvetica-Bold', fontSize=7)) for c in valid_cols]]
    for _, row in merged.iterrows():
        comp_rows.append([
            Paragraph(str(row.get(c, "N/A"))[:30], normal) if isinstance(row.get(c), str)
            else Paragraph(f"{row.get(c):.1f}" if pd.notna(row.get(c)) and isinstance(row.get(c), float) else str(row.get(c, "N/A")), normal)
            for c in valid_cols
        ])

    col_w = 7.5 * inch / len(valid_cols)
    comp_table = Table(comp_rows, colWidths=[col_w] * len(valid_cols), repeatRows=1)
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    story.append(comp_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "<i>⚠ Simulated Data Notice: Market cap, P/E, P/B, and dividend yield figures in this "
        "report are SIMULATED for this project — they are not real market data.</i>",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#64748B'), leading=9)
    ))

    doc.build(story)

    return pdf_path


def run_all_sector_reports():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_sec = pd.read_sql_query("SELECT DISTINCT broad_sector FROM sectors", conn)
    finally:
        conn.close()

    generated = []
    for _, row in df_sec.iterrows():
        sector = row["broad_sector"]
        path = generate_sector_report(sector)
        if path:
            generated.append(path)

    print(f"Generated {len(generated)} sector PDFs in '{SECTOR_DIR}/'.")
    return generated


if __name__ == "__main__":
    run_all_sector_reports()
