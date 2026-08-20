import pytest
import pandas as pd
import numpy as np

from backend.features.feature_engine import compute_features_and_target
from backend.models.splitter import chronological_split
from backend.models.baseline_models import ModelPipeline

def test_baseline_models_pipeline():
    dates = pd.date_range("2024-01-01", periods=150, freq="D")
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.randn(150))
    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": np.random.randint(1000, 5000, size=150).astype(float)
    })

    df_feat = compute_features_and_target(df)
    train_df, val_df, _ = chronological_split(df_feat, 0.7, 0.15, 0.15)

    pipe = ModelPipeline("RandomForest", "TEST")
    metrics = pipe.train(train_df, val_df)

    assert pipe.is_trained is True
    assert "accuracy" in metrics
    assert "brier_score" in metrics

    preds, probs = pipe.predict(val_df)
    assert len(preds) == len(val_df)
    assert len(probs) == len(val_df)
    assert ((probs >= 0.0) & (probs <= 1.0)).all()
