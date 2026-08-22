import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def compute_market_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes past-looking market regime labels across two independent dimensions:
    1. Trend Regime: BULL, BEAR, SIDEWAYS
    2. Volatility Regime: HIGH_VOLATILITY, LOW_VOLATILITY
    
    LEAKAGE PREVENTION RULE:
    1. All calculations use ONLY rolling windows of prices <= index t.
    2. Future close prices or full-dataset statistics are NEVER accessed.
    """
    if df is None or df.empty or len(df) < 60:
        return df

    df_res = df.copy().sort_values("date").reset_index(drop=True)
    close = df_res["close"]

    # 1. Past-looking Moving Averages for Trend Classification
    sma_10 = close.rolling(window=10, min_periods=10).mean()
    sma_50 = close.rolling(window=50, min_periods=50).mean()
    
    # Distance from SMA50 (within 1% = SIDEWAYS signal)
    sma50_dist = (close - sma_50).abs() / sma_50

    # Trend Regime Classification
    trend_conditions = [
        (close > sma_50) & (sma_10 > sma_50) & (sma50_dist > 0.008),
        (close < sma_50) & (sma_10 < sma_50) & (sma50_dist > 0.008)
    ]
    trend_choices = ["BULL", "BEAR"]
    df_res["trend_regime"] = np.select(trend_conditions, trend_choices, default="SIDEWAYS")

    # 2. Past-looking Volatility Classification
    daily_returns = close.pct_change()
    vol_20d = daily_returns.rolling(window=20, min_periods=20).std()
    vol_60d_median = vol_20d.rolling(window=60, min_periods=30).median()

    vol_conditions = [
        vol_20d > vol_60d_median
    ]
    vol_choices = ["HIGH_VOLATILITY"]
    df_res["volatility_regime"] = np.select(vol_conditions, vol_choices, default="LOW_VOLATILITY")

    # 3. Explicit Combined Display Label for Telemetry & UI
    df_res["combined_regime"] = df_res["trend_regime"] + " (" + df_res["volatility_regime"].str.replace("_VOLATILITY", " VOL") + ")"

    return df_res

def get_latest_regime(df: pd.DataFrame) -> Dict[str, str]:
    """Returns the latest market regime status dict for a given asset dataframe."""
    if df is None or df.empty or "trend_regime" not in df.columns:
        df_calc = compute_market_regimes(df)
        if df_calc.empty:
            return {
                "trend_regime": "SIDEWAYS",
                "volatility_regime": "LOW_VOLATILITY",
                "combined_regime": "SIDEWAYS (LOW VOL)"
            }
        df = df_calc

    latest = df.iloc[-1]
    return {
        "trend_regime": str(latest.get("trend_regime", "SIDEWAYS")),
        "volatility_regime": str(latest.get("volatility_regime", "LOW_VOLATILITY")),
        "combined_regime": str(latest.get("combined_regime", "SIDEWAYS (LOW VOL)"))
    }
