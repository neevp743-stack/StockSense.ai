import pytest
import time
import asyncio
from datetime import datetime, timedelta

from backend.data.realtime_provider import RealTimeWebSocketProvider, LiveTickCache
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_provider_without_credentials():
    provider = RealTimeWebSocketProvider()
    provider.api_key = ""  # Ensure empty
    assert provider.is_configured() is False
    tick = provider.process_incoming_tick("AAPL", 150.0)
    assert tick["data_status"] == "UNAVAILABLE"
    assert tick["is_delayed"] is True

def test_tick_normalization():
    cache = LiveTickCache(stale_threshold_seconds=30)
    tick = cache.update_tick("RELIANCE", 1314.25, provider="TEST_WS")
    assert tick["symbol"] == "RELIANCE"
    assert tick["price"] == 1314.25
    assert tick["provider"] == "TEST_WS"
    assert tick["data_status"] == "LIVE"
    assert tick["is_delayed"] is False

def test_live_status():
    provider = RealTimeWebSocketProvider()
    provider.api_key = "test_key"
    tick = provider.process_incoming_tick("MSFT", 400.0)
    assert tick["data_status"] == "LIVE"
    assert provider.connection_status == "LIVE"

def test_stale_status():
    cache = LiveTickCache(stale_threshold_seconds=1)
    cache.update_tick("NVDA", 120.0)
    time.sleep(1.2)  # Wait for tick to exceed stale threshold
    tick = cache.get_latest_tick("NVDA")
    assert tick is not None
    assert tick["data_status"] == "STALE"
    assert tick["last_tick_age_seconds"] > 1.0

def test_reconnecting_status():
    provider = RealTimeWebSocketProvider()
    provider.api_key = "test_key"
    provider.connection_status = "RECONNECTING"
    status = provider.get_stream_status()
    assert status["connection_status"] == "RECONNECTING"

def test_subscription():
    provider = RealTimeWebSocketProvider()
    provider.subscribe("AAPL")
    assert "AAPL" in provider.subscribed_symbols
    assert "AAPL" in provider.get_stream_status()["subscribed_symbols"]

def test_unsubscription():
    provider = RealTimeWebSocketProvider()
    provider.subscribe("AAPL")
    provider.unsubscribe("AAPL")
    assert "AAPL" not in provider.subscribed_symbols

def test_historical_isolation():
    """Verifies that live ticks do NOT modify historical training prices dataframe."""
    from backend.data.data_service import get_historical_data_from_db
    df1 = get_historical_data_from_db("RELIANCE")
    provider = RealTimeWebSocketProvider()
    provider.api_key = "test_key"
    provider.process_incoming_tick("RELIANCE", 9999.99)
    df2 = get_historical_data_from_db("RELIANCE")
    
    if not df1.empty and not df2.empty:
        assert len(df1) == len(df2)
        assert df1["close"].iloc[-1] == df2["close"].iloc[-1]
        assert df2["close"].iloc[-1] != 9999.99

def test_no_fake_live_data():
    """Verifies yfinance provider quotes are marked DELAYED/HISTORICAL, NEVER LIVE."""
    from backend.data.provider import YFinanceProvider
    prov = YFinanceProvider()
    quote = prov.get_latest_quote("AAPL")
    assert quote["data_status"] in ["DELAYED", "HISTORICAL", "UNAVAILABLE"]
    assert quote["data_status"] != "LIVE"

def test_quote_endpoint():
    response = client.get("/api/realtime/quote/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data
    assert "price" in data
    assert "data_status" in data

def test_realtime_status_endpoint():
    response = client.get("/api/realtime/status")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "configured" in data
    assert "connection_status" in data

def test_finnhub_lifecycle_and_security():
    """Verifies async start/stop lifecycle and token redaction safety."""
    async def run_test():
        provider = RealTimeWebSocketProvider()
        provider.api_key = "test_finnhub_token_12345"

        assert provider.is_configured() is True

        # Test subscribe mapping
        provider.subscribe("BTC-USD")
        assert "BINANCE:BTCUSDT" in provider.subscribed_symbols

        # Test start and stop async lifecycle
        await provider.start()
        assert provider._running is True

        status = provider.get_stream_status()
        assert status["configured"] is True
        assert status["provider"] == "FINNHUB"
        # Ensure token is never in status payload string
        assert "test_finnhub_token_12345" not in str(status)

        await provider.stop()
        assert provider._running is False

    asyncio.run(run_test())


