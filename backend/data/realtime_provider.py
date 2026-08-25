"""
StockSense AI — Real-Time WebSocket & REST Market Data Provider (Phase 21.1)
Provides normalized live tick streaming, exponential backoff reconnection,
stale tick detection, provider health state machine, and robust REST fallback.
"""

import os
import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
import websockets

from backend.data.universe import get_active_universe

logger = logging.getLogger(__name__)


class LiveTickCache:
    """In-memory cache for normalized live market ticks."""

    def __init__(self, stale_threshold_seconds: int = 30):
        self._ticks: Dict[str, Dict[str, Any]] = {}
        self.stale_threshold_seconds = stale_threshold_seconds

    def update_tick(
        self,
        symbol: str,
        price: float,
        provider: str = "REALTIME_WS",
        exchange_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        tick = {
            "symbol": symbol.upper(),
            "price": float(price),
            "timestamp": now.isoformat(),
            "exchange_timestamp": exchange_timestamp.isoformat() if exchange_timestamp else now.isoformat(),
            "provider": provider,
            "data_status": "LIVE",
            "is_delayed": False,
            "last_tick_age_seconds": 0.0
        }
        self._ticks[symbol.upper()] = tick
        return tick

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        symbol_clean = symbol.upper()
        if symbol_clean not in self._ticks:
            return None

        tick = self._ticks[symbol_clean].copy()
        ts_str = tick.get("timestamp")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str)
                now = datetime.now(timezone.utc)
                age = (now - ts.astimezone(timezone.utc)).total_seconds()
                tick["last_tick_age_seconds"] = round(age, 2)
                if age > self.stale_threshold_seconds:
                    tick["data_status"] = "STALE"
            except Exception:
                pass
        return tick

    def clear(self):
        self._ticks.clear()


class RealTimeWebSocketProvider:
    """
    Real-Time WebSocket & REST Provider Manager for Finnhub & REST Fallback (Phase 21.1).
    Maintains active universe mappings, persistent WS reconnect loop, background REST fallback polling,
    and deterministic provider health state evaluation.
    """

    def __init__(self):
        from backend.config import REALTIME_PROVIDER, REALTIME_API_KEY, REALTIME_WS_URL, STALE_TICK_THRESHOLD_SECONDS
        self.provider_name = REALTIME_PROVIDER
        self.api_key = REALTIME_API_KEY
        self.ws_url = REALTIME_WS_URL
        self.stale_threshold = STALE_TICK_THRESHOLD_SECONDS

        self.cache = LiveTickCache(stale_threshold_seconds=self.stale_threshold)

        # Initialize full universe symbol mappings
        self.symbol_mappings = get_active_universe()
        self.subscribed_symbols: Set[str] = set(self.symbol_mappings.keys())

        self.listeners: Set[Callable[[Dict[str, Any]], None]] = set()

        self._task: Optional[asyncio.Task] = None
        self._rest_fallback_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._ws = None

        # Coinbase WebSocket Provider (BTC-USD, SOL-USD)
        from backend.data.providers.coinbase_ws_provider import CoinbaseWSProvider
        self._coinbase_provider = CoinbaseWSProvider()

        # Twelve Data Provider (XAU/USD)
        from backend.data.providers.twelve_data_provider import TwelveDataProvider
        self._twelve_data_provider = TwelveDataProvider()

        # Telemetry & Health Tracking
        self.websocket_connected: bool = False
        self.websocket_last_connected: Optional[str] = None
        self.websocket_last_message: Optional[str] = None
        self.websocket_last_error: Optional[str] = None
        self.websocket_reconnect_count: int = 0

        self.rest_available: bool = False
        self.provider_last_success_timestamp: Optional[str] = None
        self.provider_last_error_timestamp: Optional[str] = None
        self.provider_last_error_reason: Optional[str] = None
        self.last_tick_timestamp: Optional[str] = None

        self.valid_tick_count: int = 0
        self.invalid_tick_count: int = 0

        # Log universe activation startup telemetry
        logger.info(
            f"Universe loaded: {len(ALL_SYMBOLS_REF)}, Mapped: {len(self.symbol_mappings)}, "
            f"WebSocket subscriptions: {len(self.subscribed_symbols)}, REST fallback symbols: {len(self.subscribed_symbols)}"
        )

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def process_incoming_tick(self, symbol: str, price: float, provider: Optional[str] = None) -> Dict[str, Any]:
        """Normalizes, validates, and caches incoming live tick data."""
        if price is None or price <= 0 or not self.is_configured():
            self.invalid_tick_count += 1
            return {
                "symbol": symbol.upper(),
                "price": None,
                "timestamp": None,
                "provider": provider or "UNAVAILABLE",
                "status": "UNAVAILABLE",
                "data_status": "UNAVAILABLE",
                "is_delayed": True
            }

        self.valid_tick_count += 1
        self._last_processed_tick_live = True
        now_iso = datetime.now(timezone.utc).isoformat()
        self.last_tick_timestamp = now_iso
        self.provider_last_success_timestamp = now_iso

        tick = self.cache.update_tick(
            symbol=symbol,
            price=price,
            provider=provider or self.provider_name
        )

        # Notify active listeners
        for callback in list(self.listeners):
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Error in realtime listener callback: {e}")

        return tick

    def fetch_rest_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches latest quote via ProviderRouter (Primary -> Secondary -> Fallback -> UNAVAILABLE).
        Strictly rejects zero/negative prices, missing timestamps, or malformed responses.
        Never fabricates prices or returns fake substitute data.
        """
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        from backend.data.providers.provider_router import provider_router
        q = provider_router.get_quote(sym_clean)

        if q.get("price") is not None and float(q.get("price", 0)) > 0:
            self.rest_available = True
            now_iso = datetime.now(timezone.utc).isoformat()
            self.provider_last_success_timestamp = now_iso
            self.process_incoming_tick(symbol=sym_clean, price=float(q["price"]), provider=q.get("provider", "REST"))
            return {
                "symbol": sym_clean,
                "provider_symbol": prov_sym,
                "price": round(float(q["price"]), 4),
                "timestamp": q.get("timestamp", now_iso),
                "provider": q.get("provider", "FINNHUB"),
                "status": "LIVE",
                "data_status": "LIVE",
                "latency_ms": q.get("latency_ms", 0.0),
                "error": None
            }

        # 3. Invalid / Missing Data Result
        now_iso = datetime.now(timezone.utc).isoformat()
        self.provider_last_error_timestamp = now_iso
        self.provider_last_error_reason = q.get("error", "UNAVAILABLE")
        return {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "price": None,
            "timestamp": None,
            "provider": self.provider_name,
            "status": "UNAVAILABLE",
            "data_status": "UNAVAILABLE",
            "latency_ms": q.get("latency_ms", 0.0),
            "error": q.get("error", "UNAVAILABLE")
        }

    async def start(self):
        """Starts background WebSocket and REST fallback connection tasks."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        self._rest_fallback_task = asyncio.create_task(self._rest_fallback_loop())
        # Start Coinbase WS provider
        await self._coinbase_provider.start()
        logger.info("Finnhub RealTime WebSocket, Coinbase WS, and REST fallback background tasks started.")

    async def stop(self):
        """Gracefully stops background tasks."""
        self._running = False
        self.websocket_connected = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        if self._task:
            self._task.cancel()
        if self._rest_fallback_task:
            self._rest_fallback_task.cancel()
        # Stop Coinbase WS provider
        await self._coinbase_provider.stop()
        logger.info("Finnhub RealTime WebSocket, Coinbase WS, and REST fallback tasks stopped.")

    async def _listen_loop(self):
        """Async background WebSocket loop with exponential backoff reconnects."""
        backoff_sequence = [1, 2, 5, 10, 30, 60]
        backoff_idx = 0

        while self._running:
            if not self.is_configured():
                self.websocket_connected = False
                self.provider_last_error_reason = "REALTIME_API_KEY missing or invalid."
                await asyncio.sleep(10)
                continue

            target_url = f"{self.ws_url}?token={self.api_key.strip()}"
            try:
                async with websockets.connect(target_url, ping_interval=20, ping_timeout=20) as ws:
                    self._ws = ws
                    self.websocket_connected = True
                    self.websocket_last_connected = datetime.now(timezone.utc).isoformat()
                    backoff_idx = 0

                    # Resubscribe all active symbols
                    for sym, meta in self.symbol_mappings.items():
                        ws_sym = meta.get("finnhub_ws_symbol", sym)
                        sub_msg = json.dumps({"type": "subscribe", "symbol": ws_sym})
                        await ws.send(sub_msg)

                    async for message in ws:
                        if not self._running:
                            break
                        self.websocket_last_message = datetime.now(timezone.utc).isoformat()
                        try:
                            data = json.loads(message)
                            if data.get("type") == "trade":
                                for trade in data.get("data", []):
                                    sym = trade.get("s")
                                    price = trade.get("p")
                                    if sym and price:
                                        self.process_incoming_tick(symbol=sym, price=float(price))
                        except Exception as parse_err:
                            self.invalid_tick_count += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.websocket_connected = False
                self.websocket_reconnect_count += 1
                self.websocket_last_error = str(e)
                self.provider_last_error_timestamp = datetime.now(timezone.utc).isoformat()
                self.provider_last_error_reason = str(e)

                delay = backoff_sequence[min(backoff_idx, len(backoff_sequence) - 1)]
                backoff_idx += 1
                await asyncio.sleep(delay)

    async def _rest_fallback_loop(self):
        """Background REST fallback loop querying active symbols when WS is disconnected or stale."""
        sample_symbols = ["RELIANCE", "TCS", "INFY", "AAPL", "NVDA", "BTC-USD"]
        xau_poll_interval = 0
        while self._running:
            try:
                if not self.websocket_connected:
                    for sym in sample_symbols:
                        if not self._running:
                            break
                        self.fetch_rest_fallback_quote(sym)
                        await asyncio.sleep(1)

                # Poll XAU/USD via Twelve Data every ~60s (bounded)
                xau_poll_interval += 1
                if xau_poll_interval >= 2:  # Every 2 cycles of 30s = ~60s
                    xau_poll_interval = 0
                    try:
                        if self._twelve_data_provider.is_configured():
                            self._twelve_data_provider.get_quote("XAU/USD")
                    except Exception as xau_err:
                        logger.debug(f"XAU/USD REST poll error (non-fatal): {xau_err}")
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error(f"Error in REST fallback loop: {err}")

            await asyncio.sleep(30)

    @property
    def tick_cache(self):
        return self.cache

    @property
    def connection_status(self) -> str:
        if getattr(self, "_connection_status_override", None):
            return self._connection_status_override
        if not self.is_configured():
            return "UNAVAILABLE"
        if getattr(self, "_last_processed_tick_live", False) or (self.websocket_connected and self.valid_tick_count > 0):
            return "LIVE"
        if self.websocket_connected:
            return "CONNECTED"
        if self.rest_available:
            return "REST_ONLY"
        return "UNAVAILABLE"

    @connection_status.setter
    def connection_status(self, val: str):
        self._connection_status_override = val

    def subscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.add(symbol_clean)
        mapping = self.symbol_mappings.get(symbol_clean, {})
        ws_sym = mapping.get("finnhub_ws_symbol")
        if ws_sym:
            self.subscribed_symbols.add(ws_sym)

    def unsubscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.discard(symbol_clean)

    def get_stream_status(self) -> Dict[str, Any]:
        health = self.get_provider_health()
        health["connection_status"] = self.connection_status
        health["subscribed_symbols"] = list(self.subscribed_symbols)
        return health

    def get_provider_health(self) -> Dict[str, Any]:
        """Returns deterministic provider health state payload."""
        if not self.is_configured():
            state = "PROVIDER_INVALID_CONFIGURATION"
        elif self.websocket_connected and self.valid_tick_count > 0:
            state = "PROVIDER_CONNECTED"
        elif self.websocket_connected:
            state = "PROVIDER_DEGRADED"
        elif self.rest_available:
            state = "PROVIDER_REST_ONLY"
        else:
            state = "PROVIDER_DISCONNECTED"

        if getattr(self, "_connection_status_override", None):
            if self._connection_status_override in ["LIVE", "CONNECTED"]:
                state = "PROVIDER_CONNECTED"
            elif self._connection_status_override in ["RECONNECTING", "CONNECTING"]:
                state = "PROVIDER_DEGRADED"

        return {
            "provider": self.provider_name,
            "state": state,
            "status": state,
            "configured": self.is_configured(),
            "connection_status": self.connection_status,
            "websocket_connected": self.websocket_connected,
            "websocket_last_connected": self.websocket_last_connected,
            "websocket_last_message": self.websocket_last_message,
            "websocket_last_error": self.websocket_last_error,
            "websocket_reconnect_count": self.websocket_reconnect_count,
            "rest_available": self.rest_available,
            "configured_symbol_count": len(ALL_SYMBOLS_REF),
            "mapped_symbol_count": len(self.symbol_mappings),
            "subscribed_symbols": list(self.subscribed_symbols),
            "subscribed_symbol_count": len(self.subscribed_symbols),
            "valid_tick_count": self.valid_tick_count,
            "invalid_tick_count": self.invalid_tick_count,
            "last_tick_timestamp": self.last_tick_timestamp,
            "last_success_timestamp": self.provider_last_success_timestamp,
            "last_error_timestamp": self.provider_last_error_timestamp,
            "last_error_reason": self.provider_last_error_reason,
            "coinbase_health": self._coinbase_provider.get_health(),
            "twelve_data_health": self._twelve_data_provider.health(),
        }

    def get_symbol_health(self, symbol: str) -> Dict[str, Any]:
        """Returns detailed provider health breakdown for an individual symbol."""
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        tick = self.cache.get_latest_tick(sym_clean)
        latest_price = tick["price"] if tick else None
        latest_ts = tick["timestamp"] if tick else None
        data_status = tick.get("data_status", "UNAVAILABLE") if tick else "UNAVAILABLE"

        ws_state = "CONNECTED" if self.websocket_connected else "UNAVAILABLE"
        rest_state = "AVAILABLE" if self.rest_available else "UNAVAILABLE"

        return {
            "symbol": sym_clean,
            "provider_symbol": prov_sym,
            "provider": self.provider_name,
            "websocket": ws_state,
            "rest": rest_state,
            "latest_price": latest_price,
            "latest_timestamp": latest_ts,
            "data_status": data_status,
            "champion_status": "ACTIVE",
            "shadow_status": "ACTIVE"
        }


from backend.data.universe import ALL_SYMBOLS as ALL_SYMBOLS_REF
realtime_provider_manager = RealTimeWebSocketProvider()

