# Nifty 100 Financial Intelligence Platform Makefile
# Environment Detection: Windows vs Linux/macOS
ifeq ($(OS),Windows_NT)
    VENV_BIN = .venv\Scripts
    PYTHON = $(VENV_BIN)\python.exe
    PIP = $(VENV_BIN)\pip.exe
    PYTEST = $(VENV_BIN)\pytest.exe
    STREAMLIT = $(VENV_BIN)\streamlit.exe
    UVICORN = $(VENV_BIN)\uvicorn.exe
    RM = rmdir /s /q
    DEL = del /q
else
    VENV_BIN = .venv/bin
    PYTHON = $(VENV_BIN)/python
    PIP = $(VENV_BIN)/pip
    PYTEST = $(VENV_BIN)/pytest
    STREAMLIT = $(VENV_BIN)/streamlit
    UVICORN = $(VENV_BIN)/uvicorn
    RM = rm -rf
    DEL = rm -f
endif

.PHONY: setup load ratios analysis valuation cashflow nlp cluster report test dashboard api clean all

setup:
	python -m venv .venv
	$(PIP) install -r requirements.txt

# D-01/D-02/D-03: Ingest all Excel files into nifty100.db
load:
	$(PYTHON) -m src.etl.loader

# D-05: Compute and populate the financial_ratios table
ratios:
	$(PYTHON) -m src.analytics.populate_ratios

# D-06: Run screener analysis and export screener_output.xlsx / peer_comparison.xlsx / etc.
analysis:
	$(PYTHON) -m src.screener.run_analysis

# D-07: Run valuation flags and export valuation_summary.xlsx / valuation_flags.csv
valuation:
	$(PYTHON) -m src.analytics.valuation

# D-08: Run cash-flow KPI analysis and export cashflow_intelligence.xlsx
cashflow:
	$(PYTHON) -m src.analytics.cashflow_kpis

# D-09/D-10: Parse existing pros/cons and generate NLP narratives
nlp:
	$(PYTHON) -m src.nlp.parser
	$(PYTHON) -m src.nlp.pros_cons_generator

# D-19: Run KMeans clustering and generate cluster_labels.csv + plots
cluster:
	$(PYTHON) -m src.analytics.clustering

# D-16/D-17/D-18: Generate all company tearsheets, sector reports, and portfolio PDF
report:
	$(PYTHON) -m src.reports.tearsheet
	$(PYTHON) -m src.reports.sector_report
	$(PYTHON) -m src.reports.portfolio_summary

# Run all 117 pytest tests and generate HTML report
# Run this before every git commit. Zero failures are mandatory.
test:
	$(PYTEST) tests/ --html=reports/pytest_report.html --self-contained-html

# D-11: Launch Streamlit Dashboard on localhost:8501
# Runs from the project root (app.py) so the pages/ directory is discovered correctly.
dashboard:
	$(STREAMLIT) run app.py

# D-20: Launch FastAPI REST server on localhost:8000
api:
	$(UVICORN) src.api.main:app --reload --port 8000

# Run the complete pipeline end-to-end in dependency order.
# Use this after a fresh clone: make setup && make all
all: load ratios analysis valuation cashflow nlp cluster report test

# Remove cache (.pyc) and test artifacts. Database remains untouched.
clean:
	@echo Cleaning up temporary and cache files...
	-$(RM) src\etl\__pycache__ 2>nul || true
	-$(RM) src\analytics\__pycache__ 2>nul || true
	-$(RM) src\nlp\__pycache__ 2>nul || true
	-$(RM) src\dashboard\__pycache__ 2>nul || true
	-$(RM) src\api\__pycache__ 2>nul || true
	-$(RM) src\api\routers\__pycache__ 2>nul || true
	-$(RM) src\reports\__pycache__ 2>nul || true
	-$(RM) src\screener\__pycache__ 2>nul || true
	-$(RM) tests\etl\__pycache__ 2>nul || true
	-$(RM) tests\kpi\__pycache__ 2>nul || true
	-$(RM) tests\api\__pycache__ 2>nul || true
	-$(RM) tests\dq\__pycache__ 2>nul || true
	-$(RM) tests\__pycache__ 2>nul || true
	-$(RM) .pytest_cache 2>nul || true
	-$(RM) .ruff_cache 2>nul || true
	@echo Clean complete.
