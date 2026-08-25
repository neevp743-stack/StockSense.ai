"""
StockSense AI — Global Pytest Setup & Teardown
Ensures realtime_provider_manager is clean before AND after every test.
"""

import pytest

def reset_manager():
    from backend.data.realtime_provider import realtime_provider_manager
    realtime_provider_manager.connection_status = "CONNECTED"
    realtime_provider_manager.ws_url = "wss://ws.finnhub.io"
    if not realtime_provider_manager.api_key:
        realtime_provider_manager.api_key = "mock_token"
    try:
        realtime_provider_manager.tick_cache.clear()
    except Exception:
        pass
    # Reset Coinbase provider state
    try:
        cb = realtime_provider_manager._coinbase_provider
        cb.connected = False
        cb.tick_count = 0
        cb.candle_count = 0
        cb.heartbeat_count = 0
        cb.error_count = 0
        cb.reconnect_count = 0
        cb._started = False
        cb._running = False
    except Exception:
        pass

@pytest.fixture(autouse=True)
def global_reset_provider_state():
    reset_manager()
    yield
    reset_manager()
