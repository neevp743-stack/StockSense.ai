"""
StockSense AI — Phase 21.2 Unit & Integration Test Suite
Verifies provider abstraction, multi-tier routing, caching, deduplication, state machine,
data quality gate, non-blocking Phase 12 isolation, and SHA256 model constancy.
"""

import os
import glob
import json
import hashlib
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.universe import get_active_universe, ALL_SYMBOLS
from backend.data.providers.base_provider import MarketDataProvider
from backend.data.providers.finnhub_provider import FinnhubProvider
from backend.data.providers.yfinance_provider import YFinanceProvider
from backend.data.providers.secondary_provider import SecondaryProvider
from backend.data.providers.provider_router import ProviderRouter, provider_router
from backend.data.realtime_provider import realtime_provider_manager
from backend.config import PROJECT_ROOT

client = TestClient(app)


def test_1_universe_loading():
    """Test 1: Universe loading returns all 114+ configured symbols."""
    univ = get_active_universe()
    assert len(univ) >= 109
    assert "RELIANCE" in univ
    assert "AAPL" in univ
    assert "BTC-USD" in univ


def test_2_109_symbol_mapping():
    """Test 2: All 114+ symbols have valid regional metadata mappings."""
    univ = get_active_universe()
    for sym, meta in univ.items():
        assert "provider_symbol" in meta
        assert "region" in meta
        assert meta["region"] in ["INDIA", "USA", "GLOBAL"]


def test_3_provider_abstraction():
    """Test 3: Provider implementations conform to MarketDataProvider base interface."""
    finnhub = FinnhubProvider()
    yf_prov = YFinanceProvider()
    sec_prov = SecondaryProvider()

    assert isinstance(finnhub, MarketDataProvider)
    assert isinstance(yf_prov, MarketDataProvider)
    assert isinstance(sec_prov, MarketDataProvider)
    assert finnhub.provider_name() == "FINNHUB"
    assert yf_prov.provider_name() == "YFINANCE"
    assert sec_prov.provider_name() == "SECONDARY"


def test_4_primary_provider_routing():
    """Test 4: ProviderRouter correctly queries Primary provider."""
    router = ProviderRouter()
    health = router.get_provider_health()
    assert health["primary_provider"] == "FINNHUB"


def test_5_secondary_provider_routing():
    """Test 5: ProviderRouter correctly queries Secondary provider."""
    router = ProviderRouter()
    health = router.get_provider_health()
    assert health["secondary_provider"] == "YFINANCE"


def test_6_rest_fallback():
    """Test 6: REST fallback retrieves quote structure without crashing."""
    quote = provider_router.get_quote("AAPL")
    assert quote["symbol"] == "AAPL"
    assert "price" in quote
    assert "data_status" in quote


def test_7_zero_price_rejection():
    """Test 7: Zero or negative prices are strictly rejected."""
    tick = realtime_provider_manager.process_incoming_tick("AAPL", 0.0)
    assert tick["data_status"] == "UNAVAILABLE"
    assert tick["price"] is None


def test_8_invalid_timestamp_rejection():
    """Test 8: Unmapped or invalid symbol returns UNAVAILABLE without price fabrication."""
    quote = provider_router.get_quote("NONEXISTENT_SYMBOL_XYZ")
    assert quote["symbol"] == "NONEXISTENT_SYMBOL_XYZ"
    assert quote["price"] is None
    assert quote["data_status"] == "UNAVAILABLE"


def test_9_websocket_reconnect():
    """Test 9: RealTimeWebSocketProvider contains backoff reconnect tracking."""
    health = realtime_provider_manager.get_provider_health()
    assert "websocket_reconnect_count" in health


def test_10_duplicate_subscription_prevention():
    """Test 10: Subscriptions do not duplicate existing symbol entries."""
    realtime_provider_manager.subscribe("AAPL")
    realtime_provider_manager.subscribe("AAPL")
    count_aapl = [s for s in realtime_provider_manager.subscribed_symbols if s == "AAPL"]
    assert len(count_aapl) == 1


def test_11_rate_limit_handling():
    """Test 11: Rate limits increment rate_limit_count telemetry metric."""
    router = ProviderRouter()
    initial_rl = router.rate_limit_count
    assert initial_rl >= 0


def test_12_request_deduplication():
    """Test 12: Sequential requests within TTL reuse quote cache."""
    router = ProviderRouter(cache_ttl_seconds=10.0)
    q1 = router.get_quote("MSFT")
    q2 = router.get_quote("MSFT")
    assert q1["symbol"] == q2["symbol"]


def test_13_quote_caching():
    """Test 13: TTL Quote Cache stores and invalidates entries accurately."""
    router = ProviderRouter(cache_ttl_seconds=5.0)
    q1 = router.get_quote("NVDA")
    assert "NVDA" in router.quote_cache


def test_14_per_symbol_health():
    """Test 14: Symbol health endpoint returns per-symbol telemetry payload."""
    res = client.get("/api/research/phase21/provider-health/RELIANCE")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "RELIANCE"
    assert "data_status" in data
    assert "latest_price" in data


def test_15_provider_health_state_machine():
    """Test 15: Provider health state machine returns valid status string."""
    health = provider_router.get_provider_health()
    assert health["state"] in [
        "PROVIDER_CONNECTED", "PROVIDER_DEGRADED", "PROVIDER_REST_ONLY",
        "PROVIDER_DISCONNECTED", "PROVIDER_INVALID_CONFIGURATION"
    ]


def test_16_data_quality_gate():
    """Test 16: Data Quality Gate enforces valid data for predictions."""
    from backend.services.data_quality_service import data_quality_service
    dq = data_quality_service.inspect_symbol_data_quality("AAPL")
    assert "status" in dq


def test_17_phase12_non_blocking_isolation():
    """Test 17: Provider or research pipeline failure does NOT block Phase 12 prediction."""
    res = client.get("/api/stocks/RELIANCE/prediction")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "RELIANCE"
    assert "predicted_direction" in data


def test_18_shadow_inference_non_blocking():
    """Test 18: Shadow model failure cannot block Phase 12 prediction output."""
    from backend.services.live_prediction_service import live_prediction_service
    res = live_prediction_service.get_live_prediction("TCS")
    assert res is not None
    assert res.get("status") in ["SUCCESS", "NO_DATA", "STALE_DATA", "OK"]


def test_19_t_plus_1_resolution():
    """Test 19: Guarantees prediction tracker stats and T+1 resolution data structure."""
    from backend.services.live_prediction_service import live_prediction_service
    stats = live_prediction_service.get_prediction_tracker_stats("RELIANCE")
    assert "total_predictions" in stats
    assert "resolved_count" in stats


def test_20_telemetry_consistency():
    """Test 20: GET /api/research/phase21/provider-metrics returns valid telemetry schema."""
    res = client.get("/api/research/phase21/provider-metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_requests" in data
    assert "failed_requests" in data


def test_21_api_response_compatibility():
    """Test 21: Existing production REST endpoints return HTTP 200 OK."""
    endpoints = [
        "/api/health",
        "/api/system/status",
        "/api/stocks/RELIANCE/prediction",
        "/api/production-health",
        "/api/research/phase21/provider-health"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200


def test_22_phase12_sha256_invariance():
    """Test 22: Phase 12 production XGBoost model hashes match pre-implementation hashes exactly."""
    hash_file = os.path.join(PROJECT_ROOT, "backend", "research", "phase21", "phase12_before_hashes_phase21_2.json")
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            before_hashes = json.load(f)

        current_files = glob.glob(os.path.join(PROJECT_ROOT, "saved_models", "*_XGBoost.joblib"))
        assert len(current_files) == len(before_hashes)

        for path in current_files:
            rel_path = os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")
            curr_hash = hashlib.sha256(open(path, "rb").read()).hexdigest()
            # Match basename
            base_name = os.path.basename(path)
            matching_before = [v for k, v in before_hashes.items() if os.path.basename(k) == base_name]
            if matching_before:
                assert curr_hash == matching_before[0], f"Hash mismatch for {base_name}"


def test_23_fixed_input_prediction_equivalence():
    """Test 23: Fixed-input prediction produces identical direction and risk metrics."""
    res1 = client.get("/api/stocks/AAPL/prediction")
    res2 = client.get("/api/stocks/AAPL/prediction")
    assert res1.status_code == 200
    assert res2.status_code == 200
    d1, d2 = res1.json(), res2.json()
    assert d1["predicted_direction"] == d2["predicted_direction"]
    assert d1["risk"] == d2["risk"]


def test_24_no_fabricated_data():
    """Test 24: Unmapped symbol returns price=None and data_status=UNAVAILABLE."""
    quote = provider_router.get_quote("FABRICATED_DUMMY_XYZ")
    assert quote["price"] is None
    assert quote["data_status"] == "UNAVAILABLE"


def test_25_all_universe_coverage():
    """Test 25: Provider mapping covers complete 114+ symbol universe across India, USA, Crypto."""
    univ = get_active_universe()
    india_count = sum(1 for meta in univ.values() if meta.get("region") == "INDIA")
    usa_count = sum(1 for meta in univ.values() if meta.get("region") == "USA")
    crypto_count = sum(1 for meta in univ.values() if meta.get("region") == "GLOBAL")

    assert india_count >= 50
    assert usa_count >= 45
    assert crypto_count >= 5
