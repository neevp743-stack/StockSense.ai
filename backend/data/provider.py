"""
StockSense AI — Market Data Provider Abstraction & Freshness Engine
Supports historical data fetching, latest quote retrieval, dynamic freshness evaluation,
and controlled real-time streaming sockets.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf
from backend.assets.asset_registry import get_asset_info

class MarketDataProvider(ABC):
    """Abstract Base Class for Multi-Asset Market Data Providers."""

    @abstractmethod
    def get_historical_data(self, symbol: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
        """Fetches historical OHLCV data strictly for DB storage, training, and backtesting."""
        pass

    @abstractmethod
    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches latest quote with timestamp, provider name, and dynamic data freshness status."""
        pass

    @abstractmethod
    def get_realtime_stream(self, symbol: str) -> Dict[str, Any]:
        """Optional socket hook for real-time streaming feeds."""
        pass


class YFinanceProvider(MarketDataProvider):
    """
    Yahoo Finance provider implementation.
    Evaluates quote freshness dynamically. Labels data as DELAYED or HISTORICAL.
    Never fabricates LIVE websocket status.
    """

    def get_historical_data(self, symbol: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
        asset_info = get_asset_info(symbol)
        provider_ticker = asset_info["provider_symbol"] if asset_info else symbol

        try:
            ticker = yf.Ticker(provider_ticker)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return pd.DataFrame()

            df = df.reset_index()
            # Standardize date column
            if "Date" in df.columns:
                df["date"] = pd.to_datetime(df["Date"]).dt.date
            elif "Datetime" in df.columns:
                df["date"] = pd.to_datetime(df["Datetime"]).dt.date

            # Standardize lower-case OHLCV columns
            column_map = {
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume"
            }
            df = df.rename(columns=column_map)

            # Ensure all required columns exist
            for col in ["open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    df[col] = 0.0

            req_cols = ["date", "open", "high", "low", "close", "volume"]
            return df[req_cols].dropna(subset=["date", "close"])
        except Exception as e:
            print(f"Error fetching historical data for '{symbol}' ({provider_ticker}): {e}")
            return pd.DataFrame()

    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        asset_info = get_asset_info(symbol)
        provider_ticker = asset_info["provider_symbol"] if asset_info else symbol
        tz_str = asset_info.get("timezone", "UTC") if asset_info else "UTC"

        now_utc = datetime.now(timezone.utc)

        try:
            ticker = yf.Ticker(provider_ticker)
            fast_info = getattr(ticker, "fast_info", {})
            last_price = fast_info.get("lastPrice", None)
            
            if last_price is None or pd.isna(last_price):
                # Fallback to history tail
                df = ticker.history(period="5d", interval="1d")
                if df.empty:
                    return {
                        "symbol": symbol,
                        "provider": "yfinance",
                        "price": None,
                        "timestamp": str(now_utc.isoformat()),
                        "timezone": tz_str,
                        "data_status": "UNAVAILABLE",
                        "is_delayed": True,
                        "message": "Market data unavailable from provider."
                    }
                last_price = float(df["Close"].iloc[-1])
                last_dt = df.index[-1]
                quote_ts = last_dt.to_pydatetime() if hasattr(last_dt, "to_pydatetime") else now_utc
            else:
                last_price = float(last_price)
                quote_ts = now_utc

            # Dynamic Freshness Evaluation:
            # yfinance tickers are at best 15-min delayed or daily historical bar closes.
            # We determine DELAYED vs HISTORICAL vs UNAVAILABLE based on age.
            if hasattr(quote_ts, "tzinfo") and quote_ts.tzinfo is not None:
                age_seconds = (now_utc - quote_ts.astimezone(timezone.utc)).total_seconds()
            else:
                age_seconds = 3600  # Default assume historical if naive

            if age_seconds < 86400:  # Within 24h -> DELAYED quote
                status = "DELAYED"
            else:
                status = "HISTORICAL"

            return {
                "symbol": symbol,
                "provider": "yfinance",
                "price": round(last_price, 4),
                "timestamp": quote_ts.isoformat() if hasattr(quote_ts, "isoformat") else str(quote_ts),
                "timezone": tz_str,
                "data_status": status,
                "is_delayed": True,
                "last_updated": now_utc.strftime("%H:%M:%S UTC")
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "provider": "yfinance",
                "price": None,
                "timestamp": now_utc.isoformat(),
                "timezone": tz_str,
                "data_status": "UNAVAILABLE",
                "is_delayed": True,
                "error": str(e)
            }

    def get_realtime_stream(self, symbol: str) -> Dict[str, Any]:
        """Explicitly reports that YFinanceProvider does NOT support real-time WebSocket streaming."""
        return {
            "symbol": symbol,
            "provider": "yfinance",
            "data_status": "UNAVAILABLE",
            "streaming_supported": False,
            "message": "Real-time streaming is unsupported by YFinanceProvider. Attach licensed WebSocket provider for LIVE streams."
        }
