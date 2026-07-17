import re
import pandas as pd
import requests

class DataValidator:
    def __init__(self):
        self.failures = []

    def log_failure(self, company_id: str, year: str, field: str, rule_id: str, issue: str, severity: str):
        self.failures.append({
            "company_id": company_id,
            "year": year,
            "field": field,
            "rule_id": rule_id,
            "issue": issue,
            "severity": severity
        })

    def get_failures_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.failures)

    def save_failures(self, filepath: str):
        df = self.get_failures_df()
        if not df.empty:
            df.to_csv(filepath, index=False)
        else:
            # Create empty CSV with columns
            pd.DataFrame(columns=["company_id", "year", "field", "rule_id", "issue", "severity"]).to_csv(filepath, index=False)

    def validate_companies(self, df: pd.DataFrame) -> bool:
        """
        Validate the companies master table.
        DQ-01: Company PK Uniqueness (Critical)
        DQ-08: Ticker Format (Critical)
        Returns True if validation passes (no CRITICAL errors that require halting).
        """
        is_valid = True
        
        # Check DQ-01: Company PK uniqueness
        if df['id'].duplicated().any():
            duplicates = df[df['id'].duplicated()]['id'].unique()
            for dup in duplicates:
                self.log_failure(
                    company_id=dup,
                    year="N/A",
                    field="id",
                    rule_id="DQ-01",
                    issue="Duplicate company ticker (PK Uniqueness violation)",
                    severity="CRITICAL"
                )
            is_valid = False
            
        # Check DQ-08: Ticker format length 2-12
        for idx, row in df.iterrows():
            ticker = row['id']
            if len(ticker) < 2 or len(ticker) > 12:
                self.log_failure(
                    company_id=ticker,
                    year="N/A",
                    field="id",
                    rule_id="DQ-08",
                    issue=f"Ticker length {len(ticker)} out of range (2-12 characters)",
                    severity="CRITICAL"
                )
                is_valid = False
                
        return is_valid

    def validate_time_series(self, df: pd.DataFrame, table_name: str, valid_companies: set) -> tuple[pd.DataFrame, bool]:
        """
        Validate and clean a statement table (profitandloss, balancesheet, cashflow, etc.).
        Handles:
        DQ-02: Annual/PK Uniqueness (Critical) -> Deduplicates
        DQ-03: FK Integrity (Critical) -> Rejects orphan rows
        DQ-07: Year/Date Format (Critical) -> Rejects row
        DQ-08: Ticker Format (Critical) -> Rejects row if out of range
        
        Table-specific WARNING rules are run and logged, but rows are not rejected.
        
        Returns (cleaned_df, is_valid) where cleaned_df has invalid rows removed and is_valid is True.
        """
        is_valid = True
        rows_to_keep = []
        
        # Detect present columns
        has_company_id = 'company_id' in df.columns
        has_year = 'year' in df.columns
        has_Year = 'Year' in df.columns
        has_date = 'date' in df.columns
        
        # We process row by row to filter out CRITICAL failures
        for idx, row in df.iterrows():
            company_id = str(row.get('company_id', '')).strip().upper() if has_company_id else ""
            year_val = row.get('year') if has_year else (row.get('Year') if has_Year else None)
            year = str(year_val).strip() if year_val is not None else ""
            date_val = row.get('date') if has_date else None
            date = str(date_val).strip() if date_val is not None else ""
            
            # DQ-08: Ticker Format (only check if table has company_id)
            if has_company_id:
                if len(company_id) < 2 or len(company_id) > 12:
                    self.log_failure(
                        company_id=company_id,
                        year=year or date or "N/A",
                        field="company_id",
                        rule_id="DQ-08",
                        issue=f"Ticker length {len(company_id)} out of range (2-12 characters)",
                        severity="CRITICAL"
                    )
                    continue
                
            # DQ-07: Year Format YYYY-MM
            if has_year:
                if year == "PARSE_ERROR" or not re.match(r'^\d{4}-\d{2}$', year):
                    self.log_failure(
                        company_id=company_id,
                        year=year,
                        field="year",
                        rule_id="DQ-07",
                        issue=f"Unparseable or invalid year format: {row.get('year')}",
                        severity="CRITICAL"
                    )
                    continue
            elif has_Year:
                # Documents table uses Year (integer). Check if it's a valid year
                try:
                    year_int = int(float(year_val)) if pd.notna(year_val) else 0
                    if not (1900 <= year_int <= 2100):
                        raise ValueError()
                except (ValueError, TypeError):
                    self.log_failure(
                        company_id=company_id,
                        year=str(year_val),
                        field="Year",
                        rule_id="DQ-07",
                        issue=f"Invalid Year integer: {year_val}",
                        severity="CRITICAL"
                    )
                    continue
                    
            # Check Date Format
            if has_date:
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                    self.log_failure(
                        company_id=company_id,
                        year=date,
                        field="date",
                        rule_id="DQ-07",
                        issue=f"Invalid date format YYYY-MM-DD: {row.get('date')}",
                        severity="CRITICAL"
                    )
                    continue
                
            # DQ-03: FK Integrity
            if has_company_id:
                if company_id not in valid_companies:
                    self.log_failure(
                        company_id=company_id,
                        year=year or date or "N/A",
                        field="company_id",
                        rule_id="DQ-03",
                        issue=f"Ticker {company_id} does not exist in master companies list",
                        severity="CRITICAL"
                    )
                    continue
                
            rows_to_keep.append(idx)
            
        # Filter DataFrame to valid rows
        cleaned_df = df.loc[rows_to_keep].copy()
        
        # DQ-02: Annual/PK Uniqueness
        if has_company_id:
            pk_cols = []
            if has_year:
                pk_cols = ['company_id', 'year']
            elif has_Year:
                pk_cols = ['company_id', 'Year']
            elif has_date:
                pk_cols = ['company_id', 'date']
            else:
                pk_cols = ['company_id'] # e.g. sectors, analysis (one row per company)
                
            dups = cleaned_df.duplicated(subset=pk_cols, keep=False)
            if dups.any():
                dup_rows = cleaned_df[dups]
                for _, row in dup_rows.iterrows():
                    self.log_failure(
                        company_id=row.get('company_id') if has_company_id else "",
                        year=str(row.get('year', row.get('Year', row.get('date', 'N/A')))),
                        field=",".join(pk_cols),
                        rule_id="DQ-02",
                        issue=f"Duplicate row for composite key {pk_cols}",
                        severity="CRITICAL"
                    )
                # Deduplicate - keep last occurrence
                cleaned_df = cleaned_df.drop_duplicates(subset=pk_cols, keep='last')
                
        # Run table-specific WARNING and INFO rules
        if table_name == "profitandloss":
            self._validate_profit_and_loss(cleaned_df)
        elif table_name == "balancesheet":
            self._validate_balance_sheet(cleaned_df)
        elif table_name == "cashflow":
            self._validate_cash_flow(cleaned_df)
        elif table_name == "documents":
            self._validate_documents(cleaned_df)
            
        return cleaned_df, is_valid

    def _validate_profit_and_loss(self, df: pd.DataFrame):
        for idx, row in df.iterrows():
            company_id = row['company_id']
            year = row['year']
            
            sales = float(row.get('sales', 0) or 0)
            operating_profit = float(row.get('operating_profit', 0) or 0)
            opm_percentage = float(row.get('opm_percentage', 0) or 0)
            tax_percentage = float(row.get('tax_percentage', 0) or 0)
            dividend_payout = float(row.get('dividend_payout', 0) or 0)
            eps = float(row.get('eps', 0) or 0)
            net_profit = float(row.get('net_profit', 0) or 0)
            
            # DQ-05: OPM Cross-Check
            if sales > 0:
                computed_opm = (operating_profit / sales) * 100
                if abs(opm_percentage - computed_opm) >= 1.0:
                    self.log_failure(
                        company_id=company_id,
                        year=year,
                        field="opm_percentage",
                        rule_id="DQ-05",
                        issue=f"OPM mismatch: reported {opm_percentage}%, computed {computed_opm:.2f}%",
                        severity="WARNING"
                    )
            
            # DQ-06: Positive Sales
            if sales <= 0:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="sales",
                    rule_id="DQ-06",
                    issue=f"Sales is non-positive: {sales}",
                    severity="WARNING"
                )
                
            # DQ-11: Tax Rate Range
            if not (0 <= tax_percentage <= 60):
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="tax_percentage",
                    rule_id="DQ-11",
                    issue=f"Tax rate {tax_percentage}% out of expected range (0-60%)",
                    severity="WARNING"
                )
                
            # DQ-12: Dividend Payout Cap
            if dividend_payout > 200:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="dividend_payout",
                    rule_id="DQ-12",
                    issue=f"Dividend payout {dividend_payout}% exceeds 200%",
                    severity="WARNING"
                )
                
            # DQ-14: EPS Sign Consistency
            if net_profit > 0 and eps <= 0:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="eps",
                    rule_id="DQ-14",
                    issue=f"EPS is non-positive ({eps}) while Net Profit is positive ({net_profit})",
                    severity="WARNING"
                )

    def _validate_balance_sheet(self, df: pd.DataFrame):
        for idx, row in df.iterrows():
            company_id = row['company_id']
            year = row['year']
            
            total_assets = float(row.get('total_assets', 0) or 0)
            equity_capital = float(row.get('equity_capital', 0) or 0)
            reserves = float(row.get('reserves', 0) or 0)
            borrowings = float(row.get('borrowings', 0) or 0)
            other_liabilities = float(row.get('other_liabilities', 0) or 0)
            fixed_assets = float(row.get('fixed_assets', 0) or 0)
            
            total_liabilities = equity_capital + reserves + borrowings + other_liabilities
            
            # DQ-04: Balance Sheet Balance (< 1% variance)
            if total_assets > 0:
                variance = abs(total_assets - total_liabilities) / total_assets
                if variance >= 0.01:
                    self.log_failure(
                        company_id=company_id,
                        year=year,
                        field="total_assets",
                        rule_id="DQ-04",
                        issue=f"Balance sheet out of balance. Assets: {total_assets}, Liab/Equity: {total_liabilities} (variance {variance*100:.2f}%)",
                        severity="WARNING"
                    )
                elif total_assets != total_liabilities:
                    # DQ-15: BSE/ASE Balance (strict)
                    self.log_failure(
                        company_id=company_id,
                        year=year,
                        field="total_assets",
                        rule_id="DQ-15",
                        issue=f"Strict balance mismatch. Assets: {total_assets}, Liab/Equity: {total_liabilities}",
                        severity="INFO"
                    )
            
            # DQ-10: Non-Negative Fixed Assets
            if fixed_assets < 0:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="fixed_assets",
                    rule_id="DQ-10",
                    issue=f"Negative fixed assets: {fixed_assets}. Coercing to 0.",
                    severity="WARNING"
                )
                df.at[idx, 'fixed_assets'] = 0.0

    def _validate_cash_flow(self, df: pd.DataFrame):
        for idx, row in df.iterrows():
            company_id = row['company_id']
            year = row['year']
            
            net_cash_flow = float(row.get('net_cash_flow', 0) or 0)
            cfo = float(row.get('operating_activity', 0) or 0)
            cfi = float(row.get('investing_activity', 0) or 0)
            cff = float(row.get('financing_activity', 0) or 0)
            
            sum_cf = cfo + cfi + cff
            
            # DQ-09: Net Cash Check (10 Cr tolerance)
            if abs(net_cash_flow - sum_cf) > 10.0:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="net_cash_flow",
                    rule_id="DQ-09",
                    issue=f"Net cash flow mismatch: reported {net_cash_flow}, sum of parts {sum_cf} (diff {abs(net_cash_flow-sum_cf):.2f})",
                    severity="WARNING"
                )
                # Coerce to sum of parts
                df.at[idx, 'net_cash_flow'] = sum_cf

    def _validate_documents(self, df: pd.DataFrame):
        for idx, row in df.iterrows():
            company_id = row['company_id']
            year = str(row.get('Year', 'N/A'))
            url = str(row.get('Annual_Report', ''))
            
            if not url or url.lower() == 'nan':
                continue
                
            # DQ-13: URL Validity (validate with requests.head)
            try:
                # Use a small timeout to not hang the load
                resp = requests.head(url, timeout=2.0, allow_redirects=True)
                if resp.status_code != 200:
                    self.log_failure(
                        company_id=company_id,
                        year=year,
                        field="Annual_Report",
                        rule_id="DQ-13",
                        issue=f"Annual Report URL returned status code {resp.status_code}: {url}",
                        severity="WARNING"
                    )
            except Exception as e:
                self.log_failure(
                    company_id=company_id,
                    year=year,
                    field="Annual_Report",
                    rule_id="DQ-13",
                    issue=f"Failed to connect to Annual Report URL ({type(e).__name__}): {url}",
                    severity="WARNING"
                )

    def validate_coverage(self, time_series_dfs: dict[str, pd.DataFrame]):
        """
        DQ-16: Coverage Check.
        Verify that each company has at least 5 years of P&L, BS, and CF records.
        """
        all_companies = set()
        for df in time_series_dfs.values():
            if 'company_id' in df.columns:
                all_companies.update(df['company_id'].unique())
                
        for company in all_companies:
            counts = {}
            for name, df in time_series_dfs.items():
                if 'company_id' in df.columns:
                    counts[name] = len(df[df['company_id'] == company])
                else:
                    counts[name] = 0
            
            min_years = min(counts.values()) if counts else 0
            if min_years < 5:
                years_summary = ", ".join([f"{k}: {v} yrs" for k, v in counts.items()])
                self.log_failure(
                    company_id=company,
                    year="N/A",
                    field="coverage",
                    rule_id="DQ-16",
                    issue=f"Data coverage is insufficient (<5 years): {years_summary}",
                    severity="WARNING"
                )
