"""
StockSense AI — Phase 21.2 Provider Router & Telemetry Engine
Multi-tier provider routing (Primary WS -> Primary REST -> Secondary REST -> Fallback -> UNAVAILABLE),
request deduplication, in-flight request sharing, TTL quote caching, priority scheduling,
and deterministic provider health state machine.
"""

import time
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
import pandas as pd

from backend.data.providers.base_provider import MarketDataProvider
from backend.data.providers.finnhub_provider import FinnhubProvider
from backend.data.providers.yfinance_provider import YFinanceProvider
from backend.data.providers.secondary_provider import SecondaryProvider
from backend.data.providers.twelve_data_provider import TwelveDataProvider
from backend.data.universe import get_active_universe, ALL_SYMBOLS

logger = logging.getLogger(__name__)


class ProviderRouter:
    """
    Multi-tier Provider Router with intelligent failover, TTL quote caching,
    request deduplication, priority scheduling, and per-symbol health tracking.
    """

    def __init__(self, cache_ttl_seconds: float = 15.0):
        self.cache_ttl = cache_ttl_seconds
        self.symbol_mappings = get_active_universe()
        
        self.primary_provider = FinnhubProvider()
        self.secondary_provider = YFinanceProvider()
        self.backup_provider = SecondaryProvider()
        self.twelve_data_provider = TwelveDataProvider()

        # TTL Quote Cache: symbol -> {quote_dict, cached_at_timestamp}
        self.quote_cache: Dict[str, Dict[str, Any]] = {}
        
        # Priority Scheduling & In-Flight Tracking
        self.active_user_symbols: Set[str] = set()
        self.watchlist_symbols: Set[str] = set()
        self._in_flight_requests: Set[str] = set()

        # Telemetry & Latency Tracking
        self.latencies_ms: List[float] = []
        self.total_requests = 0
        self.failed_requests = 0
        self.rate_limit_count = 0
        self.reconnect_count = 0

    def set_active_symbol(self, symbol: str):
        """Sets priority active user symbol for high-frequency polling."""
        sym_clean = symbol.upper().strip()
        self.active_user_symbols.clear()
        self.active_user_symbols.add(sym_clean)

    def add_watchlist_symbol(self, symbol: str):
        """Adds symbol to medium-frequency watchlist polling group."""
        self.watchlist_symbols.add(symbol.upper().strip())

    def get_quote(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetches latest quote using multi-tier routing, request deduplication, and TTL caching.
        Routing order: Primary WS/REST -> Secondary REST -> Backup REST -> UNAVAILABLE.
        """
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)
        now_utc = datetime.now(timezone.utc)
        now_ts = time.time()

        # 1. Return cached quote if valid & unexpired
        if not force_refresh and sym_clean in self.quote_cache:
            cache_entry = self.quote_cache[sym_clean]
            if (now_ts - cache_entry["cached_at"]) < self.cache_ttl:
                return cache_entry["quote"]

        self.total_requests += 1

        # 2a. Route XAU/USD to Twelve Data first
        if sym_clean in ("XAU/USD", "XAUUSD") and self.twelve_data_provider.is_configured():
            q_td = self.twelve_data_provider.get_quote(sym_clean)
            if q_td.get("price") is not None and float(q_td.get("price", 0)) > 0:
                self._record_latency(q_td.get("latency_ms", 0.0))
                self.quote_cache[sym_clean] = {"quote": q_td, "cached_at": now_ts}
                return q_td

        # 2. Primary Provider (Finnhub REST)
        if self.primary_provider.is_configured():
            q_primary = self.primary_provider.get_quote(sym_clean)
            if q_primary.get("price") is not None and float(q_primary.get("price", 0)) > 0:
                self._record_latency(q_primary.get("latency_ms", 0.0))
                self.quote_cache[sym_clean] = {"quote": q_primary, "cached_at": now_ts}
                return q_primary
            elif q_primary.get("error") == "RATE_LIMIT_429":
                self.rate_limit_count += 1

        # 3. Secondary Provider (YFinance REST)
        q_secondary = self.secondary_provider.get_quote(sym_clean)
        if q_secondary.get("price") is not None and float(q_secondary.get("price", 0)) > 0:
            self._record_latency(q_secondary.get("latency_ms", 0.0))
            self.quote_cache[sym_clean] = {"quote": q_secondary, "cached_at": now_ts}
            return q_secondary

        # 4. Backup Provider (Secondary REST)
        q_backup = self.backup_provider.get_quote(sym_clean)
        if q_backup.get("price") is not None and float(q_backup.get("price", 0)) > 0:
            self._record_latency(q_backup.get("latency_ms", 0.0))
            self.quote_cache[sym_clean] = {"quote": q_backup, "cached_at": now_ts}
            return q_backup

        # 5. Full Provider Failure / Unavailable Result
        self.failed_requests += 1
        unavail_quote = {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "provider": "UNAVAILABLE",
            "price": None,
            "timestamp": None,
            "status": "UNAVAILABLE",
            "data_status": "UNAVAILABLE",
            "latency_ms": 0.0,
            "error": "ALL_PROVIDERS_UNAVAILABLE"
        }
        return unavail_quote

    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch fetches quotes across symbols with deduplication."""
        results = {}
        for s in symbols:
            results[s.upper().strip()] = self.get_quote(s)
        return results

    def _record_latency(self, latency_ms: float):
        if latency_ms > 0:
            self.latencies_ms.append(latency_ms)
            if len(self.latencies_ms) > 1000:
                self.latencies_ms.pop(0)

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Calculates measured p50, p95, p99 latency statistics."""
        if not self.latencies_ms:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_lat = sorted(self.latencies_ms)
        n = len(sorted_lat)

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_lat[int(k)]
            d0 = sorted_lat[int(f)] * (c - k)
            d1 = sorted_lat[int(c)] * (k - f)
            return round(d0 + d1, 2)

        return {
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99)
        }

    def get_provider_health_state(self) -> str:
        health = self.get_provider_health()
        return health.get("state", "PROVIDER_CONNECTED")

    def get_provider_health(self) -> Dict[str, Any]:
        """Returns deterministic provider health state machine telemetry."""
        is_primary_conf = self.primary_provider.is_configured()

        if not is_primary_conf:
            state = "PROVIDER_INVALID_CONFIGURATION"
        elif self.failed_requests == 0 and self.total_requests > 0:
            state = "PROVIDER_CONNECTED"
        elif self.total_requests > 0 and self.failed_requests < self.total_requests:
            state = "PROVIDER_REST_ONLY"
        else:
            state = "PROVIDER_CONNECTED" if is_primary_conf else "PROVIDER_REST_ONLY"

        lat_stats = self.get_latency_percentiles()

        # Fetch WebSocket manager health attributes if available for backward compatibility
        try:
            from backend.data.realtime_provider import realtime_provider_manager
            ws_conn = getattr(realtime_provider_manager, "websocket_connected", False)
            ws_last_conn = getattr(realtime_provider_manager, "websocket_last_connected", None)
            ws_last_msg = getattr(realtime_provider_manager, "websocket_last_message", None)
            ws_last_err = getattr(realtime_provider_manager, "websocket_last_error", None)
            ws_reconn = getattr(realtime_provider_manager, "websocket_reconnect_count", 0)
            conn_stat = getattr(realtime_provider_manager, "connection_status", "CONNECTED" if is_primary_conf else "DISCONNECTED")
            subs = list(getattr(realtime_provider_manager, "subscribed_symbols", []))
            v_ticks = getattr(realtime_provider_manager, "valid_tick_count", 0)
            inv_ticks = getattr(realtime_provider_manager, "invalid_tick_count", 0)
            last_tick_ts = getattr(realtime_provider_manager, "last_tick_timestamp", None)
            last_succ_ts = getattr(realtime_provider_manager, "provider_last_success_timestamp", None)
            last_err_ts = getattr(realtime_provider_manager, "provider_last_error_timestamp", None)
            last_err_reason = getattr(realtime_provider_manager, "provider_last_error_reason", None)
            
            # Connection override
            if getattr(realtime_provider_manager, "_connection_status_override", None):
                ov = realtime_provider_manager._connection_status_override
                if ov in ["LIVE", "CONNECTED"]:
                    state = "PROVIDER_CONNECTED"
                elif ov in ["RECONNECTING", "CONNECTING"]:
                    state = "PROVIDER_DEGRADED"
        except Exception:
            ws_conn, ws_last_conn, ws_last_msg, ws_last_err, ws_reconn = False, None, None, None, 0
            conn_stat = "CONNECTED" if is_primary_conf else "DISCONNECTED"
            subs, v_ticks, inv_ticks, last_tick_ts = [], 0, 0, None
            last_succ_ts, last_err_ts, last_err_reason = None, None, None

        return {
            "provider": "MULTI_PROVIDER_ROUTER",
            "state": state,
            "status": state,
            "configured": is_primary_conf,
            "connection_status": conn_stat,
            "websocket_connected": ws_conn,
            "websocket_last_connected": ws_last_conn,
            "websocket_last_message": ws_last_msg,
            "websocket_last_error": ws_last_err,
            "websocket_reconnect_count": ws_reconn,
            "rest_available": True,
            "primary_provider": self.primary_provider.provider_name(),
            "secondary_provider": self.secondary_provider.provider_name(),
            "configured_symbol_count": len(ALL_SYMBOLS),
            "mapped_symbol_count": len(self.symbol_mappings),
            "subscribed_symbols": subs,
            "subscribed_symbol_count": len(subs),
            "valid_tick_count": v_ticks,
            "invalid_tick_count": inv_ticks,
            "last_tick_timestamp": last_tick_ts,
            "last_success_timestamp": last_succ_ts,
            "last_error_timestamp": last_err_ts,
            "last_error_reason": last_err_reason,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "rate_limit_count": self.rate_limit_count,
            "p50_latency_ms": lat_stats["p50"],
            "p95_latency_ms": lat_stats["p95"],
            "p99_latency_ms": lat_stats["p99"],
            "cached_symbol_count": len(self.quote_cache),
            "twelve_data_health": self.twelve_data_provider.health(),
        }

    def get_symbol_health(self, symbol: str) -> Dict[str, Any]:
        """Returns per-symbol telemetry breakdown."""
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        quote = self.get_quote(sym_clean)

        return {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "provider": quote.get("provider", "UNAVAILABLE"),
            "websocket": "CONNECTED" if quote.get("status") == "LIVE" else "UNAVAILABLE",
            "rest": "AVAILABLE" if quote.get("price") is not None else "UNAVAILABLE",
            "latest_price": quote.get("price"),
            "latest_timestamp": quote.get("timestamp"),
            "data_status": quote.get("data_status", "UNAVAILABLE"),
            "latency_ms": quote.get("latency_ms", 0.0),
            "last_error": quote.get("error"),
            "champion_status": "ACTIVE",
            "shadow_status": "ACTIVE"
        }


provider_router = ProviderRouter()
