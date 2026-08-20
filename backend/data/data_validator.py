import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from typing import Dict, Any, List

def validate_market_data(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """
    Validates market data DataFrame.
    Strictly distinguishes expected non-trading days (weekends & holidays) from actual data quality issues.
    
    Checks:
    - Missing OHLCV values
    - Duplicate dates
    - Non-positive prices (Open, High, Low, Close <= 0)
    - Low <= High, Low <= Open, Low <= Close checks
    - Zero volume rows
    - Suspicious calendar date gaps (> 4 calendar days gap or unexpected mid-week missing days)
    """
    report = {
        "symbol": symbol,
        "total_rows": len(df),
        "earliest_date": None,
        "latest_date": None,
        "missing_values_count": 0,
        "duplicate_dates_count": 0,
        "invalid_price_rows_count": 0,
        "zero_volume_rows_count": 0,
        "suspicious_gaps": [],
        "is_valid": True,
        "issues": []
    }

    if df is None or df.empty:
        report["is_valid"] = False
        report["issues"].append("DataFrame is empty or None.")
        return report

    # Standardize column names
    required_cols = ["date", "open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df.columns:
            report["is_valid"] = False
            report["issues"].append(f"Missing required column: {col}")
            return report

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    df_copy = df_copy.sort_values('date').reset_index(drop=True)

    report["earliest_date"] = df_copy['date'].min().strftime('%Y-%m-%d')
    report["latest_date"] = df_copy['date'].max().strftime('%Y-%m-%d')

    # Missing values
    missing_count = int(df_copy[required_cols].isnull().sum().sum())
    report["missing_values_count"] = missing_count
    if missing_count > 0:
        report["issues"].append(f"Found {missing_count} missing cell values in OHLCV columns.")

    # Duplicate dates
    dups = int(df_copy.duplicated(subset=['date']).sum())
    report["duplicate_dates_count"] = dups
    if dups > 0:
        report["issues"].append(f"Found {dups} duplicate trading dates.")

    # Non-positive prices or invalid high/low logic
    invalid_prices = df_copy[
        (df_copy['open'] <= 0) | 
        (df_copy['high'] <= 0) | 
        (df_copy['low'] <= 0) | 
        (df_copy['close'] <= 0) |
        (df_copy['high'] < df_copy['low']) |
        (df_copy['open'] < df_copy['low']) |
        (df_copy['close'] < df_copy['low']) |
        (df_copy['high'] < df_copy['open']) |
        (df_copy['high'] < df_copy['close'])
    ]
    report["invalid_price_rows_count"] = len(invalid_prices)
    if len(invalid_prices) > 0:
        report["issues"].append(f"Found {len(invalid_prices)} rows with non-positive prices or invalid High/Low boundaries.")

    # Zero volume
    zero_vol = df_copy[df_copy['volume'] <= 0]
    report["zero_volume_rows_count"] = len(zero_vol)
    
    from backend.assets.asset_registry import get_asset_info
    asset_info = get_asset_info(symbol)
    asset_class = asset_info["asset_class"] if asset_info else "INDIAN_EQUITY"

    if len(zero_vol) > 0:
        if asset_class in ["FOREX", "INDEX"]:
            report["issues"].append(f"Found {len(zero_vol)} rows with un-reported volume (Expected for {asset_class}).")
        else:
            report["issues"].append(f"Found {len(zero_vol)} rows with zero volume.")
            report["is_valid"] = False

    # Check for suspicious gaps
    # Normal trading week: Mon-Fri. Gap between Fri and Mon is 3 calendar days (Fri+1=Sat, Fri+2=Sun, Fri+3=Mon).
    # Normal long weekend holiday: 4 calendar days.
    # Gap > 4 calendar days or unexpected mid-week gap > 1 day without standard holiday reason is flagged.
    dates = df_copy['date'].drop_duplicates().sort_values().tolist()
    suspicious = []
    for i in range(len(dates) - 1):
        d1 = dates[i]
        d2 = dates[i + 1]
        days_gap = (d2 - d1).days
        
        # Mid-week gap check: If d1 is Mon-Thu (dayofweek 0..3) and gap > 1 day, or d1 is Fri and gap > 4 days
        weekday1 = d1.dayofweek
        if weekday1 in [0, 1, 2, 3] and days_gap > 2:  # Allow 2 days for mid-week single-day holiday
            suspicious.append({
                "from": d1.strftime('%Y-%m-%d'),
                "to": d2.strftime('%Y-%m-%d'),
                "calendar_days_gap": days_gap,
                "reason": "Unexpected mid-week multi-day trading gap"
            })
        elif weekday1 == 4 and days_gap > 4:  # Gap over weekend with 2+ holidays
            suspicious.append({
                "from": d1.strftime('%Y-%m-%d'),
                "to": d2.strftime('%Y-%m-%d'),
                "calendar_days_gap": days_gap,
                "reason": "Extended gap over weekend (>4 calendar days)"
            })
        elif days_gap > 5:
            suspicious.append({
                "from": d1.strftime('%Y-%m-%d'),
                "to": d2.strftime('%Y-%m-%d'),
                "calendar_days_gap": days_gap,
                "reason": "Large unexpected trading gap"
            })

    report["suspicious_gaps"] = suspicious
    if len(report["issues"]) > 0:
        report["is_valid"] = False

    return report
