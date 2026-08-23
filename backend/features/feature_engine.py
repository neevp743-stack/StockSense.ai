import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any

# Phase 11 baseline features
FEATURE_COLUMNS_V1 = [
    "sma_10", "sma_20", "sma_50",
    "ema_10", "ema_20",
    "rsi",
    "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "daily_return", "rolling_volatility", "volume_change"
]

# Modular Feature Groups for Ablation Testing
FEATURE_GROUPS = {
    "BASE": ["sma_10", "sma_20", "sma_50", "ema_10", "ema_20", "daily_return"],
    "TECHNICAL": ["sma_10", "sma_20", "sma_50", "ema_10", "ema_20", "close_to_sma10", "close_to_sma20", "close_to_sma50", "sma10_to_sma50"],
    "MOMENTUM": ["rsi", "macd", "macd_signal", "macd_hist", "roc_10", "stoch_k", "stoch_d", "williams_r", "rsi_change_3d", "macd_hist_change_3d"],
    "VOLATILITY": ["daily_return", "rolling_volatility", "bb_upper", "bb_lower", "bb_width", "atr_14", "volatility_change_5d"],
    "VOLUME": ["volume_change", "volume_ratio_5d", "obv_slope"],
    "REGIME": ["volatility_regime", "trend_regime"]
}

# Phase 12 full expanded feature set
FEATURE_COLUMNS_V2 = list(set([
    item for sublist in FEATURE_GROUPS.values() for item in sublist
]))
FEATURE_COLUMNS_V2.sort()

FEATURE_COLUMNS = FEATURE_COLUMNS_V1

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average over rolling window (strictly past-looking)."""
    return series.rolling(window=window, min_periods=window).mean()

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average (strictly past-looking)."""
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI) using Wilder's Smoothing."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0/period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates Moving Average Convergence Divergence (MACD)."""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates Bollinger Bands."""
    rolling_mean = series.rolling(window=window, min_periods=window).mean()
    rolling_std = series.rolling(window=window, min_periods=window).std()
    upper = rolling_mean + (rolling_std * num_std)
    lower = rolling_mean - (rolling_std * num_std)
    bandwidth = (upper - lower) / rolling_mean.replace(0, np.nan)
    return upper, lower, bandwidth

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR) strictly past-looking."""
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr

def compute_features_and_target(df: pd.DataFrame, target_horizon: int = 1) -> pd.DataFrame:
    """
    Calculates all Phase 12 technical, momentum, volatility, volume, & regime indicators.
    
    LEAKAGE PREVENTION RULE:
    1. Features at index t use ONLY rows <= t.
    2. Target at index t uses close price at t+horizon (Close_{t+horizon} > Close_t).
    3. Rows where future close price is unobserved have target = NaN.
    """
    if df is None or df.empty or len(df) < 60:
        return pd.DataFrame()

    df_feat = df.copy().sort_values("date").reset_index(drop=True)
    close = df_feat["close"]
    high = df_feat["high"] if "high" in df_feat.columns else close
    low = df_feat["low"] if "low" in df_feat.columns else close
    volume = df_feat["volume"] if "volume" in df_feat.columns else pd.Series(1.0, index=df_feat.index)

    # 1. Price & Returns
    df_feat["daily_return"] = close.pct_change()
    df_feat["return_1d"] = df_feat["daily_return"]
    df_feat["return_3d"] = close.pct_change(3)
    df_feat["return_5d"] = close.pct_change(5)
    df_feat["return_10d"] = close.pct_change(10)

    # 2. Moving Averages & Ratios
    df_feat["sma_10"] = calculate_sma(close, 10)
    df_feat["sma_20"] = calculate_sma(close, 20)
    df_feat["sma_50"] = calculate_sma(close, 50)
    df_feat["ema_10"] = calculate_ema(close, 10)
    df_feat["ema_20"] = calculate_ema(close, 20)

    df_feat["close_to_sma10"] = (close / df_feat["sma_10"]).fillna(1.0) - 1.0
    df_feat["close_to_sma20"] = (close / df_feat["sma_20"]).fillna(1.0) - 1.0
    df_feat["close_to_sma50"] = (close / df_feat["sma_50"]).fillna(1.0) - 1.0
    df_feat["sma10_to_sma50"] = (df_feat["sma_10"] / df_feat["sma_50"]).fillna(1.0) - 1.0

    # 3. Momentum & Oscillators
    df_feat["rsi"] = calculate_rsi(close, 14)
    macd, signal, hist = calculate_macd(close, 12, 26, 9)
    df_feat["macd"] = macd
    df_feat["macd_signal"] = signal
    df_feat["macd_hist"] = hist

    df_feat["roc_10"] = close.pct_change(10) * 100.0
    
    # Stochastic Oscillator
    low_14 = low.rolling(window=14, min_periods=14).min()
    high_14 = high.rolling(window=14, min_periods=14).max()
    stoch_k = 100.0 * (close - low_14) / (high_14 - low_14).replace(0, np.nan)
    df_feat["stoch_k"] = stoch_k.fillna(50.0)
    df_feat["stoch_d"] = df_feat["stoch_k"].rolling(window=3, min_periods=3).mean().fillna(50.0)

    # Williams %R
    williams_r = -100.0 * (high_14 - close) / (high_14 - low_14).replace(0, np.nan)
    df_feat["williams_r"] = williams_r.fillna(-50.0)

    # Momentum Changes
    df_feat["rsi_change_3d"] = df_feat["rsi"].diff(3).fillna(0.0)
    df_feat["macd_hist_change_3d"] = df_feat["macd_hist"].diff(3).fillna(0.0)

    # 4. Volatility Indicators
    upper, lower, width = calculate_bollinger_bands(close, 20, 2.0)
    df_feat["bb_upper"] = upper
    df_feat["bb_lower"] = lower
    df_feat["bb_width"] = width
    df_feat["rolling_volatility"] = df_feat["daily_return"].rolling(window=20, min_periods=20).std().fillna(0.0)
    df_feat["atr_14"] = calculate_atr(df_feat, 14).fillna(0.0)
    df_feat["volatility_change_5d"] = df_feat["rolling_volatility"].diff(5).fillna(0.0)

    # 5. Volume Indicators
    df_feat["volume_change"] = volume.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
    volume_sma_5 = calculate_sma(volume, 5)
    df_feat["volume_ratio_5d"] = (volume / volume_sma_5).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    
    # On-Balance Volume (OBV) slope
    obv_direction = np.sign(df_feat["daily_return"].fillna(0.0))
    obv = (obv_direction * volume).cumsum()
    df_feat["obv_slope"] = obv.pct_change(5).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # 6. Regime Indicators
    vol_med = df_feat["rolling_volatility"].rolling(window=60, min_periods=20).median()
    df_feat["volatility_regime"] = np.where(df_feat["rolling_volatility"] > vol_med, 1.0, 0.0)
    
    # Trend regime: 1 = Bull (close > sma20 > sma50), -1 = Bear (close < sma20 < sma50), 0 = Sideways
    bull_cond = (close > df_feat["sma_20"]) & (df_feat["sma_20"] > df_feat["sma_50"])
    bear_cond = (close < df_feat["sma_20"]) & (df_feat["sma_20"] < df_feat["sma_50"])
    df_feat["trend_regime"] = np.where(bull_cond, 1.0, np.where(bear_cond, -1.0, 0.0))

    # Target Construction: 1-day, 5-day, 10-day forward returns
    for h in [1, 5, 10]:
        future_close = close.shift(-h)
        col_name = f"target_{h}d" if h > 1 else "target"
        df_feat[col_name] = np.where(future_close > close, 1, 0)
        # Mark unobserved future labels as NaN
        df_feat.iloc[-h:, df_feat.columns.get_loc(col_name)] = np.nan

    # Target threshold (direction where forward 5-day return magnitude > 0.5%)
    fut_ret_5d = (close.shift(-5) - close) / close
    df_feat["target_threshold"] = np.where(fut_ret_5d > 0.005, 1, np.where(fut_ret_5d < -0.005, 0, np.nan))
    df_feat.iloc[-5:, df_feat.columns.get_loc("target_threshold")] = np.nan

    # Drop early warm-up rows where 50-day SMA is NaN
    df_clean = df_feat.dropna(subset=["sma_50"]).reset_index(drop=True)
    return df_clean

def compute_phase15_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes complete Phase 15 feature set (Phase 12 Technicals + Candlestick + Price Action + Chart Structure).
    Uses strict temporal ordering without future data leakage.
    """
    from backend.features.candlestick_features import compute_candlestick_features
    from backend.features.price_action_features import compute_price_action_features
    from backend.features.structure_features import compute_structure_features

    df_base = compute_features_and_target(df)
    if df_base.empty:
        return df_base

    df_c = compute_candlestick_features(df_base)
    df_pa = compute_price_action_features(df_c)
    df_full = compute_structure_features(df_pa)

    return df_full

