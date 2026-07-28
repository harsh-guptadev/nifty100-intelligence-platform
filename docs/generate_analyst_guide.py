import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def build_analyst_guide():
    pdf_path = "docs/analyst_guide.pdf"
    os.makedirs("docs", exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'GuideTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15,
        alignment=1
    )
    
    h1_style = ParagraphStyle(
        'GuideH1',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=15,
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'GuideH2',
        parent=styles['Heading3'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        'GuideBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'GuideCode',
        parent=styles['Code'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        backColor=colors.HexColor('#F1F5F9'),
        borderColor=colors.HexColor('#CBD5E1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )

    story = []

    # PAGE 1: Cover & Table of Contents
    story.append(Spacer(1, 40))
    story.append(Paragraph("Nifty 100 Financial Intelligence Platform", title_style))
    story.append(Paragraph("Institutional User & Technical Analyst Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1E3A8A'), spaceAfter=20))
    
    story.append(Paragraph("<b>Version:</b> 1.0.0 | <b>Date:</b> July 2026", body_style))
    story.append(Paragraph("<b>Author:</b> Antigravity Data Science & Engineering Team", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Table of Contents", h2_style))
    toc_data = [
        ["Section", "Topic", "Target Page"],
        ["1", "Executive Platform Overview & System Architecture", "Page 2"],
        ["2", "Interactive Streamlit Dashboard Operations", "Page 3"],
        ["3", "Multi-Criteria Stock Screener & Preset Engine", "Page 4"],
        ["4", "Peer Group Radar Analysis & Percentile Scoring", "Page 5"],
        ["5", "Machine Learning & KMeans Clustering Archetypes", "Page 6"],
        ["6", "FastAPI REST API Reference & Integration", "Page 7"],
        ["7", "PDF Tearsheets & Report Generation Center", "Page 8"],
        ["8", "Data Quality Rules & Validation Framework", "Page 9"],
        ["9", "Troubleshooting, Performance & FAQs", "Page 10"]
    ]
    t_toc = Table(toc_data, colWidths=[60, 380, 80])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # PAGE 2: Section 1
    story.append(Paragraph("1. Platform Overview & System Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("The Nifty 100 Financial Intelligence Platform processes fundamental, market, and textual data for the constituent companies of the Nifty 100 index. The architecture integrates an ETL ingestion layer, a SQLite core database, pre-computed ratio analytics, machine learning clustering, an interactive 8-screen Streamlit dashboard, and a 16-endpoint REST API.", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("System Architecture Diagram:", h2_style))
    story.append(Paragraph("""
    [Raw Excel Datasets] -> [src/etl/loader & validator] -> [data/nifty100.db]<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br/>
    [src/analytics/ratios] -> [financial_ratios] ---------> [KMeans Clustering & Screener]<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|<br/>
    [FastAPI /api/v1 (Port 8000)] <------------------------ [Streamlit UI (Port 8501)]
    """, code_style))
    story.append(PageBreak())

    # PAGE 3: Section 2
    story.append(Paragraph("2. Interactive Streamlit Dashboard Operations", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("The Streamlit web interface is structured across 8 specialized views accessible via the sidebar navigation menu:", body_style))
    screens_data = [
        ["Screen", "Primary Functionality"],
        ["01_home.py", "Executive Summary: Universe KPIs, Sector Donut Chart, Quality Leaderboard."],
        ["02_profile.py", "Company Deep Dive: 10-Yr Financial Statements, Dual-Axis Charts, Pros/Cons."],
        ["03_screener.py", "Multi-Criteria Screener: 10 Sliders, 6 Analyst Presets, Live CSV Export."],
        ["04_peers.py", "Peer Analysis: Plotly 8-Axis Polar Radar Overlay & Percentiles."],
        ["05_trends.py", "Historical Trend Visualizer: Overlay 3 metrics with YoY % growth."],
        ["06_sectors.py", "Sector Diagnostics: Bubble Chart (Revenue vs ROE) & Medians."],
        ["07_capital.py", "Capital Allocation Matrix: Treemap Visualizer of 8 Cashflow Patterns."],
        ["08_reports.py", "Document Center: PDF Tearsheet Download Hub & BSE Filings Links."]
    ]
    t_screens = Table(screens_data, colWidths=[100, 420])
    t_screens.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_screens)
    story.append(PageBreak())

    # PAGE 4: Section 3
    story.append(Paragraph("3. Multi-Criteria Stock Screener & Preset Engine", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("The screener engine evaluates companies using cross-sectional percentile winsorization (P10/P90) and relative sector scoring.", body_style))
    story.append(Paragraph("Analyst Presets Available:", h2_style))
    presets_data = [
        ["Preset Name", "Core Filter Conditions"],
        ["Quality Compounders", "ROE >= 15%, D/E <= 0.5, FCF > 0, Rev CAGR 5Yr >= 10%"],
        ["Value Picks", "P/E <= 20, P/B <= 3.0, D/E <= 2.0, Div Yield >= 1.0%"],
        ["High Dividend Yield", "Div Yield >= 3.0%, D/E <= 1.0, FCF > 0"],
        ["High Growth", "Rev CAGR 5Yr >= 15%, PAT CAGR 5Yr >= 15%, ROE >= 12%"],
        ["Debt-Free Performers", "D/E == 0.0, ROE >= 15%, OPM >= 15%"],
        ["Turnaround Candidates", "Rev CAGR 3Yr >= 5%, FCF > 0, Deleveraging YoY"]
    ]
    t_presets = Table(presets_data, colWidths=[140, 380])
    t_presets.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_presets)
    story.append(PageBreak())

    # PAGE 5: Section 4
    story.append(Paragraph("4. Peer Group Radar Analysis & Percentile Scoring", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("Peer group comparison standardizes metric evaluations across 11 industry peer groups. Metrics are mapped to 8 polar radar axes normalized between 0th and 100th percentiles.", body_style))
    story.append(Paragraph("Radar Axes Metrics:", h2_style))
    story.append(Paragraph("1. Return on Equity (ROE %)<br/>2. Operating Profit Margin (OPM %)<br/>3. Net Profit Margin (NPM %)<br/>4. Debt-to-Equity (Inverse Scale)<br/>5. Interest Coverage Ratio (ICR)<br/>6. Asset Turnover<br/>7. 5-Year Revenue CAGR %<br/>8. Free Cash Flow (Cr)", body_style))
    story.append(PageBreak())

    # PAGE 6: Section 5
    story.append(Paragraph("5. Machine Learning & KMeans Clustering Archetypes", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("All 92 companies are categorized into 5 financial clusters using StandardScaler normalization and KMeans (k=5, random_state=42).", body_style))
    cluster_table = [
        ["Cluster ID", "Archetype Name", "Key Financial Attributes"],
        ["0", "High-Quality Compounders", "High ROE (>18%), Low Debt (D/E < 0.5), Strong FCF"],
        ["1", "Defensive Dividend Payers", "High Margins (OPM > 25%), Moderate Growth, High Payout"],
        ["2", "Emerging Growth", "High Sales CAGR (>15%), Reinvesting Cash Flows"],
        ["3", "Value Cyclicals", "Moderate Margins, Lower Multiples, Capital Intensive"],
        ["4", "Distressed or Turnaround", "High Leverage or Negative Profit Growth"]
    ]
    t_clusters = Table(cluster_table, colWidths=[70, 160, 290])
    t_clusters.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_clusters)
    story.append(PageBreak())

    # PAGE 7: Section 6
    story.append(Paragraph("6. FastAPI REST API Reference & Integration", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("The API service runs on <b>http://localhost:8000</b>. Interactive OpenAPI documentation is accessible at <b>/docs</b>.", body_style))
    story.append(Paragraph("Sample cURL Commands:", h2_style))
    story.append(Paragraph("curl -X GET \"http://localhost:8000/api/v1/health\"<br/>curl -X GET \"http://localhost:8000/api/v1/companies/TCS\"<br/>curl -X GET \"http://localhost:8000/api/v1/screener?min_roe=15&max_de=1.0\"<br/>curl -X GET \"http://localhost:8000/api/v1/sectors/Information%20Technology/companies\"", code_style))
    story.append(PageBreak())

    # PAGE 8: Section 7
    story.append(Paragraph("7. PDF Tearsheets & Report Generation Center", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("Automated PDF tearsheet generation creates 2-page executive tearsheets for all 92 companies saved in <b>reports/tearsheets/</b>.", body_style))
    story.append(Paragraph("Each tearsheet includes: Header metadata, 10-Yr financial summary table, Key KPI metric tiles, 8-Axis Polar Radar plot, and Automated Qualitative Pros & Cons narrative.", body_style))
    story.append(PageBreak())

    # PAGE 9: Section 8
    story.append(Paragraph("8. Data Quality Rules & Validation Framework", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("The platform executes 16 automated Data Quality rules across CRITICAL, WARNING, and INFO severities:", body_style))
    dq_data = [
        ["Rule ID", "Name", "Severity", "Description"],
        ["DQ-01", "Company PK Uniqueness", "CRITICAL", "Ticker uniqueness in companies master"],
        ["DQ-03", "FK Integrity", "CRITICAL", "Orphan record detection"],
        ["DQ-04", "BS Identity Equation", "WARNING", "Total Assets == Total Liabilities (<1% var)"],
        ["DQ-05", "OPM Cross-Check", "WARNING", "OPM vs (Operating Profit / Sales)"],
        ["DQ-07", "Year Format", "CRITICAL", "Standardized YYYY-MM format check"]
    ]
    t_dq = Table(dq_data, colWidths=[55, 140, 65, 260])
    t_dq.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_dq)
    story.append(PageBreak())

    # PAGE 10: Section 9
    story.append(Paragraph("9. Troubleshooting, Performance & FAQs", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563EB'), spaceAfter=10))
    story.append(Paragraph("Common Issues & Operations Guide:", h2_style))
    story.append(Paragraph("<b>Q1: How do I run the full test suite?</b><br/>Run <code>.venv\\Scripts\\python -m pytest tests/ --html=reports/pytest_report.html</code>", body_style))
    story.append(Paragraph("<b>Q2: How do I launch the FastAPI REST API?</b><br/>Run <code>.venv\\Scripts\\python -m src.api.main</code>", body_style))
    story.append(Paragraph("<b>Q3: How do I launch the Streamlit Dashboard?</b><br/>Run <code>streamlit run src/dashboard/app.py</code>", body_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Sign-Off Verification:", h2_style))
    story.append(Paragraph("All 20 Acceptance Gates (AC-01 through AC-20) verified and signed off.", body_style))

    doc.build(story)
    print("Generated docs/analyst_guide.pdf successfully.")

if __name__ == "__main__":
    build_analyst_guide()
