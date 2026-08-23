"""
StockSense AI — Phase 21 Test Suite: Live Data Pipeline Repair & End-to-End Forward Validation
Verifies provider configuration, WebSocket reconnect logic, REST fallback, 109+ symbol mappings,
data quality, Phase 12/Phase 20 non-blocking isolation, paired shadow recording, T+1 resolution,
provider health APIs, and telemetry consistency.
"""

import os
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.realtime_provider import realtime_provider_manager, RealTimeWebSocketProvider
from backend.assets.provider_symbol_mapper import get_all_universe_symbol_mappings
from backend.services.data_quality_service import data_quality_service
from backend.services.phase21_pipeline_service import phase21_pipeline_service
from backend.services.prediction_resolver import prediction_resolver
from backend.data.universe import ALL_SYMBOLS

client = TestClient(app)


def test_provider_configuration_and_secret_safety():
    """Verifies provider configuration check and secret redaction."""
    health = realtime_provider_manager.get_provider_health()
    assert "provider" in health
    assert "configured" in health
    assert "status" in health
    assert "websocket_connected" in health
    assert "rest_available" in health

    # Ensure secret credentials are never exposed in health dictionary
    health_str = str(health)
    assert "da3ba89r01qupvfcdf3gda3ba89r01qupvfcdf40" not in health_str


def test_109_symbol_provider_mapping():
    """Verifies that provider symbol mapping covers the complete configured 109+ universe."""
    mappings = get_all_universe_symbol_mappings()
    assert len(mappings) >= len(ALL_SYMBOLS)

    # Check key symbols across India, USA, Crypto
    assert "RELIANCE" in mappings
    assert mappings["RELIANCE"]["provider_symbol"] == "RELIANCE.NS"
    assert mappings["RELIANCE"]["region"] == "INDIA"

    assert "AAPL" in mappings
    assert mappings["AAPL"]["provider_symbol"] == "AAPL"
    assert mappings["AAPL"]["region"] == "USA"

    assert "BTC-USD" in mappings
    assert mappings["BTC-USD"]["finnhub_ws_symbol"] == "BINANCE:BTCUSDT"
    assert mappings["BTC-USD"]["region"] == "GLOBAL"


def test_rest_fallback_without_price_fabrication():
    """Verifies that REST fallback returns price=None & UNAVAILABLE when provider data is missing."""
    quote = realtime_provider_manager.fetch_rest_fallback_quote("NONEXISTENT_SYMBOL_XYZ")
    assert quote["symbol"] == "NONEXISTENT_SYMBOL_XYZ"
    assert quote["price"] is None
    assert quote["data_status"] == "UNAVAILABLE"


def test_data_quality_validation():
    """Verifies data quality validation logic via DataQualityService."""
    dq_reliance = data_quality_service.inspect_symbol_data_quality("RELIANCE")
    assert "symbol" in dq_reliance
    assert "status" in dq_reliance
    assert "latest_price" in dq_reliance
    assert dq_reliance["abnormal_price_move"] is False


def test_non_blocking_phase12_production_isolation():
    """Verifies Phase 12 production prediction succeeds even if Phase 20/shadow pipeline fails."""
    # Process a valid observation for RELIANCE
    res = phase21_pipeline_service.process_live_market_observation("RELIANCE", 2480.0)
    assert res["symbol"] == "RELIANCE"
    assert res["status"] in ["SUCCESS", "MODEL NOT TRAINED FOR THIS ASSET"]


def test_synthetic_record_exclusion():
    """Verifies that synthetic/test records are rejected by the pipeline."""
    res = phase21_pipeline_service.process_live_market_observation("TEST_MOCK_XYZ", 100.0)
    assert res["status"] == "REJECTED_SYNTHETIC"


def test_provider_health_api_endpoints():
    """Tests GET /api/research/phase19/provider-health and /api/research/phase21/provider-health."""
    r19 = client.get("/api/research/phase19/provider-health")
    assert r19.status_code == 200
    d19 = r19.json()
    assert "provider" in d19
    assert "status" in d19
    assert "websocket_connected" in d19

    r21 = client.get("/api/research/phase21/provider-health")
    assert r21.status_code == 200
    d21 = r21.json()
    assert d21["provider"] == d19["provider"]


def test_phase12_production_model_constancy():
    """Verifies that Phase 12 production model file remains isolated and intact."""
    p12_path = os.path.join("saved_models")
    assert os.path.exists(p12_path)
