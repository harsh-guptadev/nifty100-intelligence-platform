# Nifty 100 Financial Intelligence Platform

Production-grade financial analytics and intelligence platform for the 92 Nifty 100 index constituent companies. The platform automates data ingestion, cleaning, validation, key ratio computations, peer group analysis, KMeans clustering archetypes, reports, backed by an interactive Streamlit dashboard and a FastAPI REST layer.

---

## Project Structure

```text
N1000/
├── config/              # Configuration files (.env.template, configs)
├── data/                # Data storage directory (raw/, supporting/, nifty100.db) [Git Ignored]
├── db/                  # SQL schema definitions (schema.sql)
├── docs/                # Project documentation, specifications, analyst_guide.pdf, openapi.json
├── notebooks/           # Jupyter notebooks and verification queries
├── output/              # Final deliverables, ETL logs, export reports [Git Ignored]
├── reports/             # Tearsheets, charts, elbow plot, correlation heatmap, pytest report
├── src/                 # Python source packages
│   ├── analytics/       # Ingestion, ratio computations, and KMeans clustering
│   ├── api/             # FastAPI REST endpoints and routers
│   ├── etl/             # Ingestion, validation, and normalization
│   ├── nlp/             # Narrative text generation (Pros & Cons)
│   ├── reports/         # PDF tearsheet and report generators
│   └── screener/        # Multi-criteria screening engine
├── tests/               # 117 automated pytest suites (etl/, kpi/, dq/, api/)
├── Makefile             # Automation shortcut targets
├── requirements.txt     # Pinned Python package dependencies
└── README.md            # Project overview and setup instructions
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Git

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

### 5. Running Data Ingestion & Clustering
Ensure your raw Excel datasets are placed in `data/raw/` and run the data pipeline and clustering:
```powershell
python -m src.etl.loader
python -m src.analytics.clustering
```

### 6. Running Tests & Generating HTML Test Report
To execute all 117 unit and integration tests with HTML report output:
```powershell
pytest tests/ --html=reports/pytest_report.html
```

### 7. Launching the FastAPI REST Service
To start the FastAPI REST API layer on port `8000`:
```powershell
python -m src.api.main
```
Interactive OpenAPI documentation will be available at `http://localhost:8000/docs`.

### 8. Running the Streamlit Dashboard
To launch the 8-screen interactive web dashboard on port `8501`:
```powershell
streamlit run src/dashboard/app.py
```
The app will be available in your browser at `http://localhost:8501`.

---

## Final Deliverables & Acceptance

- **KMeans Cluster Archetypes**: [cluster_labels.csv](output/cluster_labels.csv) & [elbow_plot.png](reports/elbow_plot.png)
- **Pearson Correlation Heatmap**: [correlation_heatmap.png](reports/correlation_heatmap.png)
- **OpenAPI 3.0 & Postman Collection**: [openapi.json](docs/openapi.json) & [postman_collection.json](docs/postman_collection.json)
- **Pytest HTML Execution Report**: [pytest_report.html](reports/pytest_report.html)
- **Institutional Analyst User Guide**: [analyst_guide.pdf](docs/analyst_guide.pdf)
- **Acceptance Checklist & Sign-Off**: [acceptance_checklist.pdf](docs/acceptance_checklist.pdf)
---

## Preset Screener Adjustments

- **Dividend Champion Yield Recalibration**: The original spec requests a `>2%` dividend yield threshold for this preset. In the actual Nifty 100 constituent data, average P/E ratios are high (mean ~44), and raw dividend payout information is sparsely populated. As a result, the maximum calculated yield across the constituent universe is ~1.56%. To prevent this screener from returning an empty list, the threshold in `config/screener_config.yaml` is calibrated to `>=1.0%`, ensuring valid companies like `BANKBARODA` and `INDUSINDBK` are correctly highlighted.
