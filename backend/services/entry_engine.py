import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Calculates Average True Range (ATR) from OHLC dataframe."""
    if df is None or df.empty or len(df) < 2:
        return 1.0

    df_res = df.copy().sort_values("date").reset_index(drop=True)
    high = df_res["high"].values
    low = df_res["low"].values
    close = df_res["close"].values

    tr_list = []
    for i in range(1, len(df_res)):
        h = high[i]
        l = low[i]
        prev_c = close[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

    if not tr_list:
        return float(close[-1] * 0.02)

    atr_series = pd.Series(tr_list).rolling(window=min(period, len(tr_list)), min_periods=1).mean()
    return float(atr_series.iloc[-1])

def calculate_entry_zone(
    current_price: float,
    signal: str,
    df_history: pd.DataFrame,
    atr_multiplier: float = 0.5
) -> Dict[str, Any]:
    """
    Computes deterministic entry zone [entry_low, entry_high] based on current price,
    ATR volatility buffer, and recent support/resistance structure.
    Enforces entry_low <= entry_high.
    """
    if current_price <= 0:
        return {
            "entry_low": 0.0,
            "entry_high": 0.0,
            "entry_method": "INVALID_PRICE"
        }

    atr = calculate_atr(df_history, period=14)
    buffer = max(atr * atr_multiplier, current_price * 0.002)  # Minimum 0.2% price buffer

    # Calculate recent 20-period support and resistance
    if df_history is not None and not df_history.empty and len(df_history) >= 10:
        recent = df_history.iloc[-20:]
        recent_low = float(recent["low"].min())
        recent_high = float(recent["high"].max())
    else:
        recent_low = current_price * 0.95
        recent_high = current_price * 1.05

    if signal == "BUY":
        # Entry zone for long: slightly below or at current price down to ATR buffer
        entry_high = current_price
        entry_low = max(current_price - buffer, recent_low)
        if entry_low > entry_high:
            entry_low = current_price - buffer
        entry_method = "ATR Pullback + Current Close Buffer"
    elif signal == "SELL":
        # Entry zone for short: at current price up to ATR buffer
        entry_low = current_price
        entry_high = min(current_price + buffer, recent_high)
        if entry_high < entry_low:
            entry_high = current_price + buffer
        entry_method = "ATR Relief Rally + Current Close Buffer"
    else: # HOLD
        entry_low = current_price
        entry_high = current_price
        entry_method = "Neutral Current Close"

    # Enforce strictly entry_low <= entry_high
    if entry_low > entry_high:
        entry_low, entry_high = entry_high, entry_low

    return {
        "entry_low": round(float(entry_low), 2),
        "entry_high": round(float(entry_high), 2),
        "entry_method": entry_method
    }
