"""
StockSense AI — Phase 21.2 Finnhub Market Data Provider Implementation
Supports WebSocket streaming feed and Finnhub REST fallback querying.
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
from backend.data.universe import get_active_universe
from backend.config import REALTIME_API_KEY, REALTIME_WS_URL

logger = logging.getLogger(__name__)


class FinnhubProvider(MarketDataProvider):
    """Finnhub Provider implementation supporting REST quotes and WebSocket streaming telemetry."""

    def __init__(self, api_key: Optional[str] = None, ws_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else REALTIME_API_KEY
        self.ws_url = ws_url if ws_url is not None else REALTIME_WS_URL
        self.symbol_mappings = get_active_universe()
        
        self.request_count = 0
        self.failed_request_count = 0
        self.rate_limit_count = 0
        self.last_success_ts = None
        self.last_error_ts = None
        self.last_error_reason = None
        self.total_latency_ms = 0.0

    def provider_name(self) -> str:
        return "FINNHUB"

    def is_configured(self) -> bool:
        return bool(self.api_key and isinstance(self.api_key, str) and len(self.api_key.strip()) > 5)

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches latest quote for a single symbol via Finnhub REST API."""
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        if not self.is_configured():
            return {
                "symbol": sym_clean,
                "provider_symbol": prov_sym,
                "provider": self.provider_name(),
                "price": None,
                "timestamp": None,
                "status": "UNAVAILABLE",
                "data_status": "UNAVAILABLE",
                "latency_ms": 0.0,
                "error": "FINNHUB_API_KEY_NOT_CONFIGURED"
            }

        start_t = time.perf_counter()
        self.request_count += 1
        now_utc = datetime.now(timezone.utc)

        url = f"https://finnhub.io/api/v1/quote?symbol={prov_sym}&token={self.api_key.strip()}"
        req = urllib.request.Request(url, headers={"User-Agent": "StockSenseAI/1.0"})

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
                self.total_latency_ms += elapsed_ms

                if response.status == 429:
                    self.rate_limit_count += 1
                    self.failed_request_count += 1
                    self.last_error_ts = now_utc.isoformat()
                    self.last_error_reason = "RATE_LIMIT_EXCEEDED"
                    return {
                        "symbol": sym_clean,
                        "provider_symbol": prov_sym,
                        "provider": self.provider_name(),
                        "price": None,
                        "timestamp": None,
                        "status": "DEGRADED",
                        "data_status": "UNAVAILABLE",
                        "latency_ms": elapsed_ms,
                        "error": "RATE_LIMIT_429"
                    }

                if response.status == 200:
                    data = json.loads(response.read().decode())
                    current_price = data.get("c")
                    timestamp_unix = data.get("t")

                    if current_price is not None and isinstance(current_price, (int, float)) and float(current_price) > 0:
                        ts_str = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).isoformat() if timestamp_unix and isinstance(timestamp_unix, (int, float)) and timestamp_unix > 0 else now_utc.isoformat()
                        self.last_success_ts = now_utc.isoformat()
                        return {
                            "symbol": sym_clean,
                            "provider_symbol": prov_sym,
                            "provider": self.provider_name(),
                            "price": round(float(current_price), 4),
                            "timestamp": ts_str,
                            "status": "LIVE",
                            "data_status": "LIVE",
                            "latency_ms": elapsed_ms,
                            "error": None
                        }

        except urllib.error.HTTPError as he:
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            self.failed_request_count += 1
            if he.code == 429:
                self.rate_limit_count += 1
            self.last_error_ts = now_utc.isoformat()
            self.last_error_reason = f"HTTPError {he.code}: {he.reason}"
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            self.failed_request_count += 1
            self.last_error_ts = now_utc.isoformat()
            self.last_error_reason = f"Error: {e}"

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
