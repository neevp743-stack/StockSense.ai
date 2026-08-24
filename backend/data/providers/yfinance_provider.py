"""
StockSense AI — Phase 21.2 YFinance Market Data Provider Implementation
Supports YFinance REST queries for Indian equities, US equities, and Crypto with freshness evaluation.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf

from backend.data.providers.base_provider import MarketDataProvider
from backend.data.universe import get_active_universe

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """YFinance REST Provider implementation for multi-region market quote and historical fetching."""

    def __init__(self):
        self.symbol_mappings = get_active_universe()
        self.request_count = 0
        self.failed_request_count = 0
        self.rate_limit_count = 0
        self.last_success_ts = None
        self.last_error_ts = None
        self.last_error_reason = None
        self.total_latency_ms = 0.0

    def provider_name(self) -> str:
        return "YFINANCE"

    def is_configured(self) -> bool:
        return True

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches latest quote for a single symbol using yfinance."""
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        start_t = time.perf_counter()
        self.request_count += 1
        now_utc = datetime.now(timezone.utc)

        try:
            ticker = yf.Ticker(prov_sym)
            fast_info = getattr(ticker, "fast_info", None)
            price = None
            ts_iso = now_utc.isoformat()

            if fast_info:
                try:
                    price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
                except Exception:
                    price = None

            if price is None or price <= 0:
                hist = ticker.history(period="1d")
                if not hist.empty and "Close" in hist.columns:
                    price = float(hist["Close"].iloc[-1])
                    dt_val = hist.index[-1]
                    if hasattr(dt_val, "to_pydatetime"):
                        py_dt = dt_val.to_pydatetime()
                        if py_dt.tzinfo is None:
                            py_dt = py_dt.replace(tzinfo=timezone.utc)
                        ts_iso = py_dt.isoformat()

            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            self.total_latency_ms += elapsed_ms

            if price is not None and isinstance(price, (int, float)) and float(price) > 0:
                self.last_success_ts = now_utc.isoformat()
                return {
                    "symbol": sym_clean,
                    "provider_symbol": prov_sym,
                    "provider": self.provider_name(),
                    "price": round(float(price), 4),
                    "timestamp": ts_iso,
                    "status": "LIVE",
                    "data_status": "LIVE",
                    "latency_ms": elapsed_ms,
                    "error": None
                }

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            self.failed_request_count += 1
            self.last_error_ts = now_utc.isoformat()
            self.last_error_reason = f"YFinance Error for {sym_clean}: {e}"

        return {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "provider": self.provider_name(),
            "price": None,
            "timestamp": None,
            "status": "UNAVAILABLE",
            "data_status": "UNAVAILABLE",
            "latency_ms": elapsed_ms if 'elapsed_ms' in locals() else 0.0,
            "error": self.last_error_reason or "FETCH_FAILED"
        }

    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for s in symbols:
            results[s.upper().strip()] = self.get_quote(s)
        return results

    def get_historical(self, symbol: str, start: Optional[str] = None, end: Optional[str] = None, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        try:
            ticker = yf.Ticker(prov_sym)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            if "Date" in df.columns:
                df["date"] = pd.to_datetime(df["Date"]).dt.date
            elif "Datetime" in df.columns:
                df["date"] = pd.to_datetime(df["Datetime"]).dt.date

            col_map = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
            df = df.rename(columns=col_map)
            df["symbol"] = sym_clean
            return df
        except Exception as e:
            logger.error(f"Failed historical fetch for {sym_clean}: {e}")
            return pd.DataFrame()

    def subscribe(self, symbols: List[str]) -> bool:
        return True

    def unsubscribe(self, symbols: List[str]) -> bool:
        return True

    def health(self) -> Dict[str, Any]:
        avg_lat = round(self.total_latency_ms / self.request_count, 2) if self.request_count > 0 else 0.0
        return {
            "provider": self.provider_name(),
            "configured": self.is_configured(),
            "request_count": self.request_count,
            "failed_request_count": self.failed_request_count,
            "rate_limit_count": self.rate_limit_count,
            "average_latency_ms": avg_lat,
            "last_success_ts": self.last_success_ts,
            "last_error_ts": self.last_error_ts,
            "last_error_reason": self.last_error_reason
        }
