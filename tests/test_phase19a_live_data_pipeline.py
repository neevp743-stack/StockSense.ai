"""
StockSense AI — Phase 19A Unit & Integration Test Suite
Verifies backend status and symbol diagnostic endpoints for Phase 19A Live Data Pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_provider_state():
    from backend.data.realtime_provider import realtime_provider_manager
    realtime_provider_manager.connection_status = "CONNECTED"
    realtime_provider_manager.ws_url = "wss://ws.finnhub.io"
    if not realtime_provider_manager.api_key:
        realtime_provider_manager.api_key = "mock_token"
    try:
        realtime_provider_manager.tick_cache.clear()
    except Exception:
        pass
    yield
    realtime_provider_manager._connection_status_override = None


def test_phase19a_overall_status_endpoint():
    """Tests GET /api/research/phase19a/status endpoint schema and data structure."""
    response = client.get("/api/research/phase19a/status")
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "RESEARCH"
    assert data["phase"] == "PHASE19A"
    assert data["provider"] == "FINNHUB"
    assert data["websocket_status"] in ["CONNECTED", "DISCONNECTED", "CONNECTING"]
    assert data["rest_fallback_status"] in ["ACTIVE", "STANDBY", "FAILED"]

    symbol_counts = data["symbol_counts"]
    assert "total_symbols" in symbol_counts
    assert "live_symbols" in symbol_counts
    assert "delayed_symbols" in symbol_counts
    assert "stale_symbols" in symbol_counts
    assert "unavailable_symbols" in symbol_counts

    shadow_pipeline = data["shadow_pipeline"]
    assert "observations_today" in shadow_pipeline
    assert "paired_observations" in shadow_pipeline
    assert "failed_observations" in shadow_pipeline
    assert "pipeline_status" in shadow_pipeline
    assert shadow_pipeline["pipeline_status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE"]


@pytest.mark.parametrize("symbol", [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "AAPL", "NVDA", "BTC-USD"
])
def test_phase19a_symbol_diagnostics_endpoints(symbol):
    """Tests GET /api/research/phase19a/{symbol} for all required diagnostic symbols."""
    response = client.get(f"/api/research/phase19a/{symbol}")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == symbol
    assert "live_data" in data
    assert "prediction_pipeline" in data
    assert "database" in data
    assert "diagnostics" in data

    live_data = data["live_data"]
    assert live_data["provider"] == "FINNHUB"
    assert live_data["websocket_status"] in ["CONNECTED", "DISCONNECTED", "CONNECTING"]
    assert live_data["rest_fallback_status"] in ["ACTIVE", "STANDBY", "FAILED"]
    assert live_data["data_status"] in ["LIVE", "DELAYED", "STALE", "UNAVAILABLE"]

    pred_pipe = data["prediction_pipeline"]
    assert pred_pipe["champion_status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE"]
    assert pred_pipe["challenger_status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE"]

    db_stats = data["database"]
    assert "observations" in db_stats
    assert "paired_observations" in db_stats
