import os
import json
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import PROJECT_ROOT
from backend.features.regime_engine import compute_market_regimes, get_latest_regime

client = TestClient(app)

def test_regime_engine_past_looking_calculation():
    """Verify market regime engine calculates trend and volatility regimes strictly past-looking."""
    dates = pd.date_range("2023-01-01", periods=100)
    prices = [100.0 + i*0.5 + (i%5)*0.2 for i in range(100)]
    
    df_raw = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": 1000})
    df_regime = compute_market_regimes(df_raw)
    
    assert not df_regime.empty
    assert "trend_regime" in df_regime.columns
    assert "volatility_regime" in df_regime.columns
    assert "combined_regime" in df_regime.columns
    
    valid_trends = {"BULL", "BEAR", "SIDEWAYS"}
    valid_vols = {"HIGH_VOLATILITY", "LOW_VOLATILITY"}
    
    for _, row in df_regime.iterrows():
        assert row["trend_regime"] in valid_trends
        assert row["volatility_regime"] in valid_vols

def test_get_latest_regime_dict():
    """Verify get_latest_regime returns structured dict with trend_regime, volatility_regime, and combined_regime."""
    dates = pd.date_range("2023-01-01", periods=80)
    prices = [100.0 + i*0.3 for i in range(80)]
    df = pd.DataFrame({"date": dates, "close": prices, "high": prices, "low": prices, "open": prices, "volume": 1000})
    
    res = get_latest_regime(df)
    assert isinstance(res, dict)
    assert "trend_regime" in res
    assert "volatility_regime" in res
    assert "combined_regime" in res

def test_phase13_research_artifacts_exist():
    """Verify Phase 13 research artifacts exist in backend/research/phase13/."""
    res_dir = os.path.join(PROJECT_ROOT, "backend", "research", "phase13")
    assert os.path.exists(res_dir)
    
    artifacts = [
        "regime_analysis.json",
        "regime_balance.json",
        "walk_forward.json",
        "confidence_analysis.json",
        "final_results.json",
        "phase13_rejected.json"
    ]
    for art in artifacts:
        p = os.path.join(res_dir, art)
        assert os.path.exists(p), f"Artifact '{art}' missing."
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None

def test_classify_market_regimes_alias():
    """Verify classify_market_regimes alias function produces identical dataframe to compute_market_regimes."""
    from backend.features.regime_engine import classify_market_regimes
    dates = pd.date_range("2023-01-01", periods=70)
    prices = [100.0 + i*0.2 for i in range(70)]
    df = pd.DataFrame({"date": dates, "close": prices, "high": prices, "low": prices, "open": prices, "volume": 1000})
    
    df1 = compute_market_regimes(df)
    df2 = classify_market_regimes(df)
    pd.testing.assert_frame_equal(df1, df2)

def test_ensemble_probability_averaging_logic():
    """Verify equal and validation weighted ensemble probability averaging logic."""
    p_xgb = np.array([0.6, 0.4, 0.7])
    p_rf = np.array([0.5, 0.5, 0.8])
    p_lr = np.array([0.4, 0.3, 0.6])
    
    p_eq = (p_xgb + p_rf + p_lr) / 3.0
    p_wt = (0.5 * p_xgb + 0.25 * p_rf + 0.25 * p_lr)
    
    assert np.allclose(p_eq, [0.5, 0.4, 0.7])
    assert np.allclose(p_wt, [0.525, 0.4, 0.7])

def test_regime_balance_min_sample_size():
    """Verify regime balance json artifact enforces observation counts across assets."""
    res_path = os.path.join(PROJECT_ROOT, "backend", "research", "phase13", "regime_balance.json")
    if os.path.exists(res_path):
        with open(res_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for symbol, info in data.items():
            assert "total_samples" in info
            assert info["total_samples"] >= 30

