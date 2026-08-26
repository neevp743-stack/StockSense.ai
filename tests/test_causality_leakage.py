"""
StockSense AI — Phase 21.5 Causality & Leakage-Protection Audit Tests
Verifies that market intelligence, indicators, breakouts, swing highs/lows,
and trade setup signals are strictly causal and have zero future look-ahead leaks.
"""

import pandas as pd
import numpy as np
import pytest
from backend.services.market_intelligence_service import (
    calculate_indicators,
    analyze_market_structure_and_features
)

@pytest.fixture
def base_causal_data():
    """Generates 300 candles of trending and ranging behavior."""
    np.random.seed(1337)
    n = 300
    dates = pd.date_range(start="2026-01-01", periods=n, freq="D")
    
    close = [100.0]
    for i in range(1, n):
        close.append(close[-1] + np.random.uniform(-2, 3))
            
    close = np.array(close)
    high = close + np.random.uniform(0.1, 1.5, n)
    low = close - np.random.uniform(0.1, 1.5, n)
    open_val = close - np.random.uniform(-0.8, 0.8, n)
    volume = np.random.uniform(1000, 5000, n)
    
    df = pd.DataFrame({
        "date": dates,
        "open": open_val,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    })
    return df

def test_causality_slice_invariance(base_causal_data):
    """
    Strips future candles and asserts computed values at index K are identical.
    Ensures calculations at N never inspect N+1.
    """
    n = len(base_causal_data)
    # Perform audit at slice index K
    k = 250
    
    # 1. Full Dataset Run
    df_full = calculate_indicators(base_causal_data)
    # Slice the computed indicators up to K
    df_full_at_k = df_full.iloc[:k+1].copy()
    full_run_analysis = analyze_market_structure_and_features(df_full_at_k)

    # 2. Causal Sliced Dataset Run
    # We slice raw candles first, ensuring index > K is completely hidden from indicators
    sliced_raw_data = base_causal_data.iloc[:k+1].copy()
    df_sliced = calculate_indicators(sliced_raw_data)
    sliced_run_analysis = analyze_market_structure_and_features(df_sliced)

    # Assert indicators are identical at index K
    row_full_k = df_full.iloc[k]
    row_sliced_k = df_sliced.iloc[k]
    
    test_indicators = [
        "ema_9", "ema_21", "ema_50", "ema_200",
        "sma_20", "sma_50", "sma_200",
        "rsi_14", "macd_line", "macd_signal", "macd_hist",
        "atr_14", "bb_upper", "bb_lower", "vwap", "relative_volume"
    ]
    for ind in test_indicators:
        val_full = row_full_k[ind]
        val_sliced = row_sliced_k[ind]
        if np.isnan(val_full) and np.isnan(val_sliced):
            continue
        assert float(val_full) == pytest.approx(float(val_sliced), abs=1e-6), \
            f"Indicator '{ind}' failed causality slice check at index {k}"

    # Assert structural details, regime, confluence, and setups are identical
    assert full_run_analysis["price"] == sliced_run_analysis["price"]
    assert full_run_analysis["regime"] == sliced_run_analysis["regime"]
    assert full_run_analysis["confluence"]["score"] == sliced_run_analysis["confluence"]["score"]
    
    assert full_run_analysis["structure"]["trend"] == sliced_run_analysis["structure"]["trend"]
    assert full_run_analysis["structure"]["swing_high"] == sliced_run_analysis["structure"]["swing_high"]
    assert full_run_analysis["structure"]["swing_low"] == sliced_run_analysis["structure"]["swing_low"]
    
    assert full_run_analysis["setup"]["bias"] == sliced_run_analysis["setup"]["bias"]
    assert full_run_analysis["setup"]["stop_loss"] == sliced_run_analysis["setup"]["stop_loss"]
    assert full_run_analysis["setup"]["tp1"] == sliced_run_analysis["setup"]["tp1"]
    assert full_run_analysis["setup"]["tp2"] == sliced_run_analysis["setup"]["tp2"]
