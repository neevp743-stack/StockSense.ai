import pandas as pd
import numpy as np
from typing import Dict, Any

def compute_structure_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes past-looking chart structure, support/resistance, breakout, volatility structure,
    and regime interaction features.
    
    LEAKAGE PREVENTION RULE:
    1. Strictly past-looking: features at index t use ONLY observations <= t.
    2. Swing levels and breakout thresholds at index t are computed using observations BEFORE index t (shift(1)).
    """
    if df is None or df.empty or len(df) < 5:
        return df

    df_res = df.copy().sort_values("date").reset_index(drop=True)
    open_p = df_res["open"]
    high = df_res["high"]
    low = df_res["low"]
    close = df_res["close"]
    volume = df_res["volume"] if "volume" in df_res.columns else pd.Series(1.0, index=df_res.index)

    # 1. Support & Resistance (Swing High / Swing Low using past 20 days)
    # Important: shift(1) prevents using current candle's high/low to define the target resistance
    swing_high_20 = high.shift(1).rolling(20, min_periods=5).max()
    swing_low_20 = low.shift(1).rolling(20, min_periods=5).min()

    swing_high_50 = high.shift(1).rolling(50, min_periods=10).max()
    swing_low_50 = low.shift(1).rolling(50, min_periods=10).min()

    df_res["recent_swing_high"] = swing_high_20.fillna(high)
    df_res["recent_swing_low"] = swing_low_20.fillna(low)

    df_res["distance_from_support"] = ((close - df_res["recent_swing_low"]) / close.replace(0, np.nan)).fillna(0.0)
    df_res["distance_from_resistance"] = ((df_res["recent_swing_high"] - close) / close.replace(0, np.nan)).fillna(0.0)

    df_res["distance_from_20d_high"] = ((swing_high_20 - close) / close.replace(0, np.nan)).fillna(0.0)
    df_res["distance_from_20d_low"] = ((close - swing_low_20) / close.replace(0, np.nan)).fillna(0.0)
    df_res["distance_from_50d_high"] = ((swing_high_50 - close) / close.replace(0, np.nan)).fillna(0.0)
    df_res["distance_from_50d_low"] = ((close - swing_low_50) / close.replace(0, np.nan)).fillna(0.0)

    # Support & Resistance strength (count of touches within 1.5% in last 20 days)
    near_supp = ((low - swing_low_20).abs() / close <= 0.015).astype(float)
    near_res = ((high - swing_high_20).abs() / close <= 0.015).astype(float)

    df_res["support_strength"] = near_supp.shift(1).rolling(20, min_periods=1).sum().fillna(0.0)
    df_res["resistance_strength"] = near_res.shift(1).rolling(20, min_periods=1).sum().fillna(0.0)

    # 2. Breakout Features
    # Breakout up: close breaks above past 20-day high
    breakout_up = (close > swing_high_20).astype(float)
    breakout_down = (close < swing_low_20).astype(float)

    df_res["breakout_up"] = breakout_up
    df_res["breakout_down"] = breakout_down

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.rolling(14, min_periods=1).mean().fillna(0.01)

    df_res["breakout_strength"] = pd.Series(np.where(
        breakout_up == 1.0,
        (close - swing_high_20) / atr14.replace(0, np.nan),
        np.where(breakout_down == 1.0, (swing_low_20 - close) / atr14.replace(0, np.nan), 0.0)
    ), index=df_res.index).fillna(0.0)


    vol_sma20 = volume.rolling(20, min_periods=1).mean()
    vol_ratio = (volume / vol_sma20.replace(0, np.nan)).fillna(1.0)
    df_res["volume_breakout_ratio"] = vol_ratio

    candle_range = high - low
    range_avg20 = candle_range.rolling(20, min_periods=1).mean()
    df_res["range_expansion"] = (candle_range / range_avg20.replace(0, np.nan)).fillna(1.0)

    df_res["close_above_resistance"] = breakout_up
    df_res["close_below_support"] = breakout_down

    # False breakout candidate: breakout occurs on low volume (volume ratio < 0.85)
    df_res["false_breakout_candidate"] = (((breakout_up == 1.0) | (breakout_down == 1.0)) & (vol_ratio < 0.85)).astype(float)


    # 3. Consolidation / Volatility Structure
    atr10 = tr.rolling(10, min_periods=1).mean()
    df_res["range_compression"] = (atr10 < atr14).astype(float)

    vol20 = close.pct_change().rolling(20, min_periods=1).std()
    vol50 = close.pct_change().rolling(50, min_periods=1).std()
    vol60 = close.pct_change().rolling(60, min_periods=1).std()

    df_res["volatility_contraction"] = (vol20 / vol60.replace(0, np.nan)).fillna(1.0)
    df_res["volatility_expansion"] = (vol20 / vol50.replace(0, np.nan)).fillna(1.0)
    df_res["atr_relative_to_price"] = (atr14 / close.replace(0, np.nan)).fillna(0.0)

    # 4. Candle + Regime Interaction Features
    bull_eng = df_res.get("pattern_bullish_engulfing", pd.Series(0.0, index=df_res.index))
    bear_eng = df_res.get("pattern_bearish_engulfing", pd.Series(0.0, index=df_res.index))
    hammer = df_res.get("pattern_hammer", pd.Series(0.0, index=df_res.index))
    shooting_star = df_res.get("pattern_shooting_star", pd.Series(0.0, index=df_res.index))

    # Trend regime (bull = 1, bear = -1)
    sma20 = close.rolling(20, min_periods=1).mean()
    sma50 = close.rolling(50, min_periods=1).mean()
    bull_regime = ((close > sma20) & (sma20 > sma50)).astype(float)
    bear_regime = ((close < sma20) & (sma20 < sma50)).astype(float)

    df_res["bullish_engulfing_in_bull_regime"] = (bull_eng * bull_regime).astype(float)
    df_res["bearish_engulfing_in_bear_regime"] = (bear_eng * bear_regime).astype(float)
    df_res["hammer_near_support"] = (hammer * (df_res["distance_from_support"] < 0.015).astype(float)).astype(float)
    df_res["shooting_star_near_resistance"] = (shooting_star * (df_res["distance_from_resistance"] < 0.015).astype(float)).astype(float)
    df_res["breakout_in_high_volume"] = (breakout_up * (vol_ratio > 1.5).astype(float)).astype(float)

    return df_res
