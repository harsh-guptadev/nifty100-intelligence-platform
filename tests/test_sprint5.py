import os
import pytest
import pandas as pd
from src.nlp.pros_cons_generator import generate_pros_and_cons

def test_pros_cons_every_company_has_both():
    """Every company must have at least 1 Pro and 1 Con with confidence > 60%."""
    df = generate_pros_and_cons()
    assert not df.empty, "Pros/Cons output must not be empty"
    assert "company_id" in df.columns
    assert "type" in df.columns
    assert "confidence_pct" in df.columns

    # Check confidence filter
    assert (df["confidence_pct"] > 60).all(), "All entries must have confidence > 60%"

    # Check at least 1 pro per company
    pros_per_company = df[df["type"] == "pro"].groupby("company_id").size()
    assert len(pros_per_company) == 92, f"Expected 92 companies with pros, got {len(pros_per_company)}"

    # Check at least 1 con per company
    cons_per_company = df[df["type"] == "con"].groupby("company_id").size()
    assert len(cons_per_company) == 92, f"Expected 92 companies with cons, got {len(cons_per_company)}"


def test_pros_cons_output_file_exists():
    """output/pros_cons_generated.csv must exist after generation."""
    generate_pros_and_cons()
    assert os.path.exists("output/pros_cons_generated.csv")
    df = pd.read_csv("output/pros_cons_generated.csv")
    assert len(df) > 0


def test_tearsheet_files_exist():
    """92 PDF tearsheets must exist in reports/tearsheets/ each >= 30 KB."""
    tearsheet_dir = "reports/tearsheets"
    if not os.path.exists(tearsheet_dir):
        pytest.skip("Tearsheets not yet generated")
    pdfs = [f for f in os.listdir(tearsheet_dir) if f.endswith("_tearsheet.pdf")]
    assert len(pdfs) == 92, f"Expected 92 tearsheets, found {len(pdfs)}"
    for pdf in pdfs:
        path = os.path.join(tearsheet_dir, pdf)
        size_kb = os.path.getsize(path) // 1024
        assert size_kb >= 5, f"{pdf} is too small: {size_kb} KB"


def test_cashflow_intelligence_output():
    """output/cashflow_intelligence.xlsx must exist with 91+ rows and required columns."""
    assert os.path.exists("output/cashflow_intelligence.xlsx"), "cashflow_intelligence.xlsx not found"
    df = pd.read_excel("output/cashflow_intelligence.xlsx")
    assert len(df) >= 91, f"Expected 91+ rows, got {len(df)}"
    required_cols = ["company_id", "sector", "cfo_quality_label", "capex_label",
                     "distress_flag", "deleveraging_flag", "capital_allocation_label"]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
