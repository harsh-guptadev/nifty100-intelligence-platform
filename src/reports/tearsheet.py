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
TEARSHEET_DIR = "reports/tearsheets"
os.makedirs(TEARSHEET_DIR, exist_ok=True)

def generate_tearsheet_pdf(company_id: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql_query("SELECT * FROM companies WHERE id=?", conn, params=(company_id,))
        df_pl = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year", conn, params=(company_id,))
        df_bs = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year", conn, params=(company_id,))
        df_cf = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id=? ORDER BY year", conn, params=(company_id,))
        df_rat = pd.read_sql_query("SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year", conn, params=(company_id,))
        df_sec = pd.read_sql_query("SELECT * FROM sectors WHERE company_id=?", conn, params=(company_id,))
        df_pros = pd.read_sql_query("SELECT * FROM prosandcons WHERE company_id=?", conn, params=(company_id,))
    finally:
        conn.close()

    if df_comp.empty:
        return None

    company_name = df_comp.iloc[0].get("company_name", company_id)
    sector_name = df_sec.iloc[0].get("broad_sector", "General") if not df_sec.empty else "General"

    pdf_filename = os.path.join(TEARSHEET_DIR, f"{company_id}_tearsheet.pdf")
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#002B49'),
        spaceAfter=4
    )
    normal_style = ParagraphStyle('NormalText', parent=styles['Normal'], fontSize=9, leading=11)
    bold_style = ParagraphStyle('BoldText', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11)

    story = []

    # PAGE 1: Header Bar
    story.append(Paragraph(f"<b>{company_name} ({company_id})</b> — <i>{sector_name} Sector</i>", title_style))
    story.append(Spacer(1, 6))

    # 6 KPI Tiles in 2 Rows of 3
    lat_rat = df_rat.iloc[-1] if not df_rat.empty else {}
    roe_val = f"{lat_rat.get('return_on_equity_pct', 0):.1f}%" if pd.notna(lat_rat.get('return_on_equity_pct')) else "N/A"
    roce_val = f"{lat_rat.get('roce_percentage', 0):.1f}%" if pd.notna(lat_rat.get('roce_percentage')) else "N/A"
    npm_val = f"{lat_rat.get('net_profit_margin_pct', 0):.1f}%" if pd.notna(lat_rat.get('net_profit_margin_pct')) else "N/A"
    de_val = f"{lat_rat.get('debt_to_equity', 0):.2f}" if pd.notna(lat_rat.get('debt_to_equity')) else "N/A"
    cagr_val = f"{lat_rat.get('revenue_cagr_5yr', 0):.1f}%" if pd.notna(lat_rat.get('revenue_cagr_5yr')) else "N/A"
    fcf_val = f"₹{lat_rat.get('free_cash_flow_cr', 0):.1f} Cr" if pd.notna(lat_rat.get('free_cash_flow_cr')) else "N/A"

    kpi_data = [
        [Paragraph(f"<b>ROE</b><br/>{roe_val}", normal_style), Paragraph(f"<b>ROCE</b><br/>{roce_val}", normal_style), Paragraph(f"<b>Net Margin</b><br/>{npm_val}", normal_style)],
        [Paragraph(f"<b>D/E Ratio</b><br/>{de_val}", normal_style), Paragraph(f"<b>5Yr Rev CAGR</b><br/>{cagr_val}", normal_style), Paragraph(f"<b>Free Cash Flow</b><br/>{fcf_val}", normal_style)]
    ]
    kpi_table = Table(kpi_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0F4F8')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Revenue & Net Profit Bar Chart Image
    chart_path = f"output/{company_id}_pl_chart.png"
    plt.figure(figsize=(6, 2.2))
    if not df_pl.empty:
        plt.bar(df_pl['year'].astype(str), df_pl['sales'].fillna(0), color='#1f77b4', label='Revenue')
        plt.title(f"{company_id} Historical Revenue (₹ Cr)", fontsize=9)
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=120)
    plt.close()

    if os.path.exists(chart_path):
        story.append(Image(chart_path, width=7.5 * inch, height=2.5 * inch))
        story.append(Spacer(1, 10))

    # Dual-axis ROE & ROCE Chart
    line_chart_path = f"output/{company_id}_roe_chart.png"
    plt.figure(figsize=(6, 2.2))
    if not df_rat.empty:
        plt.plot(df_rat['year'].astype(str), df_rat['return_on_equity_pct'].fillna(0), marker='o', color='#ff7f0e', label='ROE (%)')
        if 'roce_percentage' in df_rat.columns:
            plt.plot(df_rat['year'].astype(str), df_rat['roce_percentage'].fillna(0), marker='s', color='#2ca02c', label='ROCE (%)')
        plt.title(f"{company_id} Return Ratios Trend (%)", fontsize=9)
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)
        plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(line_chart_path, dpi=120)
    plt.close()

    if os.path.exists(line_chart_path):
        story.append(Image(line_chart_path, width=7.5 * inch, height=2.5 * inch))

    # PAGE 2: Balance Sheet Composition & Pros/Cons
    story.append(PageBreak())
    story.append(Paragraph(f"<b>{company_name} ({company_id}) — Financial Position & Highlights</b>", title_style))
    story.append(Spacer(1, 8))

    # Pros & Cons Section
    pros_list = df_pros[df_pros['type'] == 'pro']['text'].tolist() if not df_pros.empty else ["Solid market presence."]
    cons_list = df_pros[df_pros['type'] == 'con']['text'].tolist() if not df_pros.empty else ["Macro-economic cyclical risks."]

    pros_text = "<br/>".join([f"• {p}" for p in pros_list[:4]])
    cons_text = "<br/>".join([f"• {c}" for c in cons_list[:4]])

    pc_data = [
        [Paragraph("<b>✅ Key Strengths (Pros)</b>", bold_style), Paragraph("<b>⚠️ Key Risks (Cons)</b>", bold_style)],
        [Paragraph(pros_text, normal_style), Paragraph(cons_text, normal_style)]
    ]
    pc_table = Table(pc_data, colWidths=[3.7 * inch, 3.7 * inch])
    pc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#DCFCE7')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#FEE2E2')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(pc_table)
    story.append(Spacer(1, 12))

    # Financial Ratios Table
    story.append(Paragraph("<b>📊 Historical Financial Ratios</b>", bold_style))
    story.append(Spacer(1, 4))
    
    if not df_rat.empty:
        tbl_data = [["Year", "ROE (%)", "NPM (%)", "D/E", "Revenue CAGR", "FCF (Cr)"]]
        for _, r in df_rat.tail(5).iterrows():
            tbl_data.append([
                str(r.get("year", "")),
                f"{r.get('return_on_equity_pct', 0):.1f}%" if pd.notna(r.get('return_on_equity_pct')) else "-",
                f"{r.get('net_profit_margin_pct', 0):.1f}%" if pd.notna(r.get('net_profit_margin_pct')) else "-",
                f"{r.get('debt_to_equity', 0):.2f}" if pd.notna(r.get('debt_to_equity')) else "-",
                f"{r.get('revenue_cagr_5yr', 0):.1f}%" if pd.notna(r.get('revenue_cagr_5yr')) else "-",
                f"{r.get('free_cash_flow_cr', 0):.1f}" if pd.notna(r.get('free_cash_flow_cr')) else "-"
            ])
        ratios_table = Table(tbl_data, colWidths=[1.2 * inch] * 6)
        ratios_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002B49')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(ratios_table)

    doc.build(story)

    # Clean up temporary chart images
    for p in [chart_path, line_chart_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return pdf_filename

def run_batch_tearsheet_generation():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql_query("SELECT id FROM companies", conn)
    finally:
        conn.close()

    count = 0
    for _, r in df_comp.iterrows():
        comp_id = r["id"]
        res = generate_tearsheet_pdf(comp_id)
        if res:
            count += 1

    print(f"Batch tearsheet generation complete. Generated {count} 2-page PDF tearsheets in '{TEARSHEET_DIR}/'.")
    return count

if __name__ == "__main__":
    run_batch_tearsheet_generation()
