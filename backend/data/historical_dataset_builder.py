"""
StockSense AI — Phase 17 Historical Dataset Builder
Downloads multi-year historical OHLCV data across the broad stock universe.
Stores partitioned research Parquet datasets under backend/research/phase17/data/
and performs bulk SQLite database upserts safely without data fabrication.
"""

import os
import time
import json
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.data.universe import (
    get_universe, get_provider_symbol, get_internal_symbol_from_provider,
    INDIA_SYMBOLS, US_SYMBOLS, CRYPTO_SYMBOLS
)
from backend.data.data_service import save_prices_to_db, DataProviderUnavailableException
from backend.db.database import get_db_context

logger = logging.getLogger(__name__)

DATASET_BASE_DIR = os.path.join("backend", "research", "phase17", "data")


def get_symbol_region(symbol: str) -> str:
    """Categorizes symbol into region sub-folder (india, usa, crypto)."""
    sym = symbol.upper().strip()
    if sym in CRYPTO_SYMBOLS or "-USD" in sym:
        return "crypto"
    elif sym in INDIA_SYMBOLS or sym.endswith(".NS"):
        return "india"
    else:
        return "usa"


def download_symbol_history(symbol: str, period: str = "5y", retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Downloads raw OHLCV market history for a single symbol with rate-limiting and retry logic.
    Never interpolates or fabricates missing prices.
    """
    provider_sym = get_provider_symbol(symbol)
    internal_sym = get_internal_symbol_from_provider(provider_sym)

    for attempt in range(retries):
        try:
            ticker = yf.Ticker(provider_sym)
            df = ticker.history(period=period, auto_adjust=False)

            if df is None or df.empty or len(df) < 10:
                # Try fallback without auto_adjust
                df = yf.download(provider_sym, period=period, progress=False, auto_adjust=False)

            if df is None or df.empty or len(df) < 5:
                time.sleep(0.5)
                continue

            # Clean MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            df = df.reset_index()

            # Map date column
            date_col = None
            for col in ["Date", "date", "Datetime", "datetime"]:
                if col in df.columns:
                    date_col = col
                    break

            if not date_col:
                continue

            df["date"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")

            # Column mapping
            col_map = {
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Adj Close": "adjusted_close", "Volume": "volume"
            }
            df = df.rename(columns={col: col_map[col] for col in df.columns if col in col_map})

            if "adjusted_close" not in df.columns:
                df["adjusted_close"] = df["close"]

            required_cols = ["date", "open", "high", "low", "close", "adjusted_close", "volume"]
            for c in required_cols:
                if c not in df.columns:
                    df[c] = None

            df = df[required_cols].copy()
            df["symbol"] = internal_sym

            # Convert numeric types
            for c in ["open", "high", "low", "close", "adjusted_close", "volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")

            # Drop invalid/NaN rows
            df = df.dropna(subset=["date", "open", "high", "low", "close"])
            df = df[df["open"] > 0]
            df = df.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)

            if len(df) >= 5:
                return df

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}")
            time.sleep(1.0)

    return None


def download_and_store_universe(
    symbols: Optional[List[str]] = None,
    period: str = "5y",
    save_to_db: bool = True,
    save_parquet: bool = True
) -> Dict[str, Any]:
    """
    Downloads historical OHLCV data for entire universe.
    Saves partitioned Parquet files and performs bulk SQLite upserts.
    """
    target_symbols = symbols or get_universe("ALL")
    total_symbols = len(target_symbols)

    print(f"Starting Historical Dataset Builder for {total_symbols} symbols (period={period})...")

    successful_symbols = []
    failed_symbols = []
    total_rows = 0

    os.makedirs(DATASET_BASE_DIR, exist_ok=True)
    for reg in ["india", "usa", "crypto"]:
        os.makedirs(os.path.join(DATASET_BASE_DIR, reg), exist_ok=True)

    for idx, sym in enumerate(target_symbols, 1):
        print(f"[{idx}/{total_symbols}] Downloading {sym}...")
        df = download_symbol_history(sym, period=period)

        if df is not None and not df.empty:
            region = get_symbol_region(sym)
            rows = len(df)
            total_rows += rows

            # Save Parquet
            if save_parquet:
                parquet_path = os.path.join(DATASET_BASE_DIR, region, f"{sym}.parquet")
                df.to_parquet(parquet_path, index=False)

            # Bulk DB Upsert
            if save_to_db:
                try:
                    save_prices_to_db(df)
                except Exception as e:
                    logger.error(f"Failed to upsert DB for {sym}: {e}")

            successful_symbols.append(sym)
            print(f"  [OK] {sym}: {rows} rows saved to {region}/{sym}.parquet")
        else:
            failed_symbols.append(sym)
            print(f"  [FAIL] {sym}: Failed to download historical data")

        time.sleep(0.1)  # Rate limiting courtesy

    summary = {
        "timestamp": datetime.now().isoformat(),
        "period": period,
        "total_symbols": total_symbols,
        "successful_symbols_count": len(successful_symbols),
        "failed_symbols_count": len(failed_symbols),
        "total_rows": total_rows,
        "successful_symbols": successful_symbols,
        "failed_symbols": failed_symbols
    }

    summary_path = os.path.join(os.path.dirname(DATASET_BASE_DIR), "download_summary.json")
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nHistorical Dataset Download Complete! Successful: {len(successful_symbols)}/{total_symbols}, Total Rows: {total_rows}")
    return summary


if __name__ == "__main__":
    download_and_store_universe()
