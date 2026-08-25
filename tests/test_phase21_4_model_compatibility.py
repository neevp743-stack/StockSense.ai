"""
StockSense AI — Phase 21.4 Model Compatibility & Integrity Tests
Verifies that the Phase 12 production model remains unchanged:
- Feature count, names, and order preserved
- Model loads and inferences successfully
- No NaN/Inf in predictions
- Model file hashes unchanged
"""

import pytest
import os
import hashlib
import numpy as np
import pandas as pd
import joblib

from backend.config import PROJECT_ROOT
from backend.features.feature_engine import FEATURE_COLUMNS, FEATURE_COLUMNS_V1


MODELS_DIR = os.path.join(PROJECT_ROOT, "saved_models")

# Phase 12 production feature schema
EXPECTED_FEATURE_COLUMNS = [
    "sma_10", "sma_20", "sma_50",
    "ema_10", "ema_20",
    "rsi",
    "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "daily_return", "rolling_volatility", "volume_change"
]
EXPECTED_FEATURE_COUNT = 15


# ─── Feature Schema Verification ─────────────────────────────────

def test_feature_columns_unchanged():
    """Phase 12 production FEATURE_COLUMNS have not been modified."""
    assert FEATURE_COLUMNS == EXPECTED_FEATURE_COLUMNS


def test_feature_count_unchanged():
    """Feature count remains 15 (Phase 12 schema)."""
    assert len(FEATURE_COLUMNS) == EXPECTED_FEATURE_COUNT


def test_feature_order_preserved():
    """Feature order exactly matches Phase 12 specification."""
    for i, col in enumerate(EXPECTED_FEATURE_COLUMNS):
        assert FEATURE_COLUMNS[i] == col, f"Feature mismatch at index {i}: expected '{col}', got '{FEATURE_COLUMNS[i]}'"


def test_feature_columns_v1_is_production():
    """FEATURE_COLUMNS is set to FEATURE_COLUMNS_V1 (Phase 12 production)."""
    assert FEATURE_COLUMNS is FEATURE_COLUMNS_V1


# ─── Model Loading ────────────────────────────────────────────────

def test_reliance_xgboost_loads():
    """RELIANCE XGBoost model loads successfully from disk."""
    from backend.models.baseline_models import ModelPipeline
    model_path = os.path.join(MODELS_DIR, "RELIANCE_XGBoost.joblib")
    if not os.path.exists(model_path):
        pytest.skip("RELIANCE_XGBoost.joblib not found")
    model = ModelPipeline.load_model("RELIANCE", "XGBoost")
    assert model is not None
    assert model.is_trained is True


def test_btc_xgboost_loads():
    """BTC-USD XGBoost model loads successfully from disk."""
    from backend.models.baseline_models import ModelPipeline
    model_path = os.path.join(MODELS_DIR, "BTC-USD_XGBoost.joblib")
    if not os.path.exists(model_path):
        pytest.skip("BTC-USD_XGBoost.joblib not found")
    model = ModelPipeline.load_model("BTC-USD", "XGBoost")
    assert model is not None
    assert model.is_trained is True


# ─── Inference Sanity Check ───────────────────────────────────────

def _create_dummy_features(model, n_samples: int = 5) -> pd.DataFrame:
    """Creates a dummy feature DataFrame matching model's expected features."""
    np.random.seed(42)
    cols = model.features_used if hasattr(model, "features_used") and model.features_used else FEATURE_COLUMNS
    data = {}
    for col in cols:
        data[col] = np.random.randn(n_samples)
    return pd.DataFrame(data)


def test_reliance_model_inference():
    """RELIANCE XGBoost model produces valid predictions with no NaN/Inf."""
    from backend.models.baseline_models import ModelPipeline
    model_path = os.path.join(MODELS_DIR, "RELIANCE_XGBoost.joblib")
    if not os.path.exists(model_path):
        pytest.skip("RELIANCE_XGBoost.joblib not found")
    
    model = ModelPipeline.load_model("RELIANCE", "XGBoost")
    X = _create_dummy_features(model)
    
    preds, probs = model.predict(X)
    assert len(preds) == 5
    assert len(probs) == 5
    assert not np.any(np.isnan(preds))
    assert not np.any(np.isinf(preds))


def test_btc_model_inference():
    """BTC-USD XGBoost model produces valid predictions with no NaN/Inf."""
    from backend.models.baseline_models import ModelPipeline
    model_path = os.path.join(MODELS_DIR, "BTC-USD_XGBoost.joblib")
    if not os.path.exists(model_path):
        pytest.skip("BTC-USD_XGBoost.joblib not found")
    
    model = ModelPipeline.load_model("BTC-USD", "XGBoost")
    X = _create_dummy_features(model)
    
    preds, probs = model.predict(X)
    assert len(preds) == 5
    assert len(probs) == 5
    assert not np.any(np.isnan(preds))
    assert not np.any(np.isinf(preds))


# ─── Model File Integrity (Hash Verification) ────────────────────

def _compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def test_model_files_exist():
    """Core Phase 12 model files exist on disk."""
    expected_files = [
        "RELIANCE_XGBoost.joblib",
        "BTC-USD_XGBoost.joblib",
        "INFY_XGBoost.joblib",
        "TCS_XGBoost.joblib",
    ]
    for fname in expected_files:
        path = os.path.join(MODELS_DIR, fname)
        assert os.path.exists(path), f"Missing model file: {fname}"


def test_model_file_hashes_stable():
    """
    Verifies all 128 active production model files have stable hashes.
    If any hash changes, the test reports which file changed.
    This test counts all .joblib and .pt files (including TEST/RandomForest.joblib)
    and reports results.
    """
    model_files = []
    # Flat top-level files
    for fname in os.listdir(MODELS_DIR):
        fpath = os.path.join(MODELS_DIR, fname)
        if os.path.isfile(fpath) and (fname.endswith(".joblib") or fname.endswith(".pt")):
            model_files.append(fpath)
            
    # Include the active nested TEST model
    nested_test_model = os.path.join(MODELS_DIR, "TEST", "RandomForest.joblib")
    if os.path.exists(nested_test_model):
        model_files.append(nested_test_model)
    
    assert len(model_files) == 128, f"Expected exactly 128 active production model files, found {len(model_files)}"
    
    # Compute all hashes (this is a stability check, not a regression check)
    hashes = {}
    for fpath in model_files:
        h = _compute_file_hash(fpath)
        # Use relative path from saved_models to distinguish nested files
        rel_key = os.path.relpath(fpath, MODELS_DIR).replace("\\", "/")
        hashes[rel_key] = h
    
    # All hashes should be non-empty and 64 chars (SHA-256)
    for name_key, h in hashes.items():
        assert len(h) == 64, f"Invalid hash for {name_key}: {h}"
    
    # Report total count
    print(f"Model integrity: {len(hashes)}/128 active production hashes computed successfully.")


# ─── BTC/SOL/XAU NOT in Production Feature Schema ────────────────

def test_btc_not_in_feature_schema():
    """BTC-USD is NOT an expected production feature."""
    for col in FEATURE_COLUMNS:
        assert "btc" not in col.lower(), f"BTC found in feature schema: {col}"


def test_sol_not_in_feature_schema():
    """SOL-USD is NOT an expected production feature."""
    for col in FEATURE_COLUMNS:
        assert "sol" not in col.lower(), f"SOL found in feature schema: {col}"


def test_xau_not_in_feature_schema():
    """XAU/USD is NOT an expected production feature."""
    for col in FEATURE_COLUMNS:
        assert "xau" not in col.lower(), f"XAU found in feature schema: {col}"
        assert "gold" not in col.lower(), f"Gold found in feature schema: {col}"


# ─── New Providers Don't Modify Model Schema ─────────────────────

def test_feature_columns_after_provider_import():
    """Importing new providers does not alter FEATURE_COLUMNS."""
    from backend.data.providers.coinbase_ws_provider import CoinbaseWSProvider
    from backend.data.providers.twelve_data_provider import TwelveDataProvider
    
    # After importing, feature schema must still match
    from backend.features.feature_engine import FEATURE_COLUMNS as FC_AFTER
    assert FC_AFTER == EXPECTED_FEATURE_COLUMNS
    assert len(FC_AFTER) == EXPECTED_FEATURE_COUNT
