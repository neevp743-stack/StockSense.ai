"""
StockSense AI — Phase 21.2 Secondary Market Data Provider Backup Implementation
Serves as backup secondary provider interface for REST fallback quote querying.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from backend.data.providers.base_provider import MarketDataProvider
from backend.data.universe import get_active_universe

logger = logging.getLogger(__name__)


class SecondaryProvider(MarketDataProvider):
    """Secondary Provider backup implementation for multi-tier provider routing failover."""

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
        return "SECONDARY"

    def is_configured(self) -> bool:
        return True

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Secondary fallback query handler."""
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        start_t = time.perf_counter()
        self.request_count += 1
        now_utc = datetime.now(timezone.utc)

        # Delegate to secondary YFinance query fallback
        from backend.data.providers.yfinance_provider import YFinanceProvider
        yf_prov = YFinanceProvider()
        quote = yf_prov.get_quote(sym_clean)

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        self.total_latency_ms += elapsed_ms

        if quote.get("price") is not None and float(quote.get("price", 0)) > 0:
            self.last_success_ts = now_utc.isoformat()
            return {
                "symbol": sym_clean,
                "provider_symbol": prov_sym,
                "provider": self.provider_name(),
                "price": round(float(quote["price"]), 4),
                "timestamp": quote.get("timestamp", now_utc.isoformat()),
                "status": "LIVE",
                "data_status": "LIVE",
                "latency_ms": elapsed_ms,
                "error": None
            }

        self.failed_request_count += 1
        self.last_error_ts = now_utc.isoformat()
        self.last_error_reason = f"Secondary fetch unavailable for {sym_clean}"

        return {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "provider": self.provider_name(),
            "price": None,
            "timestamp": None,
            "status": "UNAVAILABLE",
            "data_status": "UNAVAILABLE",
            "latency_ms": elapsed_ms,
            "error": self.last_error_reason
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
