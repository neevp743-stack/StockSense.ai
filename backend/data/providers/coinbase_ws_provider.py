"""
StockSense AI — Phase 21.4 Coinbase Advanced Trade WebSocket Provider
Public market data WebSocket for BTC-USD and SOL-USD.
Subscribes to ticker, candles, and heartbeats channels.
No API key required for public channels.
"""

import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Deque
import websockets

logger = logging.getLogger(__name__)

# Default Coinbase products for StockSense
DEFAULT_COINBASE_PRODUCTS = ["BTC-USD", "SOL-USD"]
DEFAULT_COINBASE_WS_URL = "wss://advanced-trade-ws.coinbase.com"

# Maximum candles per product to keep in memory (bounded)
MAX_CANDLES_PER_PRODUCT = 100


class CoinbaseWSProvider:
    """
    Coinbase Advanced Trade public WebSocket provider.
    Connects to wss://advanced-trade-ws.coinbase.com and subscribes to:
    - ticker: live price updates for BTC-USD, SOL-USD
    - candles: 5-minute candle data (bounded cache)
    - heartbeats: connection liveness detection

    No API key is required for public market data channels.
    Feeds normalized ticks into the shared LiveTickCache via process_incoming_tick().
    """

    def __init__(
        self,
        ws_url: Optional[str] = None,
        products: Optional[List[str]] = None,
    ):
        from backend.config import COINBASE_WS_URL, COINBASE_PRODUCTS
        self.ws_url = ws_url or COINBASE_WS_URL or DEFAULT_COINBASE_WS_URL
        self.products = products or COINBASE_PRODUCTS or DEFAULT_COINBASE_PRODUCTS

        # Connection state
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._ws = None
        self._started: bool = False  # Prevents duplicate start

        # Candle cache: product_id -> deque of candle dicts (bounded)
        self._candle_cache: Dict[str, Deque[Dict[str, Any]]] = {
            p: deque(maxlen=MAX_CANDLES_PER_PRODUCT) for p in self.products
        }

        # Telemetry
        self.connected: bool = False
        self.last_connected: Optional[str] = None
        self.last_message: Optional[str] = None
        self.last_error: Optional[str] = None
        self.reconnect_count: int = 0
        self.tick_count: int = 0
        self.candle_count: int = 0
        self.heartbeat_count: int = 0
        self.error_count: int = 0

    async def start(self):
        """Starts the background WebSocket listener task. Prevents duplicate connections."""
        if self._started or self._running:
            logger.warning("CoinbaseWSProvider.start() called but already running. Skipping duplicate.")
            return
        self._running = True
        self._started = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"CoinbaseWSProvider started for products: {self.products}")

    async def stop(self):
        """Gracefully stops the WebSocket connection and background task."""
        self._running = False
        self._started = False
        self.connected = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        logger.info("CoinbaseWSProvider stopped.")

    async def restart(self):
        """Idempotently restarts the Coinbase WS provider."""
        await self.stop()
        await self.start()

    async def _listen_loop(self):
        """Async WebSocket loop with exponential backoff reconnection."""
        backoff_sequence = [1, 2, 5, 10, 30, 60]
        backoff_idx = 0

        while self._running:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    self._ws = ws
                    self.connected = True
                    self.last_connected = datetime.now(timezone.utc).isoformat()
                    backoff_idx = 0  # Reset backoff on successful connection

                    # Subscribe to channels — each channel requires a separate message
                    for channel in ["ticker", "candles", "heartbeats"]:
                        sub_msg = json.dumps({
                            "type": "subscribe",
                            "product_ids": list(self.products),
                            "channel": channel,
                        })
                        await ws.send(sub_msg)

                    logger.info(f"Coinbase WS connected and subscribed: {self.products}")

                    # Message processing loop
                    async for message in ws:
                        if not self._running:
                            break
                        self.last_message = datetime.now(timezone.utc).isoformat()
                        try:
                            self._process_message(json.loads(message))
                        except Exception as parse_err:
                            self.error_count += 1
                            logger.debug(f"Coinbase message parse error: {parse_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.connected = False
                self.reconnect_count += 1
                self.last_error = str(e)
                self.error_count += 1
                logger.warning(f"Coinbase WS error (reconnect #{self.reconnect_count}): {e}")

                delay = backoff_sequence[min(backoff_idx, len(backoff_sequence) - 1)]
                backoff_idx += 1
                await asyncio.sleep(delay)

    def _process_message(self, data: dict):
        """
        Routes incoming Coinbase messages to appropriate handlers.
        Ticker processing is independent from candle processing —
        if candle processing fails, ticker continues unaffected.
        """
        channel = data.get("channel", "")
        msg_type = data.get("type", "")

        if channel == "ticker" or msg_type == "ticker":
            self._handle_ticker(data)
        elif channel == "candles" or msg_type == "candles":
            try:
                self._handle_candles(data)
            except Exception as e:
                self.error_count += 1
                logger.debug(f"Coinbase candle processing error (ticker unaffected): {e}")
        elif channel == "heartbeats" or msg_type == "heartbeat":
            self._handle_heartbeat(data)
        # Subscription confirmations and other message types are silently ignored

    def _handle_ticker(self, data: dict):
        """
        Processes Coinbase ticker messages and feeds into LiveTickCache.
        
        Coinbase Advanced Trade ticker format:
        {
            "channel": "ticker",
            "events": [
                {
                    "type": "snapshot" | "update",
                    "tickers": [
                        {
                            "product_id": "BTC-USD",
                            "price": "50000.12",
                            ...
                        }
                    ]
                }
            ]
        }
        """
        events = data.get("events") or []
        if not isinstance(events, list):
            return
        for event in events:
            if not isinstance(event, dict):
                continue
            tickers = event.get("tickers") or []
            if not isinstance(tickers, list):
                continue
            for ticker in tickers:
                if not isinstance(ticker, dict):
                    continue
                product_id = ticker.get("product_id", "")
                price_str = ticker.get("price", "")

                if not product_id or not price_str:
                    continue

                # Only process our configured products
                if product_id not in self.products:
                    continue

                try:
                    price = float(price_str)
                    if price <= 0:
                        continue
                except (ValueError, TypeError):
                    continue

                self.tick_count += 1

                # Feed into shared LiveTickCache via realtime_provider_manager
                try:
                    from backend.data.realtime_provider import realtime_provider_manager
                    realtime_provider_manager.process_incoming_tick(
                        symbol=product_id,
                        price=price,
                        provider="COINBASE_WS"
                    )
                except Exception as e:
                    logger.debug(f"Error feeding Coinbase tick to cache: {e}")

    def _handle_candles(self, data: dict):
        """
        Processes Coinbase candle messages into bounded per-product cache.
        
        Coinbase Advanced Trade candles format:
        {
            "channel": "candles",
            "events": [
                {
                    "type": "snapshot" | "update",
                    "candles": [
                        {
                            "start": "1692000000",
                            "high": "50100.00",
                            "low": "49900.00",
                            "open": "50000.00",
                            "close": "50050.00",
                            "volume": "10.5",
                            "product_id": "BTC-USD"
                        }
                    ]
                }
            ]
        }
        """
        events = data.get("events") or []
        if not isinstance(events, list):
            return
        for event in events:
            if not isinstance(event, dict):
                continue
            candles = event.get("candles") or []
            if not isinstance(candles, list):
                continue
            for candle in candles:
                if not isinstance(candle, dict):
                    continue
                product_id = candle.get("product_id", "")
                if product_id not in self.products:
                    continue

                try:
                    candle_entry = {
                        "product_id": product_id,
                        "start": candle.get("start"),
                        "open": float(candle.get("open", 0)),
                        "high": float(candle.get("high", 0)),
                        "low": float(candle.get("low", 0)),
                        "close": float(candle.get("close", 0)),
                        "volume": float(candle.get("volume", 0)),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    # Initialize deque for unknown products (safety)
                    if product_id not in self._candle_cache:
                        self._candle_cache[product_id] = deque(maxlen=MAX_CANDLES_PER_PRODUCT)

                    self._candle_cache[product_id].append(candle_entry)
                    self.candle_count += 1
                except (ValueError, TypeError) as e:
                    self.error_count += 1
                    logger.debug(f"Coinbase candle parse error for {product_id}: {e}")

    def _handle_heartbeat(self, data: dict):
        """Processes heartbeat messages for connection liveness tracking."""
        self.heartbeat_count += 1

    def get_candle_cache(self, product_id: Optional[str] = None) -> Dict[str, list]:
        """Returns bounded candle cache. Optionally filtered by product_id."""
        if product_id:
            return {product_id: list(self._candle_cache.get(product_id, []))}
        return {k: list(v) for k, v in self._candle_cache.items()}

    def get_health(self) -> Dict[str, Any]:
        """Returns Coinbase provider health telemetry. Never exposes secrets."""
        return {
            "provider": "COINBASE_WS",
            "connected": self.connected,
            "last_connected": self.last_connected,
            "last_message": self.last_message,
            "last_error": self.last_error,
            "reconnect_count": self.reconnect_count,
            "tick_count": self.tick_count,
            "candle_count": self.candle_count,
            "heartbeat_count": self.heartbeat_count,
            "error_count": self.error_count,
            "subscribed_products": list(self.products),
            "candle_cache_sizes": {k: len(v) for k, v in self._candle_cache.items()},
        }
