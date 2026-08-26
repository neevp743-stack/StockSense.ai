"""
StockSense AI — Phase 21.5 Market Intelligence Unit Tests
Verifies mathematical indicators, structure breakouts, regime classification,
and confluence calculations under normalized conditions.
"""

import pandas as pd
import numpy as np
import pytest
from backend.services.market_intelligence_service import (
    calculate_indicators,
    analyze_market_structure_and_features,
    fetch_candles_dataframe
)

@pytest.fixture
def sample_market_data():
    """Generates 300 candles representing a bullish trend followed by a range."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range(start="2026-01-01", periods=n, freq="D")
    
    # Generate path: simple uptrend
    close = [100.0]
    for i in range(1, n):
        if i < 150:
            # Bullish trend
            close.append(close[-1] + np.random.uniform(-1, 3))
        else:
            # Ranging
            close.append(close[-1] + np.random.uniform(-2, 2))
            
    close = np.array(close)
    high = close + np.random.uniform(0.5, 2.0, n)
    low = close - np.random.uniform(0.5, 2.0, n)
    open_val = close - np.random.uniform(-1.0, 1.0, n)
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

def test_calculate_indicators(sample_market_data):
    """Verifies indicators calculate without throwing errors or returning infinite values."""
    df_ind = calculate_indicators(sample_market_data)
    assert not df_ind.empty
    assert len(df_ind) == 300
    
    # Check that crucial columns exist
    required_cols = [
        "ema_9", "ema_21", "ema_50", "ema_200",
        "sma_20", "sma_50", "sma_200",
        "rsi_14", "macd_line", "macd_signal", "macd_hist",
        "atr_14", "bb_upper", "bb_lower", "vwap", "relative_volume"
    ]
    for col in required_cols:
        assert col in df_ind.columns
        # Values after warmup should be valid numeric values
        assert not df_ind[col].iloc[250:].isna().any()
        assert not np.isinf(df_ind[col].iloc[250:]).any()

def test_analyze_market_structure_and_features(sample_market_data):
    """Verifies structural breakouts, regimes, and confluences behave logically."""
    df_ind = calculate_indicators(sample_market_data)
    res = analyze_market_structure_and_features(df_ind)
    
    assert isinstance(res, dict)
    assert "price" in res
    assert "indicators" in res
    assert "structure" in res
    assert "liquidity" in res
    assert "regime" in res
    assert "confluence" in res
    assert "setup" in res

    # Verify structure parameters
    struct = res["structure"]
    assert struct["trend"] in ["BULLISH", "BEARISH", "RANGE"]
    assert 0 <= struct["confidence"] <= 100
    assert struct["swing_high"] > 0
    assert struct["swing_low"] > 0

    # Verify regime
    assert res["regime"] in [
        "TRENDING_BULLISH", "TRENDING_BEARISH", "RANGING",
        "HIGH_VOLATILITY", "LOW_VOLATILITY", "TRANSITION"
    ]

    # Verify confluences
    conf = res["confluence"]
    assert 0 <= conf["score"] <= 100
    assert isinstance(conf["reasons"], list)
    assert isinstance(conf["penalties"], list)

    # Verify setup structure
    setup = res["setup"]
    assert setup["bias"] in ["POTENTIAL LONG SETUP", "POTENTIAL SHORT SETUP", "NO QUALIFIED SETUP"]
    if setup["bias"] != "NO QUALIFIED SETUP":
        assert setup["entry_zone"] is not None
        assert setup["stop_loss"] > 0
        assert setup["tp1"] > 0
        assert setup["tp2"] > 0
        assert setup["rr"] > 0
