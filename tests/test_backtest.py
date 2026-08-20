import pytest
import pandas as pd
import numpy as np
from backend.backtest.backtester import run_backtest, calculate_cagr, calculate_max_drawdown, calculate_sharpe_ratio

def test_backtest_metrics():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "close": 100.0 + np.linspace(0, 50, 100)  # Steady upward trend
    })
    probs = np.full(100, 0.7)  # AI predicts UP with high probability

    res = run_backtest(df, probs, initial_capital=100000.0, prob_threshold=0.55)
    assert "buy_and_hold" in res
    assert "ai_strategy" in res
    assert res["ai_strategy"]["total_return_pct"] > 0
    assert "sharpe_ratio" in res["ai_strategy"]
    assert "max_drawdown_pct" in res["ai_strategy"]

def test_cagr_calculation():
    cagr = calculate_cagr(100.0, 200.0, 365)
    assert np.isclose(cagr, 1.0, rtol=1e-2)  # Doubling in 1 year = 100% CAGR
