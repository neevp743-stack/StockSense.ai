import os
import json
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import PROJECT_ROOT
from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS_V2, FEATURE_GROUPS
from backend.models.splitter import WalkForwardSplitter

client = TestClient(app)

def test_feature_engine_expansion_no_future_leakage():
    """Verify extended Phase 12 feature engine produces non-empty past-looking features without future leakage."""
    dates = pd.date_range("2023-01-01", periods=100)
    prices = [100.0 + i*0.5 + (i%5)*0.2 for i in range(100)]
    volumes = [1000 + i*10 for i in range(100)]
    
    df_raw = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})
    df_feat = compute_features_and_target(df_raw, target_horizon=1)
    
    assert not df_feat.empty
    assert "daily_return" in df_feat.columns
    assert "rsi" in df_feat.columns
    assert "atr_14" in df_feat.columns
    assert "volatility_regime" in df_feat.columns
    assert "target" in df_feat.columns
    
    # Last row target must be NaN because future price is unknown
    assert np.isnan(df_feat.iloc[-1]["target"])

def test_walk_forward_splitter_expanding_window():
    """Verify WalkForwardSplitter maintains chronological order across folds."""
    dates = pd.date_range("2020-01-01", periods=500)
    df = pd.DataFrame({"date": dates, "close": np.random.randn(500)})
    
    splitter = WalkForwardSplitter(min_train_size=200, val_size=50, step_size=50)
    folds = splitter.split(df)
    
    assert len(folds) >= 5
    for train_fold, val_fold in folds:
        assert train_fold["date"].max() < val_fold["date"].min()

def test_phase12_research_artifacts_exist():
    """Verify Phase 12 research artifacts exist in backend/research/phase12/."""
    res_dir = os.path.join(PROJECT_ROOT, "backend", "research", "phase12")
    assert os.path.exists(res_dir)
    
    artifacts = [
        "baseline_results.json",
        "feature_ablation.json",
        "target_horizon.json",
        "walk_forward.json",
        "confidence_analysis.json",
        "model_comparison.json",
        "final_results.json"
    ]
    for art in artifacts:
        p = os.path.join(res_dir, art)
        assert os.path.exists(p), f"Artifact '{art}' missing."
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None

def test_api_prediction_response_phase12_fields():
    """Verify GET /api/stocks/RELIANCE/prediction includes Phase 12 horizon, model version, and signal."""
    res = client.get("/api/stocks/RELIANCE/prediction")
    assert res.status_code == 200
    data = res.json()
    assert "prediction_horizon" in data
    assert "model_version" in data
    assert "signal" in data
    assert "coverage_stats" in data
