import sqlite3
import pandas as pd
import os

def export_all_tables():
    db_path = 'data/nifty100.db'
    output_dir = 'output/csv_tables'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    # Get all tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=== Exporting SQLite tables to CSV ===")
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        csv_path = os.path.join(output_dir, f"{table}.csv")
        df.to_csv(csv_path, index=False)
        print(f" - Exported table '{table}' ({len(df)} rows) to: {csv_path}")
        
    conn.close()
    print("\nAll tables exported successfully! You can open these CSV files directly in Excel or your IDE.")

if __name__ == "__main__":
    export_all_tables()
