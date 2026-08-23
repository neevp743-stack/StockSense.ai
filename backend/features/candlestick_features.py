import pandas as pd
import numpy as np
from typing import Dict, Any, List

def compute_candlestick_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes past-looking candle geometry, pattern detectors, and pattern strength features.
    
    LEAKAGE PREVENTION RULE:
    1. Calculations at index t use ONLY rows <= t.
    2. Future close/high/low prices are NEVER accessed.
    3. Handles division by zero, NaNs, and extreme values safely.
    """
    if df is None or df.empty or len(df) < 5:
        return df

    df_res = df.copy().sort_values("date").reset_index(drop=True)
    open_p = df_res["open"]
    high = df_res["high"]
    low = df_res["low"]
    close = df_res["close"]
    volume = df_res["volume"] if "volume" in df_res.columns else pd.Series(1.0, index=df_res.index)

    # 1. Candle Geometry Features
    body = close - open_p
    body_abs = body.abs()
    candle_range = (high - low).replace(0, np.nan)

    upper_wick = high - np.maximum(open_p, close)
    lower_wick = np.minimum(open_p, close) - low

    df_res["body_abs"] = body_abs
    df_res["candle_range"] = candle_range.fillna(0.01)

    df_res["body_ratio"] = (body_abs / candle_range).fillna(0.0).clip(0.0, 1.0)
    df_res["upper_wick_ratio"] = (upper_wick / candle_range).fillna(0.0).clip(0.0, 1.0)
    df_res["lower_wick_ratio"] = (lower_wick / candle_range).fillna(0.0).clip(0.0, 1.0)

    df_res["close_position_in_range"] = ((close - low) / candle_range).fillna(0.5).clip(0.0, 1.0)

    prev_close = close.shift(1).replace(0, np.nan)
    df_res["open_close_change_percent"] = ((close - open_p) / open_p.replace(0, np.nan) * 100.0).fillna(0.0)
    df_res["high_low_range_percent"] = ((high - low) / low.replace(0, np.nan) * 100.0).fillna(0.0)

    df_res["bullish_candle"] = (close > open_p).astype(float)
    df_res["bearish_candle"] = (close < open_p).astype(float)

    df_res["gap_percent"] = ((open_p - prev_close) / prev_close * 100.0).fillna(0.0)

    # 2. Deterministic Pattern Detection (0 or 1)
    # Doji: body is <= 10% of total candle range
    df_res["pattern_doji"] = (df_res["body_ratio"] <= 0.10).astype(float)

    # Hammer: small body in upper 30% of range, lower wick >= 2x body
    is_hammer = (df_res["close_position_in_range"] >= 0.70) & (lower_wick >= 1.8 * body_abs) & (body_abs > 0)
    df_res["pattern_hammer"] = is_hammer.astype(float)

    # Inverted Hammer: small body in lower 30% of range, upper wick >= 2x body
    is_inv_hammer = (df_res["close_position_in_range"] <= 0.30) & (upper_wick >= 1.8 * body_abs) & (body_abs > 0)
    df_res["pattern_inverted_hammer"] = is_inv_hammer.astype(float)

    # Shooting Star: small body in lower 35% of range after uptrend
    is_shooting_star = (df_res["close_position_in_range"] <= 0.35) & (upper_wick >= 1.8 * body_abs)
    df_res["pattern_shooting_star"] = is_shooting_star.astype(float)

    # Hanging Man: small body in upper 35% of range with long lower wick
    is_hanging_man = (df_res["close_position_in_range"] >= 0.65) & (lower_wick >= 1.8 * body_abs)
    df_res["pattern_hanging_man"] = is_hanging_man.astype(float)

    # Bullish Engulfing: prev candle bearish, curr candle bullish engulfing prev body
    prev_open = open_p.shift(1)
    prev_close_val = close.shift(1)
    is_bull_engulf = (prev_close_val < prev_open) & (close > prev_open) & (open_p <= prev_close_val)
    df_res["pattern_bullish_engulfing"] = is_bull_engulf.fillna(False).astype(float)

    # Bearish Engulfing: prev candle bullish, curr candle bearish engulfing prev body
    is_bear_engulf = (prev_close_val > prev_open) & (close < prev_open) & (open_p >= prev_close_val)
    df_res["pattern_bearish_engulfing"] = is_bear_engulf.fillna(False).astype(float)

    # Harami Patterns
    is_bull_harami = (prev_close_val < prev_open) & (close > open_p) & (open_p >= prev_close_val) & (close <= prev_open)
    is_bear_harami = (prev_close_val > prev_open) & (close < open_p) & (open_p <= prev_close_val) & (close >= prev_open)
    df_res["pattern_bullish_harami"] = is_bull_harami.fillna(False).astype(float)
    df_res["pattern_bearish_harami"] = is_bear_harami.fillna(False).astype(float)
    df_res["pattern_harami"] = (is_bull_harami | is_bear_harami).fillna(False).astype(float)

    # Morning Star (3-candle bullish reversal)
    prev2_open = open_p.shift(2)
    prev2_close = close.shift(2)
    is_mstar = (prev2_close < prev2_open) & (df_res["body_ratio"].shift(1) <= 0.2) & (close > (prev2_open + prev2_close) / 2.0)
    df_res["pattern_morning_star"] = is_mstar.fillna(False).astype(float)

    # Evening Star (3-candle bearish reversal)
    is_estar = (prev2_close > prev2_open) & (df_res["body_ratio"].shift(1) <= 0.2) & (close < (prev2_open + prev2_close) / 2.0)
    df_res["pattern_evening_star"] = is_estar.fillna(False).astype(float)

    # Marubozu: body ratio >= 85% of total range
    df_res["pattern_marubozu"] = (df_res["body_ratio"] >= 0.85).astype(float)

    # 3. Pattern Strength Features
    vol_sma5 = volume.rolling(window=5, min_periods=1).mean()
    df_res["pattern_body_strength"] = (body_abs / candle_range).fillna(0.0)
    df_res["pattern_volume_confirmation"] = (volume / vol_sma5.replace(0, np.nan)).fillna(1.0).clip(0.1, 5.0)
    df_res["pattern_range_strength"] = (candle_range / candle_range.rolling(window=10, min_periods=1).mean().replace(0, np.nan)).fillna(1.0)

    return df_res
