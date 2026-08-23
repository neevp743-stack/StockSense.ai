"""
StockSense AI — Phase 17 Research Training Dataset Builder
Generates a machine-learning-ready dataset by building past-looking features (Phase 12/13/15)
and leakage-safe T+1 classification targets across the entire multi-asset universe.
Saves backend/research/phase17/data/compiled_training_dataset.parquet.
"""

import os
import glob
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS_V2
from backend.data.universe import get_universe

logger = logging.getLogger(__name__)

DATASET_BASE_DIR = os.path.join("backend", "research", "phase17", "data")
COMPILED_DATASET_PATH = os.path.join(DATASET_BASE_DIR, "compiled_training_dataset.parquet")
SUMMARY_PATH = os.path.join("backend", "research", "phase17", "dataset_summary.json")


def build_symbol_features_and_target(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Computes past-looking features at or before timestamp T and T+1 leakage-safe target.
    """
    if df is None or df.empty or len(df) < 60:
        return pd.DataFrame()

    df = df.sort_values("date").reset_index(drop=True)
    df["symbol"] = symbol.upper().strip()

    # Compute Phase 12/13/15 technical features and T+1 target
    feat_df = compute_features_and_target(df, target_horizon=1)
    if feat_df is None or feat_df.empty:
        return pd.DataFrame()

    # Drop target column's last row where target is NaN
    feat_df = feat_df.dropna(subset=["target"]).copy()

    # Drop helper column if present
    if "future_close" in feat_df.columns:
        feat_df = feat_df.drop(columns=["future_close"])

    # Drop initial warmup rows containing NaNs in technical indicators
    feat_df = feat_df.dropna().reset_index(drop=True)

    return feat_df


def build_compiled_training_dataset() -> Dict[str, Any]:
    """
    Scans symbol Parquet datasets, builds features & targets per symbol,
    concatenates into compiled_training_dataset.parquet, and writes dataset_summary.json.
    """
    parquet_files = glob.glob(os.path.join(DATASET_BASE_DIR, "**", "*.parquet"), recursive=True)
    # Exclude compiled dataset itself if it exists
    parquet_files = [f for f in parquet_files if not f.endswith("compiled_training_dataset.parquet")]

    print(f"Building Research Training Dataset across {len(parquet_files)} symbol files...")

    compiled_dfs = []
    symbol_row_counts = {}
    date_ranges = {}
    insufficient_symbols = []

    for filepath in parquet_files:
        sym = os.path.basename(filepath).replace(".parquet", "")
        try:
            raw_df = pd.read_parquet(filepath)
            proc_df = build_symbol_features_and_target(raw_df, sym)

            if proc_df is not None and not proc_df.empty and len(proc_df) >= 30:
                compiled_dfs.append(proc_df)
                rows = len(proc_df)
                symbol_row_counts[sym] = rows
                date_ranges[sym] = {
                    "start": proc_df["date"].min(),
                    "end": proc_df["date"].max()
                }
            else:
                insufficient_symbols.append(sym)
        except Exception as e:
            logger.error(f"Failed to process {sym}: {e}")
            insufficient_symbols.append(sym)

    if not compiled_dfs:
        raise RuntimeError("No valid symbol datasets available to build training dataset.")

    master_df = pd.concat(compiled_dfs, ignore_index=True)

    # Sort master dataset chronologically
    master_df = master_df.sort_values(["date", "symbol"]).reset_index(drop=True)

    # Save compiled Parquet file
    os.makedirs(os.path.dirname(COMPILED_DATASET_PATH), exist_ok=True)
    master_df.to_parquet(COMPILED_DATASET_PATH, index=False)

    total_rows = len(master_df)
    feature_cols = [c for c in master_df.columns if c not in ["symbol", "date", "target"]]

    # Chronological Split Counts: 70% Train, 15% Validation, 15% Holdout
    train_end_idx = int(total_rows * 0.70)
    val_end_idx = int(total_rows * 0.85)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_symbols": len(symbol_row_counts),
        "total_rows": total_rows,
        "feature_count": len(feature_cols),
        "target_count": 1,
        "feature_columns": feature_cols,
        "training_rows": train_end_idx,
        "validation_rows": val_end_idx - train_end_idx,
        "holdout_rows": total_rows - val_end_idx,
        "rows_per_symbol": symbol_row_counts,
        "date_range_per_symbol": date_ranges,
        "symbols_with_insufficient_observations": insufficient_symbols
    }

    os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Compiled Training Dataset Saved to {COMPILED_DATASET_PATH}")
    print(f"Total Rows: {total_rows}, Features: {len(feature_cols)}, Symbols: {len(symbol_row_counts)}")
    return summary


if __name__ == "__main__":
    build_compiled_training_dataset()
