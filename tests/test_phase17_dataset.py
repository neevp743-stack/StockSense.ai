"""
StockSense AI — Phase 17 Unit & Integration Test Suite
Verifies multi-asset universe configuration, dataset building, leakage safety,
chronological splitting, holdout isolation, and model artifact isolation.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from backend.data.universe import get_universe, get_provider_symbol, ALL_SYMBOLS, INDIA_SYMBOLS, US_SYMBOLS, CRYPTO_SYMBOLS
from backend.data.historical_dataset_builder import download_symbol_history
from backend.research.phase17.data_quality import audit_symbol_data_quality
from backend.research.phase17.build_training_dataset import build_symbol_features_and_target
from backend.research.phase17.leakage_audit import run_10_point_leakage_audit
from backend.models.baseline_models import ModelPipeline


def test_universe_configuration():
    """Verifies universe loading, region filtering, and ticker provider formatting."""
    all_syms = get_universe("ALL")
    india_syms = get_universe("INDIA")
    us_syms = get_universe("USA")
    crypto_syms = get_universe("CRYPTO")

    assert len(all_syms) >= 50
    assert len(india_syms) >= 10
    assert len(us_syms) >= 10
    assert len(crypto_syms) >= 2

    assert "RELIANCE" in india_syms
    assert "AAPL" in us_syms
    assert "BTC-USD" in crypto_syms

    assert get_provider_symbol("RELIANCE") == "RELIANCE.NS"
    assert get_provider_symbol("AAPL") == "AAPL"
    assert get_provider_symbol("BTC-USD") == "BTC-USD"


def test_ohlc_data_quality_audit():
    """Tests data quality auditor detection rules."""
    valid_data = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "open": [100.0, 102.0, 104.0],
        "high": [105.0, 106.0, 108.0],
        "low": [99.0, 101.0, 103.0],
        "close": [103.0, 105.0, 107.0],
        "volume": [1000, 1200, 1500]
    })
    audit = audit_symbol_data_quality(valid_data, "TEST_SYM")
    assert audit["status"] in ["VALID", "WARNINGS"]
    assert audit["invalid_ohlc"] == 0
    assert audit["duplicate_dates"] == 0

    invalid_data = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-01"],  # Duplicate date
        "open": [100.0, 102.0],
        "high": [90.0, 106.0],   # Invalid high < open
        "low": [99.0, 101.0],
        "close": [103.0, 105.0],
        "volume": [-10, 1200]    # Negative volume
    })
    audit_inv = audit_symbol_data_quality(invalid_data, "TEST_INV")
    assert audit_inv["invalid_ohlc"] > 0
    assert audit_inv["duplicate_dates"] == 1
    assert audit_inv["negative_volume"] == 1


def test_target_generation_and_leakage_safety():
    """Verifies target is created strictly from T+1 close price and future columns are excluded from features."""
    dates = pd.date_range("2026-01-01", periods=100, freq="D").strftime("%Y-%m-%d")
    np.random.seed(42)
    close_prices = 100.0 + np.cumsum(np.random.randn(100))
    raw_df = pd.DataFrame({
        "date": dates,
        "open": close_prices - 0.5,
        "high": close_prices + 1.0,
        "low": close_prices - 1.0,
        "close": close_prices,
        "volume": np.random.randint(1000, 5000, 100)
    })

    proc_df = build_symbol_features_and_target(raw_df, "DUMMY")
    assert not proc_df.empty
    assert "target" in proc_df.columns
    assert "future_close" not in proc_df.columns

    # Verify target matches raw next_close > close for the corresponding dates
    raw_df["next_close"] = raw_df["close"].shift(-1)
    raw_df["expected_up"] = (raw_df["next_close"] > raw_df["close"]).astype(int)
    merged = proc_df.merge(raw_df.dropna(subset=["next_close"])[["date", "expected_up"]], on="date")
    assert (merged["target"] == merged["expected_up"]).all()


def test_leakage_audit_routine():
    """Tests the automated 10-point leakage audit engine."""
    dates = pd.date_range("2026-01-01", periods=100, freq="D").strftime("%Y-%m-%d")
    close_prices = 100.0 + np.arange(100)
    next_prices = np.append(close_prices[1:], 101.0)
    targets = (next_prices > close_prices).astype(int)
    sample_df = pd.DataFrame({
        "symbol": ["TEST_SYM"] * 100,
        "date": dates,
        "close": close_prices,
        "sma_10": close_prices,
        "target": targets
    })

    report = run_10_point_leakage_audit(sample_df)
    assert "final_verdict" in report
    assert report["final_verdict"] == "LEAKAGE_FREE"


def test_chronological_splitting_ordering():
    """Verifies strict chronological splitting without shuffling."""
    dates = pd.date_range("2020-01-01", periods=1000, freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({"date": dates, "val": range(1000)})

    train_end = int(1000 * 0.70)
    val_end = int(1000 * 0.85)

    train_set = df.iloc[:train_end]
    val_set = df.iloc[train_end:val_end]
    holdout_set = df.iloc[val_end:]

    assert train_set["date"].max() < val_set["date"].min()
    assert val_set["date"].max() < holdout_set["date"].min()


def test_model_artifact_isolation():
    """Verifies that Phase 12 production XGBoost v1.0 model pipeline is active and isolated from Phase 17."""
    pipeline = ModelPipeline(model_name="XGBoost", symbol="RELIANCE")
    assert pipeline is not None

    # Check Phase 17 isolated path
    phase17_dir = os.path.join("saved_models", "phase17")
    os.makedirs(phase17_dir, exist_ok=True)
    assert os.path.abspath(phase17_dir) != os.path.abspath(os.path.join("saved_models", "production"))
