"""
StockSense AI — Backend Technical Analysis & Support/Resistance Engine
Computes SMA, EMA, VWAP, RSI, MACD, Bollinger Bands, ATR, Stochastic, ADX, OBV,
and automatic support/resistance levels from historical OHLCV data.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes full set of technical indicators on OHLCV DataFrame."""
    if df.empty or len(df) < 5:
        return df

    df_res = df.copy()
    close = df_res["close"].astype(float)
    high = df_res["high"].astype(float)
    low = df_res["low"].astype(float)
    volume = df_res["volume"].astype(float)

    # 1. Moving Averages
    df_res["sma_20"] = close.rolling(window=20, min_periods=1).mean()
    df_res["sma_50"] = close.rolling(window=50, min_periods=1).mean()
    df_res["ema_12"] = close.ewm(span=12, adjust=False).mean()
    df_res["ema_26"] = close.ewm(span=26, adjust=False).mean()

    # 2. VWAP (Volume Weighted Average Price)
    typical_price = (high + low + close) / 3.0
    cum_tp_vol = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum().replace(0, 1.0)
    df_res["vwap"] = cum_tp_vol / cum_vol

    # 3. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, 1e-9)
    df_res["rsi_14"] = 100 - (100 / (1 + rs))

    # 4. MACD (12, 26, 9)
    df_res["macd"] = df_res["ema_12"] - df_res["ema_26"]
    df_res["macd_signal"] = df_res["macd"].ewm(span=9, adjust=False).mean()
    df_res["macd_hist"] = df_res["macd"] - df_res["macd_signal"]

    # 5. Bollinger Bands (20, 2.0)
    rolling_std = close.rolling(window=20, min_periods=1).std().fillna(0)
    df_res["bollinger_middle"] = df_res["sma_20"]
    df_res["bollinger_upper"] = df_res["sma_20"] + (rolling_std * 2.0)
    df_res["bollinger_lower"] = df_res["sma_20"] - (rolling_std * 2.0)

    # 6. ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df_res["atr_14"] = tr.rolling(window=14, min_periods=1).mean()

    # 7. Stochastic Oscillator (%K=14, %D=3)
    lowest_low = low.rolling(window=14, min_periods=1).min()
    highest_high = high.rolling(window=14, min_periods=1).max()
    denom = (highest_high - lowest_low).replace(0, 1e-9)
    df_res["stoch_k"] = ((close - lowest_low) / denom) * 100.0
    df_res["stoch_d"] = df_res["stoch_k"].rolling(window=3, min_periods=1).mean()

    # 8. OBV (On-Balance Volume)
    obv_change = np.where(close > close.shift(1), volume, np.where(close < close.shift(1), -volume, 0))
    df_res["obv"] = np.cumsum(obv_change)

    return df_res

def detect_support_resistance(df: pd.DataFrame, num_pivots: int = 3) -> Dict[str, Any]:
    """Detects automatic support and resistance levels from historical price structure."""
    if df.empty or len(df) < 10:
        return {"support_levels": [], "resistance_levels": []}

    highs = df["high"].astype(float).values
    lows = df["low"].astype(float).values
    closes = df["close"].astype(float).values
    current_price = float(closes[-1])

    # Find local highs and lows (pivot points)
    pivot_highs = []
    pivot_lows = []
    window = 5

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window:i + window + 1]):
            pivot_highs.append(float(highs[i]))
        if lows[i] == min(lows[i - window:i + window + 1]):
            pivot_lows.append(float(lows[i]))

    # Filter resistance levels above current price & support levels below current price
    resistance = sorted(list(set([round(p, 2) for p in pivot_highs if p > current_price])))
    support = sorted(list(set([round(p, 2) for p in pivot_lows if p < current_price])), reverse=True)

    # Fallback to 52-week max/min if no pivots found
    if not resistance:
        resistance = [round(float(max(highs)), 2)]
    if not support:
        support = [round(float(min(lows)), 2)]

    return {
        "current_price": round(current_price, 2),
        "support_levels": support[:num_pivots],
        "resistance_levels": resistance[:num_pivots]
    }
