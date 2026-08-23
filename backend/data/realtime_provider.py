"""
StockSense AI — Real-Time WebSocket & REST Market Data Provider (Phase 21)
Provides normalized live tick streaming, exponential backoff reconnection,
stale tick detection, provider health telemetry, and strict REST fallback.
"""

import os
import asyncio
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
import websockets

from backend.assets.provider_symbol_mapper import get_all_universe_symbol_mappings

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
    Legitimate WebSocket Real-Time Provider Manager for Finnhub & REST Fallback (Phase 21).
    Runs a persistent background connection loop for authenticated live ticks.
    Credentials remain strictly on the backend and are NEVER logged or exposed.
    """

    def __init__(self):
        from backend.config import REALTIME_PROVIDER, REALTIME_API_KEY, REALTIME_WS_URL, STALE_TICK_THRESHOLD_SECONDS
        self.provider_name = REALTIME_PROVIDER
        self.api_key = REALTIME_API_KEY
        self.ws_url = REALTIME_WS_URL
        self.stale_threshold = STALE_TICK_THRESHOLD_SECONDS

        self.cache = LiveTickCache(stale_threshold_seconds=self.stale_threshold)

        # Initialize full 109+ symbol mapping universe
        self.symbol_mappings = get_all_universe_symbol_mappings()
        self.subscribed_symbols: Set[str] = set(self.symbol_mappings.keys())

        self.connection_status: str = "UNAVAILABLE"  # PROVIDER_CONNECTED, PROVIDER_DEGRADED, PROVIDER_REST_ONLY, PROVIDER_DISCONNECTED, PROVIDER_INVALID_CONFIGURATION
        self.listeners: Set[Callable[[Dict[str, Any]], None]] = set()

        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._ws = None

        # Provider health metrics
        self.provider_last_success_timestamp: Optional[str] = None
        self.provider_last_error_timestamp: Optional[str] = None
        self.provider_last_error_reason: Optional[str] = None
        self.websocket_connected: bool = False
        self.rest_available: bool = False
        self.last_tick_timestamp: Optional[str] = None
        self.valid_tick_count: int = 0
        self.invalid_tick_count: int = 0

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def subscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.add(symbol_clean)

        ws_sym = symbol_clean
        if symbol_clean in self.symbol_mappings:
            ws_sym = self.symbol_mappings[symbol_clean]["finnhub_ws_symbol"]

        if self._ws and self.websocket_connected:
            try:
                msg = json.dumps({"type": "subscribe", "symbol": ws_sym})
                asyncio.create_task(self._ws.send(msg))
            except Exception as e:
                logger.error(f"Failed to send subscription for {ws_sym}: {e}")

    def unsubscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.discard(symbol_clean)

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]):
        self.listeners.add(callback)

    def unregister_listener(self, callback: Callable[[Dict[str, Any]], None]):
        self.listeners.discard(callback)

    def process_incoming_tick(self, symbol: str, price: float, provider: Optional[str] = None) -> Dict[str, Any]:
        """Normalizes and caches an incoming live tick, notifying subscribers."""
        if price is None or price <= 0 or not self.is_configured():
            self.invalid_tick_count += 1
            return {
                "symbol": symbol.upper(),
                "price": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": "UNCONFIGURED" if not self.is_configured() else "INVALID",
                "data_status": "UNAVAILABLE",
                "is_delayed": True
            }

        self.valid_tick_count += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        self.last_tick_timestamp = now_iso
        self.provider_last_success_timestamp = now_iso

        tick = self.cache.update_tick(
            symbol=symbol,
            price=price,
            provider=provider or self.provider_name
        )

        # Update alias mappings
        if symbol.upper() == "BINANCE:BTCUSDT":
            self.cache.update_tick("BTC-USD", price, provider=provider or self.provider_name)
        elif symbol.upper() == "BINANCE:ETHUSDT":
            self.cache.update_tick("ETH-USD", price, provider=provider or self.provider_name)

        for callback in list(self.listeners):
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Error in realtime listener callback: {e}")

        return tick

    def fetch_rest_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches latest quote via Finnhub REST API with YFinance fallback.
        Never fabricates fake prices. If data is unavailable, returns price=None & UNAVAILABLE.
        """
        sym_clean = symbol.upper().strip()
        mapping = self.symbol_mappings.get(sym_clean, {})
        prov_sym = mapping.get("provider_symbol", sym_clean)

        now_utc = datetime.now(timezone.utc)

        # Attempt Finnhub REST if API key is configured
        if self.is_configured():
            try:
                url = f"https://finnhub.io/api/v1/quote?symbol={prov_sym}&token={self.api_key.strip()}"
                req = urllib.request.Request(url, headers={"User-Agent": "StockSenseAI/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        current_price = data.get("c")
                        if current_price is not None and current_price > 0:
                            self.rest_available = True
                            self.provider_last_success_timestamp = now_utc.isoformat()
                            tick = self.process_incoming_tick(symbol=sym_clean, price=float(current_price), provider="FINNHUB_REST")
                            return tick
            except Exception as e:
                self.provider_last_error_timestamp = now_utc.isoformat()
                self.provider_last_error_reason = f"Finnhub REST Error for {sym_clean}: {e}"

        # Fallback to YFinance Provider
        from backend.data.provider import YFinanceProvider
        yf_provider = YFinanceProvider()
        yf_quote = yf_provider.get_latest_quote(sym_clean)

        price = yf_quote.get("price")
        if price is not None and price > 0:
            self.rest_available = True
            return self.process_incoming_tick(symbol=sym_clean, price=float(price), provider="YFINANCE_REST")

        return {
            "symbol": sym_clean,
            "provider": "UNAVAILABLE",
            "price": None,
            "timestamp": now_utc.isoformat(),
            "data_status": "UNAVAILABLE",
            "is_delayed": True
        }

    async def start(self):
        """Starts the persistent background WebSocket listener task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("Finnhub RealTime WebSocket background listener task started.")

    async def stop(self):
        """Gracefully stops the background listener task."""
        self._running = False
        self.websocket_connected = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.connection_status = "PROVIDER_DISCONNECTED"
        logger.info("Finnhub RealTime WebSocket background listener stopped.")

    async def _listen_loop(self):
        """Main async background connection and reconnection loop with exponential backoff."""
        backoff_sequence = [1, 2, 5, 10, 30, 60]
        backoff_idx = 0

        while self._running:
            if not self.is_configured():
                self.connection_status = "PROVIDER_INVALID_CONFIGURATION"
                self.websocket_connected = False
                self.provider_last_error_reason = "REALTIME_API_KEY missing or invalid."
                logger.warning("Finnhub WebSocket not configured (REALTIME_API_KEY missing/invalid). Connection loop idle.")
                await asyncio.sleep(10)
                continue

            target_url = f"{self.ws_url}?token={self.api_key.strip()}"
            safe_url = f"{self.ws_url}?token=***REDACTED***"
            logger.info(f"Connecting to Finnhub WebSocket at {safe_url}")

            try:
                self.connection_status = "RECONNECTING"
                async with websockets.connect(target_url, ping_interval=20, ping_timeout=20) as ws:
                    self._ws = ws
                    self.websocket_connected = True
                    self.connection_status = "PROVIDER_CONNECTED"
                    backoff_idx = 0
                    logger.info("FINNHUB WebSocket connection established.")

                    # Send subscriptions for all 109+ mapped symbols
                    for sym, meta in self.symbol_mappings.items():
                        ws_sym = meta["finnhub_ws_symbol"]
                        sub_msg = json.dumps({"type": "subscribe", "symbol": ws_sym})
                        await ws.send(sub_msg)

                    async for message in ws:
                        if not self._running:
                            break
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
                            logger.error(f"Error parsing Finnhub tick message: {parse_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.websocket_connected = False
                self.connection_status = "PROVIDER_REST_ONLY" if self.rest_available else "PROVIDER_DISCONNECTED"
                self.provider_last_error_timestamp = datetime.now(timezone.utc).isoformat()
                self.provider_last_error_reason = str(e)

                delay = backoff_sequence[min(backoff_idx, len(backoff_sequence) - 1)]
                backoff_idx += 1
                logger.warning(f"FINNHUB WebSocket connection unavailable: {e}. Reconnecting in {delay} seconds...")
                await asyncio.sleep(delay)

        self.websocket_connected = False
        self.connection_status = "PROVIDER_DISCONNECTED"

    def get_provider_health(self) -> Dict[str, Any]:
        """
        Returns full backward-compatible provider health status payload without secret leakage.
        """
        if not self.is_configured():
            status = "PROVIDER_INVALID_CONFIGURATION"
        elif self.websocket_connected and self.valid_tick_count > 0:
            status = "PROVIDER_CONNECTED"
        elif self.rest_available:
            status = "PROVIDER_REST_ONLY"
        elif self.websocket_connected:
            status = "PROVIDER_DEGRADED"
        else:
            status = "PROVIDER_DISCONNECTED"

        return {
            "provider": self.provider_name,
            "status": status,
            "configured": self.is_configured(),
            "websocket_connected": self.websocket_connected,
            "rest_available": self.rest_available,
            "provider_last_success_timestamp": self.provider_last_success_timestamp,
            "provider_last_error_timestamp": self.provider_last_error_timestamp,
            "provider_last_error_reason": self.provider_last_error_reason,
            "last_tick_timestamp": self.last_tick_timestamp,
            "subscribed_symbol_count": len(self.subscribed_symbols),
            "valid_tick_count": self.valid_tick_count,
            "invalid_tick_count": self.invalid_tick_count,
            "stale_threshold_seconds": self.stale_threshold,
            "active_listeners": len(self.listeners)
        }

    def get_stream_status(self) -> Dict[str, Any]:
        return self.get_provider_health()


# Global Singleton Manager
realtime_provider_manager = RealTimeWebSocketProvider()
