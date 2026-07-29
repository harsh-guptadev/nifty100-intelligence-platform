# 📊 Nifty 100 Financial Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pytest](https://img.shields.io/badge/Pytest-117%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Production-Grade Financial Analytics & Intelligence Engine for 92 Nifty 100 Index Constituents**  
> An end-to-end data pipeline automating ingestion, cleaning, ratio calculations, KMeans cluster archetypes, automated PDF reporting, interactive 8-screen Streamlit dashboard, and a FastAPI REST API layer.

---

## 🌟 Key Features

- 🔄 **Automated Data Pipeline (ETL)**: Ingests, normalizes, and validates financial data across 13 relational SQLite tables for 92 constituent companies.
- 🧮 **Comprehensive Financial Ratios**: Computes 23+ KPIs per company per year, including ROE, ROCE, NPM, OPM, Debt-to-Equity, FCF, CapEx, and 5-Year CAGRs (Revenue, PAT, EPS).
- 🎯 **Multi-Criteria Stock Screener**: Interactive filtering engine with customizable analyst presets (*Quality Compounders*, *Value Picks*, *Growth Accelerators*, *Dividend Champions*, *Debt-Free Blue Chips*, *Turnaround Watch*).
- 📊 **KMeans Cluster Archetypes**: Unsupervised Machine Learning grouping companies into 5 strategic financial archetypes, complete with Elbow Plot optimization and Pearson Correlation heatmaps.
- 📄 **Institutional PDF Reports**: Automated generation of 2-page company tearsheets (92 PDFs), sector-wide deep-dive reports (10 PDFs), and a consolidated portfolio summary PDF.
- ⚡ **FastAPI REST API Layer**: 8 RESTful routers (`/api/v1/*`) serving company fundamentals, sector analyses, peer metrics, and valuation flags with interactive OpenAPI documentation.
- 🖥️ **8-Screen Interactive Streamlit Dashboard**: User-friendly visual interface covering Home, Profile, Screener, Peers, Trends, Sectors, Capital Allocation, and Reports.

---

## 🏗️ Project Architecture & Structure

```text
N1000/
├── config/              # Configuration files (.env.template, screener_config.yaml)
├── data/                # Database and data files (raw/, supporting/, nifty100.db) [Git Ignored]
├── db/                  # SQL schema definitions (schema.sql)
├── docs/                # OpenAPI spec, Postman collection, analyst guide PDF
├── notebooks/           # Jupyter notebooks and verification queries
├── output/              # Final deliverables, ETL logs, export reports [Git Ignored]
├── pages/               # Streamlit multi-page interface (01_home to 08_reports)
├── reports/             # Tearsheets, charts, elbow plot, correlation heatmap, pytest report
├── src/                 # Main Python source packages
│   ├── analytics/       # Ingestion, ratio computations, valuation, and KMeans clustering
│   ├── api/             # FastAPI REST endpoints and routers
│   ├── etl/             # Ingestion, validation, and normalization pipeline
│   ├── nlp/             # Narrative text generation (Pros & Cons)
│   ├── reports/         # PDF tearsheet, sector, and portfolio summary generators
│   └── screener/        # Multi-criteria screening engine
├── tests/               # 117 automated pytest test suites (etl/, kpi/, dq/, api/)
├── app.py               # Streamlit application entry point
├── Makefile             # Automation shortcut targets
├── requirements.txt     # Pinned Python package dependencies
└── README.md            # Project overview and setup instructions
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- **Git**

### 2. Environment Setup
Clone the repository, create a virtual environment, and activate it:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
Install the pinned dependencies:
```powershell
pip install -r requirements.txt
```

### 4. Configuration
Create a local `.env` file from the provided template:
```powershell
copy config\.env.template .env
```

### 5. Running the Full Data Pipeline
Ensure your raw Excel datasets are placed in `data/raw/`. Run each step in order — each depends on the previous:

```powershell
# Step 1: Ingest all Excel files into nifty100.db
python -m src.etl.loader

# Step 2: Compute and populate the financial_ratios table
python -m src.analytics.populate_ratios

# Step 3: Run screener analysis and export Excel outputs
python -m src.screener.run_analysis

# Step 4: Run valuation flags and export valuation reports
python -m src.analytics.valuation

# Step 5: Run cash-flow KPI analysis
python -m src.analytics.cashflow_kpis

# Step 6: Parse and generate NLP pros/cons narratives
python -m src.nlp.parser
python -m src.nlp.pros_cons_generator

# Step 7: Run KMeans clustering and generate cluster_labels.csv + plots
python -m src.analytics.clustering

# Step 8: Generate all PDF tearsheets, sector reports, and portfolio summary
python -m src.reports.tearsheet
python -m src.reports.sector_report
python -m src.reports.portfolio_summary
```

> 💡 **Tip:** `make all` runs the full pipeline end-to-end in the correct order automatically!

### 6. Running Tests & HTML Report
To execute all 117 unit and integration tests with HTML report generation:
```powershell
pytest tests/ --html=reports/pytest_report.html --self-contained-html
```

### 7. Launching the FastAPI REST API
To start the FastAPI REST API layer on port `8000`:
```powershell
python -m src.api.main
```
Interactive OpenAPI documentation will be available at `http://localhost:8000/docs`.

### 8. Running the Streamlit Dashboard
To launch the 8-screen interactive web dashboard on port `8501`:
```powershell
streamlit run app.py
```
The app must be launched from `app.py` so Streamlit discovers the `pages/` directory. Access it in your browser at `http://localhost:8501`.

---

## 📦 Final Deliverables & Artifacts

- **KMeans Cluster Archetypes**: [`output/cluster_labels.csv`](output/cluster_labels.csv) & [`reports/elbow_plot.png`](reports/elbow_plot.png)
- **Pearson Correlation Heatmap**: [`reports/correlation_heatmap.png`](reports/correlation_heatmap.png)
- **OpenAPI 3.0 & Postman Collection**: [`docs/openapi.json`](docs/openapi.json) & [`docs/postman_collection.json`](docs/postman_collection.json)
- **Pytest HTML Execution Report**: [`reports/pytest_report.html`](reports/pytest_report.html)
- **Institutional Analyst User Guide**: [`docs/analyst_guide.pdf`](docs/analyst_guide.pdf)
- **Acceptance Checklist & Sign-Off**: [`docs/acceptance_checklist.pdf`](docs/acceptance_checklist.pdf)

---

## ⚙️ Calibration Notes

- **Dividend Champion Yield Recalibration**: The original spec requests a `>2%` dividend yield threshold for this preset. In the actual Nifty 100 constituent data, average P/E ratios are high (mean ~44), and raw dividend payout information is sparsely populated. As a result, the maximum calculated yield across the constituent universe is ~1.56%. To prevent this screener from returning an empty list, the threshold in `config/screener_config.yaml` is calibrated to `>=1.0%`, ensuring valid companies like `BANKBARODA` and `INDUSINDBK` are correctly highlighted.

---

## 👤 Author

**Harsh Gupta**  
*Final-year B.Tech (AI & ML), JSS Academy of Technical Education*  
[![GitHub](https://img.shields.io/badge/GitHub-harsh--guptadev-181717.svg?logo=github&logoColor=white)](https://github.com/harsh-guptadev)

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
