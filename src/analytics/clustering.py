import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")

FLAG_PROXIES = {
    "TURNAROUND": 15.0,
    "DECLINE_TO_LOSS": -15.0,
    "BOTH_NEGATIVE": -10.0,
    "ZERO_BASE": 0.0,
    "INSUFFICIENT": None
}

def compute_fcf_cagr_5yr(df_comp_ratios: pd.DataFrame) -> float | None:
    """Computes 5-year FCF CAGR for a company given its sorted financial_ratios history."""
    df_sorted = df_comp_ratios.sort_values("year")
    if len(df_sorted) < 5:
        return None
    fcf_latest = df_sorted.iloc[-1].get("free_cash_flow_cr")
    fcf_start = df_sorted.iloc[-5].get("free_cash_flow_cr")
    
    if pd.isna(fcf_latest) or pd.isna(fcf_start) or fcf_start == 0:
        return None
    if fcf_start > 0 and fcf_latest > 0:
        try:
            return float(((fcf_latest / fcf_start) ** (1.0 / 5.0) - 1.0) * 100.0)
        except Exception:
            return None
    elif fcf_start > 0 and fcf_latest <= 0:
        return -15.0
    elif fcf_start < 0 and fcf_latest >= 0:
        return 15.0
    else:
        return -10.0

def load_clustering_dataset():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_comp = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
        df_sec = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        df_rat = pd.read_sql("SELECT * FROM financial_ratios", conn)
    finally:
        conn.close()

    features_list = []
    
    for _, c_row in df_comp.iterrows():
        comp_id = c_row["company_id"]
        c_sec = df_sec[df_sec["company_id"] == comp_id]
        sector = c_sec.iloc[0]["broad_sector"] if not c_sec.empty else "General"
        
        comp_rat = df_rat[df_rat["company_id"] == comp_id].sort_values("year")
        if comp_rat.empty:
            continue
        
        latest_rat = comp_rat.iloc[-1]
        
        roe = latest_rat.get("return_on_equity_pct")
        de = latest_rat.get("debt_to_equity")
        opm = latest_rat.get("operating_profit_margin_pct")
        
        rev_cagr = latest_rat.get("revenue_cagr_5yr")
        rev_flag = latest_rat.get("revenue_cagr_5yr_flag")
        if pd.isna(rev_cagr) and rev_flag in FLAG_PROXIES:
            rev_cagr = FLAG_PROXIES[rev_flag]
            
        fcf_cagr = compute_fcf_cagr_5yr(comp_rat)
        
        features_list.append({
            "company_id": comp_id,
            "broad_sector": sector,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "revenue_cagr_5yr": rev_cagr,
            "fcf_cagr_5yr": fcf_cagr,
            "operating_profit_margin_pct": opm
        })
        
    df_dataset = pd.DataFrame(features_list)
    return df_dataset

def run_clustering_pipeline():
    os.makedirs("reports", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    df_raw = load_clustering_dataset()
    feature_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct"
    ]
    
    # 1. Impute missing values with sector median
    df_imputed = df_raw.copy()
    for col in feature_cols:
        sector_medians = df_imputed.groupby("broad_sector")[col].transform("median")
        universe_median = df_imputed[col].median()
        if pd.isna(universe_median):
            universe_median = 0.0
        df_imputed[col] = df_imputed[col].fillna(sector_medians).fillna(universe_median)
        
    # 2. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_imputed[feature_cols])
    
    # 3. Elbow Plot (k from 2 to 10)
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), inertias, marker='o', color='#1f77b4', linewidth=2)
    plt.title("KMeans Elbow Method (Inertia vs k)")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.axvline(x=5, color='red', linestyle='--', label='k=5 Selected')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("reports/elbow_plot.png", dpi=300)
    plt.close()
    
    # 4. Run KMeans with n_clusters=5
    kmeans_5 = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = kmeans_5.fit_predict(X_scaled)
    centroids = kmeans_5.cluster_centers_
    
    df_imputed["cluster_id"] = cluster_ids
    
    # Calculate distance from centroid
    distances = []
    for idx, c_id in enumerate(cluster_ids):
        dist = np.linalg.norm(X_scaled[idx] - centroids[c_id])
        distances.append(float(dist))
    df_imputed["distance_from_centroid"] = distances
    
    # 5. Cluster Profiling & Naming
    profile = df_imputed.groupby("cluster_id")[feature_cols].mean()
    
    cluster_names_map = {}
    for c_id in range(5):
        row = profile.loc[c_id]
        roe_val = row["return_on_equity_pct"]
        de_val = row["debt_to_equity"]
        rev_val = row["revenue_cagr_5yr"]
        opm_val = row["operating_profit_margin_pct"]
        
        if roe_val > 18 and de_val < 1.0:
            name = "High-Quality Compounders"
        elif de_val > 1.5 or (rev_val < 0 and roe_val < 10):
            name = "Distressed or Turnaround"
        elif opm_val > 25 or (de_val < 0.5 and rev_val < 10):
            name = "Defensive Dividend Payers"
        elif rev_val > 12:
            name = "Emerging Growth"
        else:
            name = "Value Cyclicals"
        cluster_names_map[c_id] = name
        
    df_imputed["cluster_name"] = df_imputed["cluster_id"].map(cluster_names_map)
    
    # Save output/cluster_labels.csv
    df_out = df_imputed[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]]
    df_out.to_csv("output/cluster_labels.csv", index=False)
    
    # 6. Correlation Heatmap of 10 KPIs
    conn = sqlite3.connect(DB_PATH)
    try:
        df_all_rat = pd.read_sql("SELECT * FROM financial_ratios", conn)
    finally:
        conn.close()
        
    latest_ratios = df_all_rat.sort_values("year").groupby("company_id").last().reset_index()
    
    kpi_cols = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "earnings_per_share",
        "book_value_per_share",
        "revenue_cagr_5yr",
        "free_cash_flow_cr"
    ]

    corr_data = latest_ratios[kpi_cols].apply(pd.to_numeric, errors='coerce')
    corr_matrix = corr_data.corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True, linewidths=0.5)
    plt.title("Pearson Correlation Heatmap of 10 Core KPIs")
    plt.tight_layout()
    plt.savefig("reports/correlation_heatmap.png", dpi=300)
    plt.close()
    
    # 7. Outlier Detection per Broad Sector (Z-Score > 3)
    outliers = []
    df_sector_merged = latest_ratios.merge(df_raw[["company_id", "broad_sector"]], on="company_id", how="left")
    
    for metric in kpi_cols:
        for sector, grp in df_sector_merged.groupby("broad_sector"):
            vals = grp[metric].dropna()
            if len(vals) < 3:
                continue
            mean = vals.mean()
            std = vals.std()
            if std == 0 or pd.isna(std):
                continue
            for _, row in grp.iterrows():
                val = row[metric]
                if pd.notna(val):
                    z = (val - mean) / std
                    if abs(z) > 3.0:
                        outliers.append({
                            "company_id": row["company_id"],
                            "broad_sector": sector,
                            "metric": metric,
                            "value": val,
                            "sector_mean": mean,
                            "sector_std": std,
                            "z_score": z
                        })
                        
    df_outliers = pd.DataFrame(outliers)
    df_outliers.to_csv("output/outlier_report.csv", index=False)
    
    # 8. Portfolio Statistics (P10 to P90, Mean, Std)
    stats_records = []
    for metric in kpi_cols:
        series = corr_data[metric].dropna()
        if not series.empty:
            stats_records.append({
                "metric": metric,
                "P10": series.quantile(0.10),
                "P25": series.quantile(0.25),
                "P50": series.quantile(0.50),
                "P75": series.quantile(0.75),
                "P90": series.quantile(0.90),
                "Mean": series.mean(),
                "Std": series.std()
            })
    df_stats = pd.DataFrame(stats_records)
    df_stats.to_csv("output/portfolio_stats.csv", index=False)
    
    print(f"Clustering complete. {len(df_out)} companies categorized into 5 clusters.")
    print("Files created:")
    print(" - reports/elbow_plot.png")
    print(" - output/cluster_labels.csv")
    print(" - reports/correlation_heatmap.png")
    print(" - output/outlier_report.csv")
    print(" - output/portfolio_stats.csv")

if __name__ == "__main__":
    run_clustering_pipeline()
