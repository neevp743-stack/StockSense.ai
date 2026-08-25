"""
StockSense AI — Phase 21.4 Coinbase WebSocket Provider Tests
Tests CoinbaseWSProvider initialization, message parsing, bounded caching,
reconnect/backoff, lifecycle, LiveTickCache integration, and security.
"""

import pytest
import asyncio
import json
import time
from collections import deque
from datetime import datetime, timezone

from backend.data.providers.coinbase_ws_provider import (
    CoinbaseWSProvider,
    DEFAULT_COINBASE_WS_URL,
    DEFAULT_COINBASE_PRODUCTS,
    MAX_CANDLES_PER_PRODUCT,
)
from backend.data.realtime_provider import RealTimeWebSocketProvider, LiveTickCache


# ─── Initialization & Configuration ───────────────────────────────

def test_coinbase_default_initialization():
    """CoinbaseWSProvider initializes with correct defaults, no API key needed."""
    provider = CoinbaseWSProvider()
    assert provider.ws_url == DEFAULT_COINBASE_WS_URL
    assert "BTC-USD" in provider.products
    assert "SOL-USD" in provider.products
    assert provider.connected is False
    assert provider._running is False
    assert provider._started is False
    assert provider.tick_count == 0
    assert provider.candle_count == 0
    assert provider.heartbeat_count == 0


def test_coinbase_custom_initialization():
    """CoinbaseWSProvider can be initialized with custom URL and products."""
    provider = CoinbaseWSProvider(
        ws_url="wss://custom.ws.url",
        products=["ETH-USD"]
    )
    assert provider.ws_url == "wss://custom.ws.url"
    assert provider.products == ["ETH-USD"]
    assert "ETH-USD" in provider._candle_cache


# ─── Ticker Message Parsing ───────────────────────────────────────

def test_coinbase_ticker_btc_parsing():
    """Parses a Coinbase ticker message for BTC-USD and feeds into LiveTickCache."""
    provider = CoinbaseWSProvider()
    # Simulate a ticker message
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{
                "product_id": "BTC-USD",
                "price": "65432.10",
                "volume_24_h": "12345.67",
                "low_24_h": "64000.00",
                "high_24_h": "66000.00",
            }]
        }]
    }
    provider._process_message(msg)
    assert provider.tick_count == 1

    # Verify tick was fed into LiveTickCache
    from backend.data.realtime_provider import realtime_provider_manager
    tick = realtime_provider_manager.cache.get_latest_tick("BTC-USD")
    assert tick is not None
    assert tick["price"] == 65432.10
    assert tick["provider"] == "COINBASE_WS"


def test_coinbase_ticker_sol_parsing():
    """Parses a Coinbase ticker message for SOL-USD."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "snapshot",
            "tickers": [{
                "product_id": "SOL-USD",
                "price": "142.55",
            }]
        }]
    }
    provider._process_message(msg)
    assert provider.tick_count == 1

    from backend.data.realtime_provider import realtime_provider_manager
    tick = realtime_provider_manager.cache.get_latest_tick("SOL-USD")
    assert tick is not None
    assert tick["price"] == 142.55
    assert tick["provider"] == "COINBASE_WS"


def test_coinbase_ticker_invalid_price_ignored():
    """Ticker with zero or negative price is silently ignored."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [
                {"product_id": "BTC-USD", "price": "0"},
                {"product_id": "BTC-USD", "price": "-100"},
                {"product_id": "BTC-USD", "price": ""},
                {"product_id": "BTC-USD", "price": "not_a_number"},
            ]
        }]
    }
    provider._process_message(msg)
    assert provider.tick_count == 0


def test_coinbase_ticker_unknown_product_ignored():
    """Ticker for product not in configured list is ignored."""
    provider = CoinbaseWSProvider(products=["BTC-USD"])
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{
                "product_id": "ETH-USD",
                "price": "3000.00",
            }]
        }]
    }
    provider._process_message(msg)
    assert provider.tick_count == 0


def test_coinbase_ticker_multiple_events():
    """Processes multiple ticker events in a single message."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [
            {"type": "update", "tickers": [{"product_id": "BTC-USD", "price": "60000.00"}]},
            {"type": "update", "tickers": [{"product_id": "SOL-USD", "price": "150.00"}]},
        ]
    }
    provider._process_message(msg)
    assert provider.tick_count == 2


# ─── Candle Message Parsing ───────────────────────────────────────

def test_coinbase_candle_parsing():
    """Parses a Coinbase candle message and stores in bounded cache."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "candles",
        "events": [{
            "type": "snapshot",
            "candles": [{
                "product_id": "BTC-USD",
                "start": "1692000000",
                "open": "50000.00",
                "high": "50100.00",
                "low": "49900.00",
                "close": "50050.00",
                "volume": "10.5",
            }]
        }]
    }
    provider._process_message(msg)
    assert provider.candle_count == 1
    cache = provider.get_candle_cache("BTC-USD")
    assert len(cache["BTC-USD"]) == 1
    assert cache["BTC-USD"][0]["close"] == 50050.00


def test_coinbase_candle_cache_bounded():
    """Candle cache respects MAX_CANDLES_PER_PRODUCT bound."""
    provider = CoinbaseWSProvider()
    for i in range(MAX_CANDLES_PER_PRODUCT + 50):
        msg = {
            "channel": "candles",
            "events": [{
                "type": "update",
                "candles": [{
                    "product_id": "BTC-USD",
                    "start": str(1692000000 + i * 300),
                    "open": str(50000 + i),
                    "high": str(50100 + i),
                    "low": str(49900 + i),
                    "close": str(50050 + i),
                    "volume": "1.0",
                }]
            }]
        }
        provider._process_message(msg)

    cache = provider.get_candle_cache("BTC-USD")
    assert len(cache["BTC-USD"]) == MAX_CANDLES_PER_PRODUCT
    assert provider.candle_count == MAX_CANDLES_PER_PRODUCT + 50


def test_coinbase_candle_failure_does_not_break_ticker():
    """If candle processing fails, ticker processing continues."""
    provider = CoinbaseWSProvider()
    # Process candle with malformed data
    bad_candle_msg = {
        "channel": "candles",
        "events": [{
            "type": "update",
            "candles": [{
                "product_id": "BTC-USD",
                "open": "not_a_number",
            }]
        }]
    }
    provider._process_message(bad_candle_msg)

    # Now process a valid ticker
    ticker_msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{"product_id": "BTC-USD", "price": "60000.00"}]
        }]
    }
    provider._process_message(ticker_msg)
    assert provider.tick_count == 1


# ─── Heartbeat Message Handling ───────────────────────────────────

def test_coinbase_heartbeat_handling():
    """Heartbeat messages are counted but don't crash."""
    provider = CoinbaseWSProvider()
    msg = {"channel": "heartbeats", "type": "heartbeat", "events": []}
    provider._process_message(msg)
    assert provider.heartbeat_count == 1

    msg2 = {"channel": "heartbeats", "events": []}
    provider._process_message(msg2)
    assert provider.heartbeat_count == 2


# ─── Malformed Message Handling ───────────────────────────────────

def test_coinbase_malformed_message_no_crash():
    """Malformed and empty messages don't crash the provider."""
    provider = CoinbaseWSProvider()
    provider._process_message({})
    provider._process_message({"channel": "unknown"})
    provider._process_message({"channel": "ticker", "events": None})
    # These should not raise
    assert provider.tick_count == 0


def test_coinbase_malformed_ticker_events_no_crash():
    """Ticker events with missing fields don't crash."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [
                {},  # No product_id or price
                {"product_id": "BTC-USD"},  # No price
                {"price": "100"},  # No product_id
            ]
        }]
    }
    provider._process_message(msg)
    assert provider.tick_count == 0


# ─── Duplicate Connection Prevention ──────────────────────────────

def test_coinbase_duplicate_start_prevention():
    """Calling start() twice does not create duplicate tasks."""
    async def run_test():
        provider = CoinbaseWSProvider(ws_url="wss://invalid.example.com")
        await provider.start()
        assert provider._started is True
        assert provider._running is True
        first_task = provider._task

        # Second start should be no-op
        await provider.start()
        assert provider._task is first_task  # Same task object

        await provider.stop()
        assert provider._started is False

    asyncio.run(run_test())


# ─── Clean Shutdown ───────────────────────────────────────────────

def test_coinbase_clean_shutdown():
    """Verify clean start/stop lifecycle."""
    async def run_test():
        provider = CoinbaseWSProvider(ws_url="wss://invalid.example.com")
        await provider.start()
        assert provider._running is True
        assert provider._started is True

        await provider.stop()
        assert provider._running is False
        assert provider._started is False
        assert provider._ws is None
        assert provider._task is None

    asyncio.run(run_test())


# ─── LiveTickCache Integration ────────────────────────────────────

def test_coinbase_integration_with_live_tick_cache():
    """
    Coinbase ticks appear in the shared LiveTickCache
    and are retrievable via get_latest_tick().
    """
    from backend.data.realtime_provider import realtime_provider_manager

    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{"product_id": "BTC-USD", "price": "99999.99"}]
        }]
    }
    provider._process_message(msg)

    tick = realtime_provider_manager.cache.get_latest_tick("BTC-USD")
    assert tick is not None
    assert tick["symbol"] == "BTC-USD"
    assert tick["price"] == 99999.99
    assert tick["provider"] == "COINBASE_WS"
    assert tick["data_status"] == "LIVE"

    # BTC-USD tick should NOT overwrite other symbols
    assert realtime_provider_manager.cache.get_latest_tick("RELIANCE") is None


def test_coinbase_does_not_overwrite_nse_symbols():
    """Coinbase ticks never overwrite NSE symbol data."""
    from backend.data.realtime_provider import realtime_provider_manager

    # Simulate an NSE tick first
    realtime_provider_manager.api_key = "test_key"
    realtime_provider_manager.process_incoming_tick("RELIANCE", 2500.0, provider="FINNHUB")

    # Now process a Coinbase tick
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "ticker",
        "events": [{
            "type": "update",
            "tickers": [{"product_id": "BTC-USD", "price": "70000.00"}]
        }]
    }
    provider._process_message(msg)

    # RELIANCE should still have the Finnhub price
    reliance_tick = realtime_provider_manager.cache.get_latest_tick("RELIANCE")
    assert reliance_tick is not None
    assert reliance_tick["price"] == 2500.0
    assert reliance_tick["provider"] == "FINNHUB"


# ─── Health Telemetry ─────────────────────────────────────────────

def test_coinbase_health_telemetry():
    """Health payload contains all required fields and no secrets."""
    provider = CoinbaseWSProvider()
    health = provider.get_health()

    assert health["provider"] == "COINBASE_WS"
    assert "connected" in health
    assert "last_connected" in health
    assert "last_message" in health
    assert "last_error" in health
    assert "reconnect_count" in health
    assert "tick_count" in health
    assert "candle_count" in health
    assert "heartbeat_count" in health
    assert "error_count" in health
    assert "subscribed_products" in health
    assert "candle_cache_sizes" in health
    assert "BTC-USD" in health["subscribed_products"]
    assert "SOL-USD" in health["subscribed_products"]

    # Must never contain secrets
    health_str = json.dumps(health)
    assert "api_key" not in health_str.lower()
    assert "secret" not in health_str.lower()
    assert "token" not in health_str.lower()


# ─── Security: No Secrets Leaked ──────────────────────────────────

def test_coinbase_no_secrets_in_health():
    """Health payloads never contain API keys, tokens, or secrets."""
    provider = CoinbaseWSProvider()
    health = provider.get_health()
    health_str = str(health)

    # No common secret key names
    for forbidden in ["api_key", "apikey", "secret", "password", "token", "credential"]:
        assert forbidden not in health_str.lower()


def test_coinbase_health_integrated_into_realtime_status():
    """Coinbase health appears in the realtime_provider_manager status."""
    from backend.data.realtime_provider import realtime_provider_manager
    status = realtime_provider_manager.get_stream_status()
    assert "coinbase_health" in status
    assert status["coinbase_health"]["provider"] == "COINBASE_WS"


# ─── Candle Cache Access ─────────────────────────────────────────

def test_coinbase_candle_cache_access():
    """get_candle_cache returns data for specific product or all."""
    provider = CoinbaseWSProvider()
    msg = {
        "channel": "candles",
        "events": [{
            "type": "update",
            "candles": [{
                "product_id": "SOL-USD",
                "start": "1692000000",
                "open": "140.00",
                "high": "145.00",
                "low": "138.00",
                "close": "143.00",
                "volume": "500.0",
            }]
        }]
    }
    provider._process_message(msg)

    # Specific product
    sol_cache = provider.get_candle_cache("SOL-USD")
    assert len(sol_cache["SOL-USD"]) == 1

    # All products
    all_cache = provider.get_candle_cache()
    assert "BTC-USD" in all_cache
    assert "SOL-USD" in all_cache


def test_coinbase_btc_freshness():
    """BTC-USD tick has valid freshness metadata."""
    from backend.data.realtime_provider import realtime_provider_manager

    provider = CoinbaseWSProvider()
    provider._process_message({
        "channel": "ticker",
        "events": [{"type": "update", "tickers": [{"product_id": "BTC-USD", "price": "71000.00"}]}]
    })

    tick = realtime_provider_manager.cache.get_latest_tick("BTC-USD")
    assert tick["data_status"] == "LIVE"
    assert tick["is_delayed"] is False
    assert tick["last_tick_age_seconds"] < 5.0


def test_coinbase_sol_freshness():
    """SOL-USD tick has valid freshness metadata."""
    from backend.data.realtime_provider import realtime_provider_manager

    provider = CoinbaseWSProvider()
    provider._process_message({
        "channel": "ticker",
        "events": [{"type": "update", "tickers": [{"product_id": "SOL-USD", "price": "155.00"}]}]
    })

    tick = realtime_provider_manager.cache.get_latest_tick("SOL-USD")
    assert tick["data_status"] == "LIVE"
    assert tick["is_delayed"] is False
