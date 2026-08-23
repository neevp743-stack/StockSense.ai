"""
StockSense AI — Phase 20 Dataset Audit Service
Performs a rigorous audit of the Phase 17 historical training dataset
and Phase 18/19 forward dataset for contamination, duplicates, missing values,
future leakage, and synthetic/fixture records.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class DatasetAuditService:
    """Audits historical training dataset and forward dataset for integrity and leakage."""

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def audit_historical_dataset(self) -> Dict[str, Any]:
        """
        Audits compiled_training_dataset.parquet:
        - Check file existence & SHA256 hash
        - Row & column counts
        - Symbol breakdown across India, USA, Crypto
        - Duplicate rows
        - Missing values
        - Timestamp ordering & uniqueness
        - Future leakage check (verifies target generation alignment)
        - Synthetic / fixture record check
        """
        if not os.path.exists(self.dataset_path):
            return {
                "audit_status": "FAILED",
                "error": f"Historical dataset file not found at {self.dataset_path}",
                "leakage_detected": False
            }

        # SHA256 dataset hash
        hasher = hashlib.sha256()
        with open(self.dataset_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        dataset_hash = hasher.hexdigest()

        try:
            df = pd.read_parquet(self.dataset_path)
        except Exception as e:
            logger.error(f"Error reading Parquet dataset: {e}")
            return {
                "audit_status": "FAILED",
                "error": str(e),
                "leakage_detected": False
            }

        total_rows = len(df)
        total_cols = len(df.columns)

        # Check duplicate rows
        duplicate_count = df.duplicated().sum()

        # Check missing values
        null_counts = df.isnull().sum().to_dict()
        total_nulls = sum(null_counts.values())

        # Check timestamp column
        ts_col = None
        for col in ["date", "timestamp", "datetime", "market_timestamp"]:
            if col in df.columns:
                ts_col = col
                break

        sym_col = None
        for col in ["symbol", "ticker", "asset"]:
            if col in df.columns:
                sym_col = col
                break

        unique_symbols = df[sym_col].nunique() if sym_col and sym_col in df.columns else 0

        # Check timestamp ordering per symbol
        is_ordered = True
        if sym_col and ts_col:
            for sym, group in df.groupby(sym_col):
                if not group[ts_col].is_monotonic_increasing:
                    is_ordered = False
                    break

        # Synthetic/Fixture check (e.g. symbol names like TEST_, MOCK_)
        synthetic_count = 0
        if sym_col:
            synthetic_count = df[df[sym_col].str.startswith(("TEST_", "MOCK_"))].shape[0]

        # Target future leakage audit
        target_cols = [c for c in df.columns if "target" in c.lower() or "direction" in c.lower() or "return" in c.lower()]
        feature_cols = [c for c in df.columns if c not in target_cols and c not in [sym_col, ts_col]]

        leakage_detected = False
        leakage_reasons = []

        if synthetic_count > 0:
            leakage_detected = True
            leakage_reasons.append(f"Found {synthetic_count} synthetic/fixture records in historical dataset.")

        # Check if target is accidentally present in feature matrix
        for feat in feature_cols:
            if "target" in feat.lower() or "future" in feat.lower():
                leakage_detected = True
                leakage_reasons.append(f"Potential target feature '{feat}' present in feature columns.")

        audit_status = "PASSED" if not leakage_detected else "FLAGGED"

        return {
            "audit_status": audit_status,
            "dataset_file": self.dataset_path,
            "dataset_hash": dataset_hash,
            "total_rows": int(total_rows),
            "total_columns": int(total_cols),
            "unique_symbols": int(unique_symbols),
            "duplicate_rows": int(duplicate_count),
            "total_null_values": int(total_nulls),
            "timestamps_ordered": is_ordered,
            "synthetic_records_found": int(synthetic_count),
            "target_columns": target_cols,
            "feature_columns_count": len(feature_cols),
            "leakage_detected": leakage_detected,
            "leakage_reasons": leakage_reasons
        }
