# Nifty 100 Financial Intelligence Platform

Production-grade financial analytics and intelligence platform for the 92 Nifty 100 index constituent companies. The platform automates data ingestion, cleaning, validation, key ratio computations, peer group analysis, and reports, backed by an interactive Streamlit dashboard and a FastAPI REST layer.

---

## Project Structure

```text
N1000/
├── config/              # Configuration files (.env.template, configs)
├── data/                # Data storage directory (raw/, supporting/, nifty100.db) [Git Ignored]
├── db/                  # SQL schema definitions (schema.sql)
├── docs/                # Project documentation and specifications
├── notebooks/           # Jupyter notebooks and verification queries
├── output/              # ETL logs and export reports [Git Ignored]
├── reports/             # Tearsheets and charts output [Git Ignored]
├── src/                 # Python source packages
│   └── etl/             # Ingestion, validation, and normalization
├── tests/               # Pytest testing suites (tests/etl/, tests/kpi/, etc.)
├── .gitignore           # Git ignore file
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
Install the pinned dependencies (pandas, openpyxl, pytest, streamlit, etc.):
```powershell
pip install -r requirements.txt
```

### 4. Configuration
Create a local `.env` file from the provided template:
```powershell
copy config\.env.template .env
```

### 5. Running the Data Ingestion (ETL)
Ensure your raw Excel datasets are placed in `data/raw/` and supplementary datasets in `data/supporting/`. Then run the loader:
```powershell
python -m src.etl.loader
```
*(Alternatively, run `make load` if a make tool is available).*

### 6. Running Tests
To run the automated test suite verifying normalization and validation rules:
```powershell
pytest
```
*(Alternatively, run `make test` to generate an HTML test coverage report under `reports/pytest_report.html`).*

---

## Sprint Notes & Accepted Exceptions

### Sprint 2
- **`composite_quality_score` Deferral**: As per agreement and design exception, the population of `composite_quality_score` in the `financial_ratios` table is deferred to Sprint 3. The scoring requires cross-sectional winsorization (P10/P90) and relative weights which are coupled with the ranking and peer-group engines of Sprint 3. This column is intentionally set to `NULL` for now and will be populated during Sprint 3 execution.

