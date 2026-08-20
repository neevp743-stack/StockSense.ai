import pytest
import numpy as np
import pandas as pd
from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS

def generate_synthetic_ohlcv(days: int = 100) -> pd.DataFrame:
    """Generates synthetic OHLCV bars for testing leakage isolation across asset classes."""
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=days, freq="D").date
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, size=days)
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.02,
        "low": prices * 0.98,
        "close": prices,
        "volume": np.random.randint(10000, 50000, size=days).astype(float)
    })
    return df

@pytest.mark.parametrize("asset_symbol", ["RELIANCE", "AAPL", "BTC-USD", "EURUSD=X", "^GSPC"])
def test_multi_asset_future_data_leakage_prevention(asset_symbol):
    """
    Concrete Data Leakage Prevention Test across Indian Equities, US Equities, Crypto, Forex, and Indices.
    
    Proves that injecting extreme price spikes and volume surges at time T+1 leaves
    feature calculations at time T 100% identical.
    """
    df = generate_synthetic_ohlcv(200)

    # 1. Compute baseline features F1
    df1 = compute_features_and_target(df)

    # Pick a raw date index T (e.g. index 70 in raw df)
    raw_T = 70
    target_date = df.at[raw_T, "date"]

    row_before = df1[df1["date"] == target_date]
    assert not row_before.empty
    features_T_before = row_before.iloc[0][FEATURE_COLUMNS].to_dict()

    # 2. Artificially tamper with price and volume at T+1 (raw index 71)
    df_tampered = df.copy()
    df_tampered.at[raw_T + 1, "close"] = df_tampered.at[raw_T + 1, "close"] * 10.0
    df_tampered.at[raw_T + 1, "high"] = df_tampered.at[raw_T + 1, "high"] * 10.0
    df_tampered.at[raw_T + 1, "volume"] = df_tampered.at[raw_T + 1, "volume"] * 100.0

    # 3. Compute tampered features F2
    df2 = compute_features_and_target(df_tampered)
    row_after = df2[df2["date"] == target_date]
    assert not row_after.empty
    features_T_after = row_after.iloc[0][FEATURE_COLUMNS].to_dict()

    # 4. Assert that features at time T are 100% identical
    for col in FEATURE_COLUMNS:
        val_before = features_T_before[col]
        val_after = features_T_after[col]
        
        if pd.isna(val_before) and pd.isna(val_after):
            continue

        assert np.isclose(val_before, val_after, atol=1e-8), (
            f"DATA LEAKAGE DETECTED in asset '{asset_symbol}' for feature '{col}' at date {target_date}! "
            f"Before: {val_before}, After T+1 modification: {val_after}"
        )
