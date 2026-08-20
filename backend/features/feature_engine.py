import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any

FEATURE_COLUMNS = [
    "sma_10", "sma_20", "sma_50",
    "ema_10", "ema_20",
    "rsi",
    "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "daily_return", "rolling_volatility", "volume_change"
]

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average over rolling window (strictly past-looking)."""
    return series.rolling(window=window, min_periods=window).mean()

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average (strictly past-looking)."""
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI) using Wilder's Smoothing.
    Strictly past-looking.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Moving Average Convergence Divergence (MACD).
    Returns (macd_line, signal_line, macd_histogram). Strictly past-looking.
    """
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Bollinger Bands.
    Returns (upper_band, lower_band, bandwidth). Strictly past-looking.
    """
    rolling_mean = series.rolling(window=window, min_periods=window).mean()
    rolling_std = series.rolling(window=window, min_periods=window).std()
    upper = rolling_mean + (rolling_std * num_std)
    lower = rolling_mean - (rolling_std * num_std)
    bandwidth = (upper - lower) / rolling_mean.replace(0, np.nan)
    return upper, lower, bandwidth

def compute_features_and_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all technical indicators and next-day directional target.
    
    LEAKAGE PREVENTION RULE:
    1. Features at index t use ONLY rows <= t.
    2. Target at index t uses close price at t+1 (Close_{t+1} > Close_t).
    3. The last row of dataset will have target = NaN because next-day close is unknown.
    """
    if df is None or df.empty or len(df) < 50:
        return pd.DataFrame()

    df_feat = df.copy().sort_values("date").reset_index(drop=True)
    close = df_feat["close"]
    volume = df_feat["volume"]

    # Simple Moving Averages
    df_feat["sma_10"] = calculate_sma(close, 10)
    df_feat["sma_20"] = calculate_sma(close, 20)
    df_feat["sma_50"] = calculate_sma(close, 50)

    # Exponential Moving Averages
    df_feat["ema_10"] = calculate_ema(close, 10)
    df_feat["ema_20"] = calculate_ema(close, 20)

    # RSI
    df_feat["rsi"] = calculate_rsi(close, 14)

    # MACD
    macd, signal, hist = calculate_macd(close, 12, 26, 9)
    df_feat["macd"] = macd
    df_feat["macd_signal"] = signal
    df_feat["macd_hist"] = hist

    # Bollinger Bands
    upper, lower, width = calculate_bollinger_bands(close, 20, 2.0)
    df_feat["bb_upper"] = upper
    df_feat["bb_lower"] = lower
    df_feat["bb_width"] = width

    # Daily Return
    df_feat["daily_return"] = close.pct_change()

    # Rolling Volatility (20-day std dev of daily returns)
    df_feat["rolling_volatility"] = df_feat["daily_return"].rolling(window=20, min_periods=20).std()

    # Volume Change (1-day % change)
    df_feat["volume_change"] = volume.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Target construction: Next day close > current close
    # Using shift(-1) ONLY for target label generation
    next_close = close.shift(-1)
    df_feat["next_close"] = next_close
    df_feat["target"] = np.where(next_close > close, 1, 0)
    
    # The last row has no future close price available, set target to NaN
    df_feat.loc[df_feat.index[-1], "target"] = np.nan

    # Drop early warm-up rows where 50-day SMA is NaN (to ensure clean dataset)
    df_clean = df_feat.dropna(subset=["sma_50"]).reset_index(drop=True)
    return df_clean
