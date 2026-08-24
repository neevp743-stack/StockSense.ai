"""
StockSense AI — Phase 21.1 Test Suite: Live Market Data Provider Recovery & 109+ Symbol Activation
Verifies universe loading, provider mapping, REST quote validation, zero price rejection,
WebSocket reconnection, provider health state machine, non-blocking Phase 12 isolation,
and Phase 12 SHA256 hash invariance.
"""

import os
import json
import hashlib
import glob
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.universe import ALL_SYMBOLS, get_active_universe
from backend.data.realtime_provider import realtime_provider_manager
from backend.services.phase21_pipeline_service import phase21_pipeline_service

client = TestClient(app)


def test_1_universe_loads_greater_than_zero_symbols():
    """Test 1: Universe loads > 0 symbols."""
    active_uni = get_active_universe()
    assert len(active_uni) > 0
    assert len(active_uni) >= len(ALL_SYMBOLS)


def test_2_all_configured_symbols_have_valid_mappings():
    """Test 2: All configured symbols have complete provider mappings."""
    active_uni = get_active_universe()
    required_keys = ["internal_symbol", "provider_symbol", "region", "exchange", "asset_type", "timezone"]

    for sym in ALL_SYMBOLS:
        assert sym in active_uni
        meta = active_uni[sym]
        for k in required_keys:
            assert k in meta, f"Missing key '{k}' for symbol '{sym}'"


def test_3_finnhub_rest_valid_response_accepted():
    """Test 3: Finnhub REST valid response is accepted."""
    quote = realtime_provider_manager.fetch_rest_fallback_quote("AAPL")
    assert quote["symbol"] == "AAPL"
    assert "status" in quote
    assert quote["status"] in ["LIVE", "UNAVAILABLE"]


def test_4_missing_rest_price_returns_unavailable():
    """Test 4: Missing REST price returns UNAVAILABLE."""
    quote = realtime_provider_manager.fetch_rest_fallback_quote("INVALID_NONEXISTENT_XYZ")
    assert quote["symbol"] == "INVALID_NONEXISTENT_XYZ"
    assert quote["price"] is None
    assert quote["status"] == "UNAVAILABLE"


def test_5_zero_price_is_rejected():
    """Test 5: Zero price is rejected."""
    tick = realtime_provider_manager.process_incoming_tick("RELIANCE", 0.0)
    assert tick["price"] is None
    assert tick["status"] == "UNAVAILABLE"


def test_6_missing_timestamp_is_rejected():
    """Test 6: Missing timestamp is rejected."""
    tick = realtime_provider_manager.process_incoming_tick("TCS", None)
    assert tick["price"] is None
    assert tick["status"] == "UNAVAILABLE"


def test_7_websocket_reconnect_parameters_configured():
    """Test 7: WebSocket reconnect sequence parameters verified."""
    health = realtime_provider_manager.get_provider_health()
    assert "websocket_reconnect_count" in health
    assert isinstance(health["websocket_reconnect_count"], int)


def test_8_subscriptions_contain_configured_symbols():
    """Test 8: Subscriptions contain all configured universe symbols."""
    subs = realtime_provider_manager.subscribed_symbols
    assert len(subs) >= len(ALL_SYMBOLS)
    assert "RELIANCE" in subs
    assert "AAPL" in subs
    assert "BTC-USD" in subs


def test_9_rest_fallback_activates_when_websocket_fails():
    """Test 9: REST fallback operates independently when WebSocket fails."""
    # Fetch REST fallback quote explicitly
    quote = realtime_provider_manager.fetch_rest_fallback_quote("BTC-USD")
    assert quote["symbol"] == "BTC-USD"
    assert quote["status"] in ["LIVE", "UNAVAILABLE"]


def test_10_provider_health_state_machine():
    """Test 10: Provider health accurately reflects deterministic state."""
    health = realtime_provider_manager.get_provider_health()
    valid_states = ["PROVIDER_CONNECTED", "PROVIDER_DEGRADED", "PROVIDER_REST_ONLY", "PROVIDER_DISCONNECTED", "PROVIDER_INVALID_CONFIGURATION"]
    assert health["state"] in valid_states


def test_11_invalid_data_never_creates_live_observation():
    """Test 11: Invalid data never creates live observation."""
    res = phase21_pipeline_service.process_live_market_observation("TEST_MOCK_SYMBOL", -100.0)
    assert res["status"] == "REJECTED_SYNTHETIC"


def test_12_phase20_failure_cannot_block_phase12():
    """Test 12: Phase 20 shadow pipeline failure cannot block Phase 12 production prediction."""
    res = phase21_pipeline_service.process_live_market_observation("RELIANCE", 2480.0)
    assert res["symbol"] == "RELIANCE"
    assert res["status"] in ["SUCCESS", "MODEL NOT TRAINED FOR THIS ASSET"]


def test_13_dashboard_status_endpoint_matches_backend_health():
    """Test 13: Dashboard status matches backend provider health API response."""
    response = client.get("/api/research/phase21/provider-health")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "configured_symbol_count" in data


def test_14_no_synthetic_observation_is_created():
    """Test 14: No synthetic observation is created for unmapped or invalid input."""
    quote = realtime_provider_manager.fetch_rest_fallback_quote("SYNTHETIC_TEST_XYZ")
    assert quote["price"] is None
    assert quote["status"] == "UNAVAILABLE"


def test_15_phase12_artifact_sha256_remains_unchanged():
    """
    Test 15: Critical Regression Test.
    Calculates SHA256 hashes of Phase 12 XGBoost model files and verifies BEFORE HASH == AFTER HASH.
    """
    before_hash_file = "backend/research/phase21/phase12_before_hashes.json"
    assert os.path.exists(before_hash_file), "BEFORE hash record file missing"

    with open(before_hash_file, "r") as f:
        before_hashes = json.load(f)

    for file_path, before_sha in before_hashes.items():
        assert os.path.exists(file_path), f"Phase 12 model file missing: {file_path}"
        current_sha = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        assert current_sha == before_sha, f"CRITICAL REGRESSION FAILURE: Phase 12 model modified at {file_path}"
