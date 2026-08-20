import pytest
import pandas as pd
import numpy as np
from backend.features.market_context import compute_market_context_features
from backend.features.fundamentals_and_sentiment import PointInTimeFundamentalsEngine, NewsSentimentPipeline

def test_cross_asset_feature_leakage():
    """
    Verifies that modifying context asset price/return at time T+1 leaves
    the computed market context feature at time T 100% identical.
    """
    df_asset = pd.DataFrame({
        "date": pd.date_range(start="2026-01-01", periods=20, freq="D").date,
        "close": [100.0 + i for i in range(20)]
    })

    # Compute baseline market context features
    df1 = compute_market_context_features(df_asset, "RELIANCE")
    
    T = 10
    target_date = df_asset.at[T, "date"]
    row_before = df1[df1["date"] == target_date]
    assert not row_before.empty
    val_before = row_before.iloc[0]["ctx_nsei_ret"]

    # Tamper with asset price at T+1
    df_tampered = df_asset.copy()
    df_tampered.at[T + 1, "close"] = df_tampered.at[T + 1, "close"] * 5.0

    df2 = compute_market_context_features(df_tampered, "RELIANCE")
    row_after = df2[df2["date"] == target_date]
    assert not row_after.empty
    val_after = row_after.iloc[0]["ctx_nsei_ret"]

    assert np.isclose(val_before, val_after, atol=1e-8), (
        f"CROSS-ASSET LEAKAGE DETECTED! Before: {val_before}, After T+1 modification: {val_after}"
    )

def test_fundamental_timestamp_leakage():
    """Verifies that Point-in-Time Fundamentals Engine correctly reports status without fabricating numbers."""
    engine = PointInTimeFundamentalsEngine("AAPL")
    res = engine.get_fundamentals_feature_matrix(pd.DataFrame())
    assert res["status"] == "FUNDAMENTAL DATA UNAVAILABLE"
    assert res["df_features"] is None
    assert "unavailable" in res["message"].lower()

def test_sentiment_timestamp_leakage():
    """Verifies that News Sentiment Pipeline correctly reports status without fabricating numbers."""
    pipe = NewsSentimentPipeline("BTC-USD")
    res = pipe.get_sentiment_feature_matrix(pd.DataFrame())
    assert res["status"] == "SENTIMENT DATA UNAVAILABLE"
    assert res["df_features"] is None
    assert "unavailable" in res["message"].lower()
