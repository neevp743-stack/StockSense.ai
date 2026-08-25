"""
StockSense AI — Phase 21.4 Twelve Data Provider for XAU/USD
REST-based market data provider for gold (XAU/USD) pricing.
API key is read from environment variable TWELVE_DATA_API_KEY — never hard-coded or exposed.
"""

import time
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from backend.data.providers.base_provider import MarketDataProvider

logger = logging.getLogger(__name__)

# Twelve Data REST API base
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"


class TwelveDataProvider(MarketDataProvider):
    """
    Twelve Data REST provider for XAU/USD (Gold) market data.
    Reads API key from environment via backend.config.TWELVE_DATA_API_KEY.
    Never exposes, logs, or returns the API key.
    Implements request timeout, retry/backoff, rate-limit handling, and bounded caching.
    """

    # Symbols this provider is authoritative for
    SUPPORTED_SYMBOLS = {"XAU/USD", "XAUUSD"}

    def __init__(self, api_key: Optional[str] = None):
        from backend.config import TWELVE_DATA_API_KEY
        self._api_key = api_key if api_key is not None else TWELVE_DATA_API_KEY

        # Telemetry
        self.request_count = 0
        self.failed_request_count = 0
        self.rate_limit_count = 0
        self.last_success_ts: Optional[str] = None
        self.last_error_ts: Optional[str] = None
        self.last_error_reason: Optional[str] = None
        self.total_latency_ms: float = 0.0

        # Bounded quote cache: symbol -> {quote, cached_at}
        self._quote_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds: float = 30.0  # 30 seconds TTL

    def provider_name(self) -> str:
        return "TWELVE_DATA"

    def is_configured(self) -> bool:
        """Returns True if the API key is present and non-placeholder."""
        return bool(
            self._api_key
            and isinstance(self._api_key, str)
            and len(self._api_key.strip()) > 5
            and not self._api_key.startswith("your_")
        )

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalizes symbol to Twelve Data format.
        XAU/USD and XAUUSD both map to 'XAU/USD' for the API.
        """
        sym_clean = symbol.upper().strip()
        if sym_clean == "XAUUSD":
            return "XAU/USD"
        return sym_clean

    @staticmethod
    def internal_symbol(symbol: str) -> str:
        """Returns the StockSense internal symbol representation."""
        sym_clean = symbol.upper().strip()
        if sym_clean == "XAUUSD":
            return "XAU/USD"
        return sym_clean

    def _is_supported(self, symbol: str) -> bool:
        """Checks if symbol is within this provider's coverage."""
        return symbol.upper().strip() in self.SUPPORTED_SYMBOLS or self.normalize_symbol(symbol) in self.SUPPORTED_SYMBOLS

    def _fetch_json(self, url: str, timeout: int = 8) -> Optional[dict]:
        """
        Makes an HTTP GET request with timeout and retry/backoff.
        Never includes the API key in logs or error messages.
        Returns parsed JSON or None on failure.
        """
        max_retries = 2
        backoff = [1, 3]

        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "StockSenseAI/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status == 429:
                        self.rate_limit_count += 1
                        self.last_error_reason = "RATE_LIMIT_429"
                        if attempt < max_retries:
                            time.sleep(backoff[min(attempt, len(backoff) - 1)])
                            continue
                        return None

                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        # Twelve Data returns {"status": "error"} on API errors
                        if data.get("status") == "error":
                            self.last_error_reason = data.get("message", "API_ERROR")
                            return None
                        return data

            except urllib.error.HTTPError as he:
                if he.code == 429:
                    self.rate_limit_count += 1
                    self.last_error_reason = "RATE_LIMIT_429"
                else:
                    self.last_error_reason = f"HTTPError {he.code}"
                if attempt < max_retries:
                    time.sleep(backoff[min(attempt, len(backoff) - 1)])
                    continue
            except Exception as e:
                self.last_error_reason = f"FetchError: {type(e).__name__}"
                if attempt < max_retries:
                    time.sleep(backoff[min(attempt, len(backoff) - 1)])
                    continue

        return None

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches latest XAU/USD price from Twelve Data REST API.
        Returns normalized quote dict compatible with StockSense provider interface.
        """
        sym_clean = self.normalize_symbol(symbol)
        internal_sym = self.internal_symbol(symbol)
        now_utc = datetime.now(timezone.utc)
        start_t = time.perf_counter()
        self.request_count += 1

        if not self.is_configured():
            return {
                "symbol": internal_sym,
                "provider_symbol": sym_clean,
                "provider": self.provider_name(),
                "price": None,
                "timestamp": None,
                "status": "UNAVAILABLE",
                "data_status": "UNAVAILABLE",
                "latency_ms": 0.0,
                "error": "TWELVE_DATA_API_KEY_NOT_CONFIGURED"
            }

        # Check cache
        cache_entry = self._quote_cache.get(internal_sym)
        if cache_entry:
            age = time.time() - cache_entry["cached_at"]
            if age < self._cache_ttl_seconds:
                return cache_entry["quote"]

        # Build URL — API key is appended as query param, never logged
        url = f"{TWELVE_DATA_BASE_URL}/price?symbol={sym_clean}&apikey={self._api_key.strip()}"

        data = self._fetch_json(url)
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        self.total_latency_ms += elapsed_ms

        if data and "price" in data:
            try:
                price = float(data["price"])
                if price > 0:
                    self.last_success_ts = now_utc.isoformat()
                    quote = {
                        "symbol": internal_sym,
                        "provider_symbol": sym_clean,
                        "provider": self.provider_name(),
                        "price": round(price, 4),
                        "timestamp": now_utc.isoformat(),
                        "status": "LIVE",
                        "data_status": "LIVE",
                        "latency_ms": elapsed_ms,
                        "error": None
                    }
                    self._quote_cache[internal_sym] = {"quote": quote, "cached_at": time.time()}

                    # Feed into LiveTickCache
                    try:
                        from backend.data.realtime_provider import realtime_provider_manager
                        realtime_provider_manager.process_incoming_tick(
                            symbol=internal_sym,
                            price=price,
                            provider="TWELVE_DATA"
                        )
                    except Exception:
                        pass

                    return quote
            except (ValueError, TypeError):
                pass

        self.failed_request_count += 1
        self.last_error_ts = now_utc.isoformat()
        return {
            "symbol": internal_sym,
            "provider_symbol": sym_clean,
            "provider": self.provider_name(),
            "price": None,
            "timestamp": None,
            "status": "UNAVAILABLE",
            "data_status": "UNAVAILABLE",
            "latency_ms": elapsed_ms if 'elapsed_ms' in locals() else 0.0,
            "error": self.last_error_reason or "FETCH_FAILED"
        }

    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch fetches quotes for multiple symbols."""
        results = {}
        for s in symbols:
            results[self.internal_symbol(s)] = self.get_quote(s)
        return results

    def get_historical(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "5y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV data for XAU/USD from Twelve Data.
        Returns standardized DataFrame with columns: date, open, high, low, close, volume.
        """
        if not self.is_configured():
            return pd.DataFrame()

        sym_clean = self.normalize_symbol(symbol)

        # Map period to Twelve Data outputsize
        period_map = {"1y": 252, "2y": 504, "5y": 1260}
        outputsize = period_map.get(period, 252)

        # Map interval
        interval_map = {"1d": "1day", "1h": "1h", "4h": "4h", "1w": "1week"}
        td_interval = interval_map.get(interval, "1day")

        url = (
            f"{TWELVE_DATA_BASE_URL}/time_series?"
            f"symbol={sym_clean}&interval={td_interval}&outputsize={outputsize}"
            f"&apikey={self._api_key.strip()}"
        )

        data = self._fetch_json(url, timeout=15)
        if not data or "values" not in data:
            return pd.DataFrame()

        try:
            rows = []
            for v in data["values"]:
                rows.append({
                    "date": pd.to_datetime(v.get("datetime")).date(),
                    "open": float(v.get("open", 0)),
                    "high": float(v.get("high", 0)),
                    "low": float(v.get("low", 0)),
                    "close": float(v.get("close", 0)),
                    "volume": float(v.get("volume", 0)),
                })
            df = pd.DataFrame(rows)
            if not df.empty:
                df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            logger.warning(f"Twelve Data historical parse error: {e}")
            return pd.DataFrame()

    def subscribe(self, symbols: List[str]) -> bool:
        """Twelve Data is REST-only, no WebSocket subscriptions."""
        return True

    def unsubscribe(self, symbols: List[str]) -> bool:
        """Twelve Data is REST-only, no WebSocket subscriptions."""
        return True

    def health(self) -> Dict[str, Any]:
        """
        Returns provider health telemetry.
        NEVER includes API key or any secrets.
        """
        avg_lat = round(self.total_latency_ms / self.request_count, 2) if self.request_count > 0 else 0.0
        return {
            "provider": self.provider_name(),
            "configured": self.is_configured(),
            "supported_symbols": list(self.SUPPORTED_SYMBOLS),
            "request_count": self.request_count,
            "failed_request_count": self.failed_request_count,
            "rate_limit_count": self.rate_limit_count,
            "average_latency_ms": avg_lat,
            "last_success_ts": self.last_success_ts,
            "last_error_ts": self.last_error_ts,
            "last_error_reason": self.last_error_reason,
            "cache_entries": len(self._quote_cache),
        }
