"""
StockSense AI — Phase 17 Historical Data Quality Auditor
Validates downloaded market datasets for OHLC integrity, zero/negative volumes,
NaNs, Infinities, timestamp ordering, and price anomalies without deleting legitimate moves.
Generates backend/research/phase17/data_quality_report.json.
"""

import os
import glob
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

DATASET_BASE_DIR = os.path.join("backend", "research", "phase17", "data")
REPORT_PATH = os.path.join("backend", "research", "phase17", "data_quality_report.json")


def audit_symbol_data_quality(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """
    Performs comprehensive data quality audit on a single symbol DataFrame.
    """
    if df is None or df.empty:
        return {
            "symbol": symbol,
            "status": "EMPTY",
            "total_rows": 0,
            "duplicate_dates": 0,
            "missing_values": 0,
            "invalid_ohlc": 0,
            "negative_volume": 0,
            "zero_volume": 0,
            "extreme_returns": 0,
            "insufficient_history": True
        }

    total_rows = len(df)
    
    # 1. Duplicate & Missing Dates
    dup_dates = df.duplicated(subset=["date"]).sum()
    
    # 2. Missing & Infinite values
    missing_vals = df[["open", "high", "low", "close", "volume"]].isna().sum().sum()
    inf_vals = np.isinf(df[["open", "high", "low", "close", "volume"]].select_dtypes(include=[np.number])).sum().sum()
    
    # 3. Invalid OHLC Logic (high < low, high < open, high < close, low > open, low > close)
    invalid_ohlc = (
        (df["high"] < df["low"]) |
        (df["high"] < df["open"]) |
        (df["high"] < df["close"]) |
        (df["low"] > df["open"]) |
        (df["low"] > df["close"]) |
        (df["open"] <= 0) |
        (df["close"] <= 0)
    ).sum()

    # 4. Volume Checks
    neg_volume = (df["volume"] < 0).sum()
    zero_volume = (df["volume"] == 0).sum()

    # 5. Extreme Price Moves (>20% or <-20% daily return flag)
    returns = df["close"].pct_change().abs()
    extreme_returns = (returns > 0.20).sum()

    # 6. Timestamp Ordering
    df_sorted = df.sort_values("date")
    is_ordered = (df["date"].values == df_sorted["date"].values).all()

    insufficient_history = total_rows < 30

    return {
        "symbol": symbol,
        "status": "VALID" if (invalid_ohlc == 0 and missing_vals == 0 and not insufficient_history) else "WARNINGS",
        "total_rows": total_rows,
        "duplicate_dates": int(dup_dates),
        "missing_values": int(missing_vals + inf_vals),
        "invalid_ohlc": int(invalid_ohlc),
        "negative_volume": int(neg_volume),
        "zero_volume": int(zero_volume),
        "extreme_returns": int(extreme_returns),
        "timestamp_ordered": bool(is_ordered),
        "insufficient_history": bool(insufficient_history)
    }


def run_data_quality_audit() -> Dict[str, Any]:
    """
    Scans all downloaded Parquet files under backend/research/phase17/data/
    and produces data_quality_report.json.
    """
    parquet_files = glob.glob(os.path.join(DATASET_BASE_DIR, "**", "*.parquet"), recursive=True)
    
    total_symbols = len(parquet_files)
    successful_symbols = 0
    failed_symbols = 0
    total_rows = 0
    duplicate_rows = 0
    missing_values = 0
    invalid_ohlc_rows = 0
    anomaly_rows = 0
    symbols_insufficient = []

    symbol_audits = []

    print(f"Running Data Quality Audit across {total_symbols} Parquet datasets...")

    for filepath in parquet_files:
        sym = os.path.basename(filepath).replace(".parquet", "")
        try:
            df = pd.read_parquet(filepath)
            audit = audit_symbol_data_quality(df, sym)
            symbol_audits.append(audit)

            total_rows += audit["total_rows"]
            duplicate_rows += audit["duplicate_dates"]
            missing_values += audit["missing_values"]
            invalid_ohlc_rows += audit["invalid_ohlc"]
            anomaly_rows += audit["extreme_returns"]

            if audit["insufficient_history"]:
                symbols_insufficient.append(sym)

            if audit["status"] in ["VALID", "WARNINGS"]:
                successful_symbols += 1
            else:
                failed_symbols += 1
        except Exception as e:
            logger.error(f"Failed to audit {filepath}: {e}")
            failed_symbols += 1

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_symbols": total_symbols,
        "successful_symbols": successful_symbols,
        "failed_symbols": failed_symbols,
        "total_rows": total_rows,
        "duplicate_rows": duplicate_rows,
        "missing_values": missing_values,
        "invalid_ohlc_rows": invalid_ohlc_rows,
        "anomaly_rows": anomaly_rows,
        "symbols_with_insufficient_history": symbols_insufficient,
        "per_symbol_details": symbol_audits
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Data Quality Report Saved to {REPORT_PATH}")
    print(f"Summary: Symbols={total_symbols}, Rows={total_rows}, Invalid OHLC={invalid_ohlc_rows}, Anomalies={anomaly_rows}")
    return report


if __name__ == "__main__":
    run_data_quality_audit()
