import pytest
import pandas as pd
import numpy as np

from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS

def test_future_data_leakage_prevention():
    """
    CRITICAL UNIT TEST: Proves that feature calculations at row index T never use 
    Close T+1, Volume T+1, or any future information.
    
    Methodology:
    1. Create a baseline synthetic price series.
    2. Compute features F1.
    3. Modify Close and Volume ONLY at index T+1 and subsequent future rows.
    4. Compute features F2.
    5. Verify that feature values at index T in F1 and F2 are 100% IDENTICAL.
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    prices = 100.0 + np.cumsum(np.random.randn(100))
    volumes = np.random.randint(1000, 5000, size=100)

    df_base = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": volumes.astype(float)
    })

    # 1. Feature matrix F1
    f1 = compute_features_and_target(df_base)

    target_idx = 20  # Choose index T = 20 (within 50 post-warmup rows)

    # 2. Modify prices and volume drastically at T+1 (index 21 in f1) onwards
    df_future_modified = df_base.copy()
    # Since warmup dropped 49 rows, index 20 in f1 corresponds to index 20 + 49 = 69 in df_base
    base_target_idx = 20 + 49
    df_future_modified.loc[base_target_idx + 1:, "close"] *= 10.0  # 10x price jump at T+1
    df_future_modified.loc[base_target_idx + 1:, "high"] *= 10.0
    df_future_modified.loc[base_target_idx + 1:, "low"] *= 10.0
    df_future_modified.loc[base_target_idx + 1:, "open"] *= 10.0
    df_future_modified.loc[base_target_idx + 1:, "volume"] *= 100.0  # 100x volume surge at T+1

    # 3. Feature matrix F2
    f2 = compute_features_and_target(df_future_modified)

    # 4. Assert feature values at index T (60) are completely identical
    row_f1 = f1.iloc[target_idx][FEATURE_COLUMNS].to_dict()
    row_f2 = f2.iloc[target_idx][FEATURE_COLUMNS].to_dict()

    for col in FEATURE_COLUMNS:
        v1 = row_f1[col]
        v2 = row_f2[col]
        assert np.isclose(v1, v2, rtol=1e-7, equal_nan=True), (
            f"LEAKAGE DETECTED in indicator '{col}' at index {target_idx}! "
            f"Original: {v1}, Modified Future: {v2}"
        )

    print("Future leakage test PASSED successfully! Zero future information leaks into feature matrix.")

def test_target_generation_uses_future_only_for_label():
    """
    Verifies that target label uses Close_{t+1} ONLY for label generation, 
    and target is NaN for the final row where future close is unknown.
    """
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "open": [100.0]*60,
        "high": [105.0]*60,
        "low": [95.0]*60,
        "close": list(range(100, 160)),
        "volume": [1000.0]*60
    })

    df_feat = compute_features_and_target(df)
    
    # Since close is strictly increasing (100, 101, 102...), target for non-last rows must be 1 (UP)
    non_last_targets = df_feat["target"].iloc[:-1]
    assert (non_last_targets == 1).all()

    # The last row raw before warm-up drop must have target = NaN
    df_raw_feat = compute_features_and_target(df)
    assert pd.isna(df_raw_feat["target"].iloc[-1])
