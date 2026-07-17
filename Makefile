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

.PHONY: setup load ratios test report dashboard api clean

setup:
	python -m venv .venv
	$(PIP) install -r requirements.txt
	$(PYTHON) -c "import nltk; nltk.download('vader_lexicon')"

load:
	$(PYTHON) src/etl/loader.py

ratios:
	$(PYTHON) src/analytics/ratios.py

test:
	$(PYTEST) tests/ --html=reports/pytest_report.html --self-contained-html

report:
	$(PYTHON) src/reports/portfolio_report.py

dashboard:
	$(STREAMLIT) run src/dashboard/app.py

api:
	$(UVICORN) src.api.main:app --reload --port 8000

clean:
	@echo Cleaning up temporary and cache files...
	-$(RM) src\etl\__pycache__ 2>nul || true
	-$(RM) src\analytics\__pycache__ 2>nul || true
	-$(RM) src\nlp\__pycache__ 2>nul || true
	-$(RM) src\dashboard\__pycache__ 2>nul || true
	-$(RM) src\api\__pycache__ 2>nul || true
	-$(RM) src\reports\__pycache__ 2>nul || true
	-$(RM) tests\etl\__pycache__ 2>nul || true
	-$(RM) tests\kpi\__pycache__ 2>nul || true
	-$(RM) tests\api\__pycache__ 2>nul || true
	-$(RM) tests\dq\__pycache__ 2>nul || true
	-$(RM) .pytest_cache 2>nul || true
	-$(RM) .ruff_cache 2>nul || true
	@echo Clean complete.
