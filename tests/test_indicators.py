import pytest
import pandas as pd
import numpy as np
from backend.features.feature_engine import (
    calculate_sma, calculate_ema, calculate_rsi, calculate_macd, calculate_bollinger_bands
)

def test_sma_calculation():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    sma3 = calculate_sma(s, window=3)
    assert pd.isna(sma3.iloc[0])
    assert pd.isna(sma3.iloc[1])
    assert np.isclose(sma3.iloc[2], 2.0)
    assert np.isclose(sma3.iloc[4], 4.0)

def test_rsi_bounds():
    np.random.seed(42)
    s = pd.Series(100.0 + np.cumsum(np.random.randn(50)))
    rsi = calculate_rsi(s, 14)
    assert (rsi >= 0.0).all() and (rsi <= 100.0).all()

def test_bollinger_bands_geometry():
    np.random.seed(42)
    s = pd.Series(100.0 + np.cumsum(np.random.randn(50)))
    upper, lower, width = calculate_bollinger_bands(s, window=20, num_std=2.0)
    valid_mask = ~upper.isna()
    assert (upper[valid_mask] >= lower[valid_mask]).all()
