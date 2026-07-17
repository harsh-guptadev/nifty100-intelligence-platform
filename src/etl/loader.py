import os
import sqlite3
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import DataValidator

# Load environment variables
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
SCHEMA_PATH = "db/schema.sql"
VALIDATION_FAILURES_PATH = "output/validation_failures.csv"
LOAD_AUDIT_PATH = "output/load_audit.csv"

def init_db():
    """Create database tables using schema.sql if not exists."""
    print(f"Initializing database at {DB_PATH}...")
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
    finally:
        conn.close()
    print("Database schema applied successfully.")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_table_columns(conn, table_name: str) -> list:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    return [row[1] for row in cursor.fetchall()]

def load_table(table_name: str, file_path: str, is_core: bool, header: int, validator: DataValidator, valid_companies: set) -> dict:
    """
    Loads, normalises, validates, and inserts data for a single table.
    Returns audit statistics dict.
    """
    start_time = time.time()
    print(f"Loading {table_name} from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found. Skipping {table_name} load.")
        return {
            "table_name": table_name,
            "rows_in": 0,
            "rows_out": 0,
            "rejected": 0,
            "timestamp": datetime.now().isoformat(),
            "runtime_s": 0.0
        }
        
    # Read Excel file
    # Handles merged cells and header offsets
    df_raw = pd.read_excel(file_path, header=header)
    rows_in = len(df_raw)
    
    # Strip whitespace from column headers
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    cleaned_df = df_raw.copy()
    
    # Run Table-Specific normalizations
    if table_name == "companies":
        cleaned_df['id'] = cleaned_df['id'].apply(normalize_ticker)
        # Handle embedded newlines in company names
        if 'company_name' in cleaned_df.columns:
            cleaned_df['company_name'] = cleaned_df['company_name'].apply(lambda x: str(x).replace('\n', ' ').strip())
            
        # Run companies validation
        is_valid = validator.validate_companies(cleaned_df)
        if not is_valid:
            raise ValueError("Critical validation failed on companies master table. Halting load.")
            
        rows_out = len(cleaned_df)
        rejected = rows_in - rows_out
        
        # Save to DB
        conn = get_db_connection()
        try:
            cols = get_table_columns(conn, "companies")
            insert_df = cleaned_df[[c for c in cleaned_df.columns if c in cols]].copy()
            insert_df.to_sql("companies", conn, if_exists="append", index=False)
        finally:
            conn.close()
            
        # Update valid companies set
        valid_companies.update(cleaned_df['id'].unique())
        

                
    else:
        # Time-series tables and supplementary tables
        # Standardise company_id
        if 'company_id' in cleaned_df.columns:
            cleaned_df['company_id'] = cleaned_df['company_id'].apply(normalize_ticker)
            
        # Standardise year / date
        if 'year' in cleaned_df.columns:
            cleaned_df['year'] = cleaned_df['year'].apply(normalize_year)
        elif 'Year' in cleaned_df.columns: # Documents uses Year with capital 'Y'
            # Convert Year to string first to normalize, then YYYY-MM
            cleaned_df['Year'] = cleaned_df['Year'].apply(lambda x: int(float(x)) if pd.notna(x) and str(x).replace('.','').isdigit() else 0)
            
        # Validate time series row by row
        cleaned_df, is_valid = validator.validate_time_series(cleaned_df, table_name, valid_companies)
        if not is_valid:
            raise ValueError(f"Critical validation failed on {table_name}. Halting load.")
            
        rows_out = len(cleaned_df)
        rejected = rows_in - rows_out
        
        # Save to DB
        conn = get_db_connection()
        try:
            if not cleaned_df.empty:
                cols = get_table_columns(conn, table_name)
                insert_df = cleaned_df[[c for c in cleaned_df.columns if c in cols]].copy()
                insert_df.to_sql(table_name, conn, if_exists="append", index=False)
        finally:
            conn.close()
                
    runtime = time.time() - start_time
    return {
        "table_name": table_name,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "rejected": rejected,
        "timestamp": datetime.now().isoformat(),
        "runtime_s": round(runtime, 4)
    }

def run_etl():
    """Main ETL orchestration script."""
    # Ensure folders exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Initialize DB
    init_db()
    
    # Instantiate validator
    validator = DataValidator()
    valid_companies = set()
    
    # Define files load order and parameters
    load_jobs = [
        # 1. Companies Master Reference
        {"table": "companies", "path": "data/raw/companies.xlsx", "core": True, "header": 1},
        
        # 2. Supplementary Sector mapping
        {"table": "sectors", "path": "data/supporting/sectors.xlsx", "core": False, "header": 0},
        
        # 3. Core time-series statements
        {"table": "profitandloss", "path": "data/raw/profitandloss.xlsx", "core": True, "header": 1},
        {"table": "balancesheet", "path": "data/raw/balancesheet.xlsx", "core": True, "header": 1},
        {"table": "cashflow", "path": "data/raw/cashflow.xlsx", "core": True, "header": 1},
        
        # 4. Other core tables
        {"table": "analysis", "path": "data/raw/analysis.xlsx", "core": True, "header": 1},
        {"table": "documents", "path": "data/raw/documents.xlsx", "core": True, "header": 1},
        {"table": "prosandcons", "path": "data/raw/prosandcons.xlsx", "core": True, "header": 1},
        
        # 5. Other supplementary tables
        {"table": "stock_prices", "path": "data/supporting/stock_prices.xlsx", "core": False, "header": 0},
        {"table": "market_cap", "path": "data/supporting/market_cap.xlsx", "core": False, "header": 0},
        {"table": "peer_groups", "path": "data/supporting/peer_groups.xlsx", "core": False, "header": 0}
    ]
    
    audit_results = []
    time_series_dfs = {}
    
    for job in load_jobs:
        try:
            stats = load_table(
                table_name=job["table"],
                file_path=job["path"],
                is_core=job["core"],
                header=job["header"],
                validator=validator,
                valid_companies=valid_companies
            )
            audit_results.append(stats)
            
            # Store time-series dfs to check coverage at the end
            if job["table"] in ["profitandloss", "balancesheet", "cashflow"]:
                # Re-load from SQLite to verify DB state
                conn = get_db_connection()
                try:
                    time_series_dfs[job["table"]] = pd.read_sql(f"SELECT * FROM {job['table']}", conn)
                finally:
                    conn.close()
                    
        except Exception as e:
            print(f"Critical error loading {job['table']}: {e}")
            # Save any failures before crashing
            validator.save_failures(VALIDATION_FAILURES_PATH)
            raise e
            
    # Run DQ-16 coverage check on loaded datasets
    validator.validate_coverage(time_series_dfs)
    
    # Save validation failures log
    validator.save_failures(VALIDATION_FAILURES_PATH)
    
    # Save load audit log
    pd.DataFrame(audit_results).to_csv(LOAD_AUDIT_PATH, index=False)
    
    print("\nETL run completed successfully.")
    print(f"Validation failures logged to: {VALIDATION_FAILURES_PATH}")
    print(f"Load audit statistics logged to: {LOAD_AUDIT_PATH}")
    
    # Print summary
    print("\nLoad Summary:")
    for res in audit_results:
        print(f" - {res['table_name']}: In={res['rows_in']}, Out={res['rows_out']}, Rejected={res['rejected']} (time: {res['runtime_s']}s)")

if __name__ == "__main__":
    run_etl()
