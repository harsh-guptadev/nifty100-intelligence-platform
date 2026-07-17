import re

MONTH_MAP = {
    'jan': '01', 'january': '01',
    'feb': '02', 'february': '02',
    'mar': '03', 'march': '03',
    'apr': '04', 'april': '04',
    'may': '05',
    'jun': '06', 'june': '06',
    'jul': '07', 'july': '07',
    'aug': '08', 'august': '08',
    'sep': '09', 'september': '09',
    'oct': '10', 'october': '10',
    'nov': '11', 'november': '11',
    'dec': '12', 'december': '12'
}

def normalize_year(year_val) -> str:
    """
    Standardise year labels into 'YYYY-MM' format.
    Handles formats like: Mar-23, Mar 23, March-2023, 2023, FY23, Dec-22, Jun-23, etc.
    Returns 'PARSE_ERROR' for invalid formats.
    """
    if year_val is None:
        return "PARSE_ERROR"
    
    # Convert to string and clean whitespace
    s = str(year_val).strip()
    if not s:
        return "PARSE_ERROR"
    
    # 1. Already normalised: YYYY-MM
    if re.match(r'^\d{4}-\d{2}$', s):
        return s
    
    # 2. Plain 4-digit year integer/string: e.g. 2023 -> assume March FY close (2023-03)
    if re.match(r'^\d{4}$', s):
        return f"{s}-03"
    
    # 3. FY prefix: e.g. FY23, FY 23, FY2023 -> assume March close
    fy_match = re.match(r'^(?:FY|fy)\s*(\d{2}|\d{4})$', s)
    if fy_match:
        yr = fy_match.group(1)
        if len(yr) == 2:
            yr = f"20{yr}"
        return f"{yr}-03"
    
    # 4. Month-Year formats: Mar-23, Mar 23, March-2023, Dec-22, etc.
    # Pattern looks for a month name word and a 2 or 4 digit year
    month_pattern = r'([a-zA-Z]+)'
    year_pattern = r'(\d{4}|\d{2})'
    
    # Search for month and year components
    month_match = re.search(month_pattern, s)
    year_match = re.search(year_pattern, s)
    
    if month_match and year_match:
        month_str = month_match.group(1).lower()
        year_str = year_match.group(1)
        
        if month_str in MONTH_MAP:
            mm = MONTH_MAP[month_str]
            # Convert 2-digit year to 4-digit
            if len(year_str) == 2:
                year_int = int(year_str)
                # Assume 2000s for years <= 50, otherwise 1900s
                if year_int <= 50:
                    year_str = f"20{year_str}"
                else:
                    year_str = f"19{year_str}"
            return f"{year_str}-{mm}"
            
    return "PARSE_ERROR"

def normalize_ticker(ticker_val) -> str:
    """
    Standardise company_id (NSE ticker).
    Strips whitespace, converts to uppercase.
    Returns 'MISSING' if empty or None.
    """
    if ticker_val is None:
        return "MISSING"
    
    s = str(ticker_val).strip().upper()
    if not s:
        return "MISSING"
        
    return s
