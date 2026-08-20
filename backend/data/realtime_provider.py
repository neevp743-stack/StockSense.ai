"""
StockSense AI — Real-Time WebSocket Market Data Provider & Connection Manager
Provides normalized live tick streaming, exponential backoff reconnection, stale tick detection,
and strict in-memory cache isolation from historical training datasets.
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
import websockets

logger = logging.getLogger(__name__)

class LiveTickCache:
    """In-memory cache for normalized live market ticks."""

    def __init__(self, stale_threshold_seconds: int = 30):
        self._ticks: Dict[str, Dict[str, Any]] = {}
        self.stale_threshold_seconds = stale_threshold_seconds

    def update_tick(self, symbol: str, price: float, provider: str = "REALTIME_WS", exchange_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
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
                age = (datetime.utcnow() - ts).total_seconds()
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
    Legitimate WebSocket Real-Time Provider Manager for Finnhub.
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
        self.subscribed_symbols: Set[str] = {"BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BTC-USD", "ETH-USD"}
        self.connection_status: str = "UNAVAILABLE"  # LIVE, STALE, RECONNECTING, UNAVAILABLE
        self.listeners: Set[Callable[[Dict[str, Any]], None]] = set()

        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._ws = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def subscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.add(symbol_clean)
        
        finnhub_symbol = symbol_clean
        if symbol_clean in ["BTC-USD", "BTCUSD"]:
            finnhub_symbol = "BINANCE:BTCUSDT"
            self.subscribed_symbols.add(finnhub_symbol)
        elif symbol_clean in ["ETH-USD", "ETHUSD"]:
            finnhub_symbol = "BINANCE:ETHUSDT"
            self.subscribed_symbols.add(finnhub_symbol)

        logger.info(f"Subscribed real-time symbol: {symbol_clean} ({finnhub_symbol})")

        if self._ws and self.connection_status in ["LIVE", "RECONNECTING"]:
            try:
                msg = json.dumps({"type": "subscribe", "symbol": finnhub_symbol})
                asyncio.create_task(self._ws.send(msg))
            except Exception as e:
                logger.error(f"Failed to send subscription for {finnhub_symbol}: {e}")

    def unsubscribe(self, symbol: str):
        symbol_clean = symbol.upper().strip()
        self.subscribed_symbols.discard(symbol_clean)
        logger.info(f"Unsubscribed real-time symbol: {symbol_clean}")

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]):
        self.listeners.add(callback)

    def unregister_listener(self, callback: Callable[[Dict[str, Any]], None]):
        self.listeners.discard(callback)

    def process_incoming_tick(self, symbol: str, price: float, provider: Optional[str] = None) -> Dict[str, Any]:
        """Normalizes and caches an incoming live tick, notifying subscribers."""
        if not self.is_configured():
            self.connection_status = "UNAVAILABLE"
            return {
                "symbol": symbol.upper(),
                "price": price,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "UNCONFIGURED",
                "data_status": "UNAVAILABLE",
                "is_delayed": True
            }

        self.connection_status = "LIVE"
        tick = self.cache.update_tick(
            symbol=symbol,
            price=price,
            provider=provider or self.provider_name
        )

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
        self.connection_status = "UNAVAILABLE"
        logger.info("Finnhub RealTime WebSocket background listener stopped.")

    async def _listen_loop(self):
        """Main async background connection and reconnection loop."""
        backoff = 2
        max_backoff = 60

        while self._running:
            if not self.is_configured():
                self.connection_status = "UNAVAILABLE"
                logger.warning("Finnhub WebSocket not configured (REALTIME_API_KEY missing). Connection loop idle.")
                await asyncio.sleep(10)
                continue

            target_url = f"{self.ws_url}?token={self.api_key.strip()}"
            safe_url = f"{self.ws_url}?token=***REDACTED***"
            logger.info(f"Connecting to Finnhub WebSocket at {safe_url}")

            try:
                self.connection_status = "RECONNECTING"
                async with websockets.connect(target_url, ping_interval=20, ping_timeout=20) as ws:
                    self._ws = ws
                    self.connection_status = "LIVE"
                    backoff = 2
                    logger.info("FINNHUB WebSocket connection established.")

                    for sym in list(self.subscribed_symbols):
                        sub_sym = sym
                        if sym in ["BTC-USD", "BTCUSD"]:
                            sub_sym = "BINANCE:BTCUSDT"
                        elif sym in ["ETH-USD", "ETHUSD"]:
                            sub_sym = "BINANCE:ETHUSDT"
                        sub_msg = json.dumps({"type": "subscribe", "symbol": sub_sym})
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
                            logger.error(f"Error parsing Finnhub tick message: {parse_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.connection_status = "RECONNECTING"
                logger.warning(f"FINNHUB WebSocket connection unavailable: {e}. Reconnecting in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

        self.connection_status = "UNAVAILABLE"

    def get_stream_status(self) -> Dict[str, Any]:
        btc_tick = self.cache.get_latest_tick("BTC-USD") or self.cache.get_latest_tick("BINANCE:BTCUSDT")
        status = self.connection_status if self.is_configured() else "UNAVAILABLE"
        if btc_tick and btc_tick.get("data_status") == "STALE" and status == "LIVE":
            status = "STALE"

        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
            "connection_status": status,
            "subscribed_symbols": list(self.subscribed_symbols),
            "stale_threshold_seconds": self.stale_threshold,
            "active_listeners": len(self.listeners)
        }

# Global Singleton Manager
realtime_provider_manager = RealTimeWebSocketProvider()
