import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

def compute_liquidity_metrics(
    df: pd.DataFrame,
    quote_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculates genuine liquidity metrics from historical OHLCV data and live quote information.
    Does NOT fabricate bid/ask data if unavailable.
    """
    if df is None or df.empty or "volume" not in df.columns or "close" not in df.columns:
        return {
            "liquidity_tier": "LOW",
            "volume_20d_avg": 0.0,
            "volume_ratio": 1.0,
            "average_traded_value": 0.0,
            "recent_volume": 0.0,
            "bid_ask_available": False,
            "bid_ask_spread": None
        }

    df_sorted = df.sort_values("date").reset_index(drop=True)
    volumes = df_sorted["volume"].dropna().values
    closes = df_sorted["close"].dropna().values

    if len(volumes) == 0 or len(closes) == 0:
        return {
            "liquidity_tier": "LOW",
            "volume_20d_avg": 0.0,
            "volume_ratio": 1.0,
            "average_traded_value": 0.0,
            "recent_volume": 0.0,
            "bid_ask_available": False,
            "bid_ask_spread": None
        }

    recent_vol = float(volumes[-1])
    current_price = float(closes[-1])
    
    # 20-day rolling average volume
    win = min(20, len(volumes))
    vol_20d_avg = float(np.mean(volumes[-win:]))
    volume_ratio = float(recent_vol / vol_20d_avg) if vol_20d_avg > 0 else 1.0
    avg_traded_value = float(vol_20d_avg * current_price)

    # Check for genuine bid/ask spread from quote_info
    bid_ask_available = False
    bid_ask_spread = None

    if quote_info and isinstance(quote_info, dict):
        bid = quote_info.get("bid")
        ask = quote_info.get("ask")
        if bid is not None and ask is not None and isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            if bid > 0 and ask > 0 and ask >= bid and current_price > 0:
                bid_ask_available = True
                bid_ask_spread = float((ask - bid) / current_price * 100.0)

    # Liquidity Tier Classification
    if avg_traded_value >= 50_000_000 or (vol_20d_avg >= 500_000 and volume_ratio >= 0.8):
        tier = "HIGH"
    elif avg_traded_value >= 5_000_000 or (vol_20d_avg >= 100_000):
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return {
        "liquidity_tier": tier,
        "volume_20d_avg": round(vol_20d_avg, 2),
        "volume_ratio": round(volume_ratio, 4),
        "average_traded_value": round(avg_traded_value, 2),
        "recent_volume": round(recent_vol, 2),
        "bid_ask_available": bid_ask_available,
        "bid_ask_spread": round(bid_ask_spread, 4) if bid_ask_spread is not None else None
    }
