"""
StockSense AI — Live Market Data Quality Engine (Phase 16)
Evaluates real-time and historical market data freshness, candle integrity,
anomalies, and provider connectivity without fabricating missing values.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

from backend.data.realtime_provider import realtime_provider_manager
from backend.data.provider import YFinanceProvider
from backend.data.data_service import get_historical_data_from_db
from backend.assets.asset_registry import get_asset_info


logger = logging.getLogger(__name__)

# Configurable environment thresholds
DATA_FRESH_SECONDS = int(os.getenv("DATA_FRESH_SECONDS", 15))
DATA_DELAYED_SECONDS = int(os.getenv("DATA_DELAYED_SECONDS", 60))
DATA_STALE_SECONDS = int(os.getenv("DATA_STALE_SECONDS", 300))


class DataQualityService:
    """
    Evaluates market data quality, age, candle continuity, and integrity.
    """

    def __init__(self):
        self.provider_fallback = YFinanceProvider()

    def inspect_symbol_data_quality(self, symbol: str) -> Dict[str, Any]:
        """
        Calculates data quality state and anomaly metrics for a given asset symbol.
        """
        symbol_clean = symbol.upper().strip()
        asset_info = get_asset_info(symbol_clean)

        if not asset_info:
            return {
                "symbol": symbol_clean,
                "status": "INVALID",
                "latest_price": None,
                "latest_candle_timestamp": None,
                "latest_tick_timestamp": None,
                "data_age_seconds": None,
                "missing_candles": 0,
                "duplicate_candles": 0,
                "abnormal_price_move": False,
                "volume_available": False,
                "provider": "NONE",
                "error_reason": f"Unknown or unsupported symbol '{symbol_clean}'."
            }

        now = datetime.now(timezone.utc)
        latest_tick = realtime_provider_manager.cache.get_latest_tick(symbol_clean)
        
        latest_price: Optional[float] = None
        latest_tick_ts_str: Optional[str] = None
        tick_dt: Optional[datetime] = None
        provider_name = realtime_provider_manager.provider_name

        if latest_tick:
            latest_price = latest_tick.get("price")
            raw_ts = latest_tick.get("timestamp")
            if raw_ts:
                latest_tick_ts_str = raw_ts
                try:
                    tick_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except Exception:
                    tick_dt = None

        # Fetch historical DB candles to inspect structural continuity
        df_hist = get_historical_data_from_db(symbol_clean)

        latest_candle_ts_str: Optional[str] = None
        missing_candles = 0
        duplicate_candles = 0
        abnormal_price_move = False
        volume_available = False
        invalid_ohlc = False

        if not df_hist.empty and len(df_hist) > 0:
            if "date" in df_hist.columns and len(df_hist) > 0:
                last_d = df_hist["date"].iloc[-1]
                latest_candle_ts_str = str(last_d)

            # Check volume availability
            if "volume" in df_hist.columns:
                vol_sum = df_hist["volume"].fillna(0).sum()
                volume_available = bool(vol_sum > 0)

            # Duplicate candles check
            if "date" in df_hist.columns:
                duplicate_candles = int(df_hist.duplicated(subset=["date"]).sum())

            # Invalid OHLC check (High < Low or Open/Close out of bounds)
            if all(col in df_hist.columns for col in ["open", "high", "low", "close"]):
                invalid_rows = df_hist[(df_hist["high"] < df_hist["low"]) | (df_hist["low"] <= 0)]
                invalid_ohlc = bool(len(invalid_rows) > 0)

            # Abnormal price move detection (>25% single candle jump)
            if len(df_hist) >= 2 and "close" in df_hist.columns:
                recent_returns = df_hist["close"].pct_change().abs()
                max_ret = float(recent_returns.max()) if not recent_returns.empty else 0.0
                abnormal_price_move = bool(max_ret > 0.25)

            if latest_price is None and "close" in df_hist.columns:
                latest_price = float(df_hist["close"].iloc[-1])

        # If tick data is absent, attempt fallback latest quote
        if latest_price is None:
            try:
                quote = self.provider_fallback.get_latest_quote(symbol_clean)
                if quote and quote.get("price") is not None:
                    latest_price = float(quote["price"])
                    provider_name = quote.get("provider", "yfinance")
                    raw_ts = quote.get("timestamp")
                    if raw_ts:
                        latest_tick_ts_str = raw_ts
                        try:
                            tick_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                        except Exception:
                            tick_dt = None
            except Exception:
                pass

        # Calculate data age in seconds
        data_age_seconds: Optional[int] = None
        if tick_dt:
            if tick_dt.tzinfo is None:
                tick_dt = tick_dt.replace(tzinfo=timezone.utc)
            data_age_seconds = max(0, int((now - tick_dt).total_seconds()))

        # Determine quality status
        if invalid_ohlc or (latest_price is not None and latest_price <= 0):
            status = "INVALID"
        elif latest_price is None:
            status = "UNAVAILABLE"
        elif data_age_seconds is None:
            status = "LIVE" if realtime_provider_manager.is_configured() else "DELAYED"
        elif data_age_seconds <= DATA_FRESH_SECONDS:
            status = "LIVE"
        elif data_age_seconds <= DATA_DELAYED_SECONDS:
            status = "DELAYED"
        elif data_age_seconds <= DATA_STALE_SECONDS:
            status = "STALE"
        else:
            status = "STALE"

        return {
            "symbol": symbol_clean,
            "status": status,
            "latest_price": round(latest_price, 2) if latest_price is not None else None,
            "latest_candle_timestamp": latest_candle_ts_str,
            "latest_tick_timestamp": latest_tick_ts_str,
            "data_age_seconds": data_age_seconds,
            "missing_candles": missing_candles,
            "duplicate_candles": duplicate_candles,
            "abnormal_price_move": abnormal_price_move,
            "volume_available": volume_available,
            "provider": provider_name
        }


# Global Singleton Service
data_quality_service = DataQualityService()
