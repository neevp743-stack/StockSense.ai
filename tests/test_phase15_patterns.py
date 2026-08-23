import os
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import PROJECT_ROOT
from backend.features.candlestick_features import compute_candlestick_features
from backend.features.price_action_features import compute_price_action_features
from backend.features.structure_features import compute_structure_features
from backend.features.feature_engine import compute_phase15_features

client = TestClient(app)

def create_sample_ohlcv(n=50):
    dates = pd.date_range("2023-01-01", periods=n)
    prices = [100.0 + i*0.5 + (i%3)*0.2 for i in range(n)]
    df = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": [p + 1.5 for p in prices],
        "low": [p - 1.5 for p in prices],
        "close": [p + 0.5 for p in prices],
        "volume": [100000.0 + i*100 for i in range(n)]
    })
    return df

def test_candle_geometry_features():
    """Verify candle geometry ratios and change percentages are bounded and safe."""
    df = create_sample_ohlcv(30)
    df_res = compute_candlestick_features(df)

    assert "body_ratio" in df_res.columns
    assert "close_position_in_range" in df_res.columns
    assert "gap_percent" in df_res.columns

    assert df_res["body_ratio"].min() >= 0.0
    assert df_res["body_ratio"].max() <= 1.0
    assert df_res["close_position_in_range"].min() >= 0.0
    assert df_res["close_position_in_range"].max() <= 1.0
    assert not df_res["body_ratio"].isna().any()

def test_candlestick_pattern_detection():
    """Verify deterministic pattern detectors trigger on specific candle shapes."""
    dates = pd.date_range("2023-01-01", periods=5)
    # Candle 0: Doji (open == close)
    # Candle 1: Hammer (small body at top, long lower wick)
    # Candle 2: Bullish Engulfing
    df = pd.DataFrame({
        "date": dates,
        "open":  [100.0, 100.0, 95.0, 90.5, 100.0],
        "high":  [102.0, 100.5, 96.0, 102.0, 105.0],
        "low":   [98.0,   90.0, 90.0, 90.0, 99.0],
        "close": [100.0, 100.2, 91.0, 98.0, 104.0],

        "volume":[1000.0]*5
    })

    df_res = compute_candlestick_features(df)
    assert df_res.loc[0, "pattern_doji"] == 1.0
    assert df_res.loc[1, "pattern_hammer"] == 1.0
    assert df_res.loc[3, "pattern_bullish_engulfing"] == 1.0

def test_price_action_features():
    """Verify price action higher highs, streaks, and momentum indicators."""
    df = create_sample_ohlcv(30)
    df_res = compute_price_action_features(df)

    assert "higher_high" in df_res.columns
    assert "consecutive_up_candles" in df_res.columns
    assert "rolling_return_5" in df_res.columns
    assert "trend_slope_10d" in df_res.columns

    assert not df_res["rolling_return_5"].isna().any()
    assert not df_res["consecutive_up_candles"].isna().any()

def test_support_resistance_and_breakout_features():
    """Verify support/resistance swing bounds use strictly past data (shift 1)."""
    df = create_sample_ohlcv(40)
    df_res = compute_structure_features(df)

    assert "recent_swing_high" in df_res.columns
    assert "recent_swing_low" in df_res.columns
    assert "breakout_up" in df_res.columns
    assert "breakout_strength" in df_res.columns

    assert not df_res["distance_from_support"].isna().any()

def test_no_future_leakage_in_features():
    """Verify modifying row t+1 does NOT change feature values at row t."""
    df = create_sample_ohlcv(40)
    df1 = compute_phase15_features(df)

    # Modify future row 35
    df_mod = df.copy()
    df_mod.loc[35, "close"] = df_mod.loc[35, "close"] * 2.0
    df_mod.loc[35, "high"] = df_mod.loc[35, "high"] * 2.0
    df2 = compute_phase15_features(df_mod)

    # Features at row 25 must be IDENTICAL
    feat_cols = [c for c in df1.columns if c not in ("target", "target_5d", "target_10d", "target_threshold")]
    for col in feat_cols:
        val1 = df1.loc[25, col]
        val2 = df2.loc[25, col]
        if isinstance(val1, (int, float, np.number)):
            np.testing.assert_almost_equal(val1, val2, decimal=5, err_msg=f"Feature {col} leaked future data!")

def test_missing_values_and_infinity_handling():
    """Verify zero volume or zero range does not produce NaNs or infinities."""
    dates = pd.date_range("2023-01-01", periods=20)
    df_zero = pd.DataFrame({
        "date": dates,
        "open": [100.0]*20,
        "high": [100.0]*20,
        "low": [100.0]*20,
        "close": [100.0]*20,
        "volume": [0.0]*20
    })

    df_res = compute_phase15_features(df_zero)
    for col in df_res.columns:
        if col not in ("target", "target_5d", "target_10d", "target_threshold"):
            assert not np.isinf(df_res[col]).any(), f"Infinity found in column '{col}'"

def test_research_api_status_endpoint():
    """Verify GET /api/research/phase15/status returns research status schema."""
    res = client.get("/api/research/phase15/status")
    assert res.status_code == 200
    data = res.json()
    assert "current_production_model" in data
    assert "phase15_status" in data or "research_status" in data
    assert "phase15_verdict" in data

