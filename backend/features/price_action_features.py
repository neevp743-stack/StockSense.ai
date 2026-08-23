import pandas as pd
import numpy as np

def compute_price_action_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes past-looking price action and momentum features.
    
    LEAKAGE PREVENTION RULE:
    Strictly past-looking: features at index t use ONLY observations <= t.
    """
    if df is None or df.empty or len(df) < 5:
        return df

    df_res = df.copy().sort_values("date").reset_index(drop=True)
    open_p = df_res["open"]
    high = df_res["high"]
    low = df_res["low"]
    close = df_res["close"]

    prev_high = high.shift(1)
    prev_low = low.shift(1)

    # 1. Higher High / Higher Low / Lower High / Lower Low
    hh = (high > prev_high).astype(float)
    hl = (low > prev_low).astype(float)
    lh = (high < prev_high).astype(float)
    ll = (low < prev_low).astype(float)

    df_res["higher_high"] = hh
    df_res["higher_low"] = hl
    df_res["lower_high"] = lh
    df_res["lower_low"] = ll

    df_res["higher_high_count_5d"] = hh.rolling(5, min_periods=1).sum()
    df_res["higher_low_count_5d"] = hl.rolling(5, min_periods=1).sum()
    df_res["lower_high_count_5d"] = lh.rolling(5, min_periods=1).sum()
    df_res["lower_low_count_5d"] = ll.rolling(5, min_periods=1).sum()

    # 2. Consecutive Up / Down Candles
    is_up = (close > open_p).astype(int)
    is_down = (close < open_p).astype(int)

    up_streak = []
    down_streak = []
    c_up = 0
    c_down = 0

    for u, d in zip(is_up, is_down):
        if u == 1:
            c_up += 1
            c_down = 0
        elif d == 1:
            c_down += 1
            c_up = 0
        else:
            c_up = 0
            c_down = 0
        up_streak.append(c_up)
        down_streak.append(c_down)

    df_res["consecutive_up_candles"] = pd.Series(up_streak, index=df_res.index, dtype=float)
    df_res["consecutive_down_candles"] = pd.Series(down_streak, index=df_res.index, dtype=float)

    # 3. Rolling Returns & Momentum
    df_res["rolling_return_3"] = close.pct_change(3).fillna(0.0)
    df_res["rolling_return_5"] = close.pct_change(5).fillna(0.0)
    df_res["rolling_return_10"] = close.pct_change(10).fillna(0.0)
    df_res["rolling_return_20"] = close.pct_change(20).fillna(0.0)

    df_res["momentum_3"] = close.diff(3).fillna(0.0)
    df_res["momentum_5"] = close.diff(5).fillna(0.0)
    df_res["momentum_10"] = close.diff(10).fillna(0.0)

    # 4. Moving Average Distances
    sma20 = close.rolling(20, min_periods=1).mean()
    sma50 = close.rolling(50, min_periods=1).mean()
    sma200 = close.rolling(200, min_periods=1).mean()

    df_res["price_distance_from_sma20"] = ((close - sma20) / sma20.replace(0, np.nan)).fillna(0.0)
    df_res["price_distance_from_sma50"] = ((close - sma50) / sma50.replace(0, np.nan)).fillna(0.0)
    df_res["price_distance_from_sma200"] = ((close - sma200) / sma200.replace(0, np.nan)).fillna(0.0)

    # 5. 10-day Trend Slope
    df_res["trend_slope_10d"] = ((close - close.shift(10)) / 10.0 / close.shift(10).replace(0, np.nan)).fillna(0.0)

    return df_res
