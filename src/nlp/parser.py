import re
import os
import sqlite3
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

def parse_analysis_text():
    """
    Parses compound growth text fields using regex matching (\d+)\s*Years?:?\s*([\d.]+)%.
    Generates output/analysis_parsed.csv and output/parse_failures.csv.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        df_analysis = pd.read_sql_query("SELECT * FROM analysis", conn)
    except Exception:
        # Fallback to excel if DB table empty
        excel_path = "data/supporting/analysis.xlsx"
        if os.path.exists(excel_path):
            df_analysis = pd.read_excel(excel_path, header=1)
        else:
            df_analysis = pd.DataFrame()
    finally:
        conn.close()

    if df_analysis.empty:
        print("Analysis dataset is empty.")
        return

    pattern = re.compile(r"(TTM|Last Year|\d+\s*Years?|\d+\s*Year)\s*:?\s*([\-\d.]+)%", re.IGNORECASE)
    metrics = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]

    records = []
    failures = []

    for _, row in df_analysis.iterrows():
        company = row.get("company_id")
        if not company:
            continue

        for metric in metrics:
            val = row.get(metric)
            if pd.isna(val):
                continue
            
            text_val = str(val).strip()
            match = pattern.search(text_val)

            if match:
                period_str = match.group(1).strip().lower()
                if period_str == "ttm":
                    years = 0
                elif period_str == "last year":
                    years = 1
                else:
                    years = int(period_str.split()[0])

                records.append({
                    "company_id": company,
                    "metric_type": metric,
                    "period_years": years,
                    "value_pct": float(match.group(2))
                })
            else:
                failures.append({
                    "company_id": company,
                    "metric_type": metric,
                    "original_text": text_val
                })

    os.makedirs("output", exist_ok=True)
    
    df_parsed = pd.DataFrame(records)
    if not df_parsed.empty:
        df_parsed = df_parsed.sort_values(["company_id", "metric_type", "period_years"])
        df_parsed.to_csv("output/analysis_parsed.csv", index=False)
        print(f"Parsed {len(df_parsed)} text growth statements -> output/analysis_parsed.csv")

    df_failed = pd.DataFrame(failures)
    df_failed.to_csv("output/parse_failures.csv", index=False)
    print(f"Recorded {len(df_failed)} parse failures -> output/parse_failures.csv")

if __name__ == "__main__":
    parse_analysis_text()
