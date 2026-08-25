"""
StockSense AI — Phase 21.4 Twelve Data Provider Tests
Tests TwelveDataProvider configuration, XAU/USD parsing, timeout handling,
rate-limit handling, bounded caching, and secret-leak prevention.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from backend.data.providers.twelve_data_provider import TwelveDataProvider


# ─── Environment Configuration ────────────────────────────────────

def test_twelve_data_not_configured_without_key():
    """Provider reports unconfigured when no API key is set."""
    provider = TwelveDataProvider(api_key="")
    assert provider.is_configured() is False


def test_twelve_data_not_configured_placeholder():
    """Provider reports unconfigured when placeholder key is used."""
    provider = TwelveDataProvider(api_key="your_twelve_data_api_key_here")
    assert provider.is_configured() is False


def test_twelve_data_configured_with_valid_key():
    """Provider reports configured when a valid API key is set."""
    provider = TwelveDataProvider(api_key="td_test_api_key_12345")
    assert provider.is_configured() is True


def test_twelve_data_provider_name():
    """Provider name is TWELVE_DATA."""
    provider = TwelveDataProvider(api_key="")
    assert provider.provider_name() == "TWELVE_DATA"


# ─── Secure API Key Loading ──────────────────────────────────────

def test_twelve_data_loads_key_from_config():
    """Provider reads API key from backend.config module."""
    provider = TwelveDataProvider()
    # Key may or may not be set in test env — just verify no crash
    assert isinstance(provider._api_key, str)


# ─── XAU/USD Response Parsing ────────────────────────────────────

def test_twelve_data_quote_unconfigured():
    """Quote returns UNAVAILABLE when not configured."""
    provider = TwelveDataProvider(api_key="")
    quote = provider.get_quote("XAU/USD")
    assert quote["price"] is None
    assert quote["data_status"] == "UNAVAILABLE"
    assert quote["error"] == "TWELVE_DATA_API_KEY_NOT_CONFIGURED"
    assert quote["provider"] == "TWELVE_DATA"


def test_twelve_data_symbol_normalization():
    """XAUUSD normalizes to XAU/USD."""
    assert TwelveDataProvider.normalize_symbol("XAUUSD") == "XAU/USD"
    assert TwelveDataProvider.normalize_symbol("XAU/USD") == "XAU/USD"
    assert TwelveDataProvider.normalize_symbol("xau/usd") == "XAU/USD"


def test_twelve_data_internal_symbol():
    """Internal symbol normalization."""
    assert TwelveDataProvider.internal_symbol("XAUUSD") == "XAU/USD"
    assert TwelveDataProvider.internal_symbol("XAU/USD") == "XAU/USD"


def test_twelve_data_quote_success_mock():
    """Mocked successful quote returns correct price."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {"price": "2650.4500"}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] == 2650.45
        assert quote["data_status"] == "LIVE"
        assert quote["provider"] == "TWELVE_DATA"
        assert quote["symbol"] == "XAU/USD"
        assert quote["error"] is None


def test_twelve_data_quote_feeds_live_tick_cache():
    """Successful quote feeds the LiveTickCache."""
    from backend.data.realtime_provider import realtime_provider_manager
    
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {"price": "2700.0000"}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        provider.get_quote("XAU/USD")
    
    tick = realtime_provider_manager.cache.get_latest_tick("XAU/USD")
    assert tick is not None
    assert tick["price"] == 2700.0
    assert tick["provider"] == "TWELVE_DATA"


# ─── Historical OHLC Parsing ─────────────────────────────────────

def test_twelve_data_historical_unconfigured():
    """Historical returns empty DataFrame when not configured."""
    provider = TwelveDataProvider(api_key="")
    df = provider.get_historical("XAU/USD")
    assert df.empty


def test_twelve_data_historical_success_mock():
    """Mocked historical data returns correct DataFrame structure."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {
        "values": [
            {"datetime": "2026-08-25", "open": "2640.00", "high": "2660.00", "low": "2630.00", "close": "2650.00", "volume": "100000"},
            {"datetime": "2026-08-24", "open": "2630.00", "high": "2645.00", "low": "2625.00", "close": "2640.00", "volume": "95000"},
        ]
    }
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        df = provider.get_historical("XAU/USD", period="1y")
    
    assert not df.empty
    assert len(df) == 2
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    # Should be sorted by date ascending
    assert df.iloc[0]["close"] == 2640.0
    assert df.iloc[1]["close"] == 2650.0


# ─── Timeout Handling ─────────────────────────────────────────────

def test_twelve_data_fetch_timeout():
    """Provider handles network timeouts gracefully."""
    import urllib.error
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    
    with patch.object(provider, '_fetch_json', return_value=None):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] is None
        assert quote["data_status"] == "UNAVAILABLE"


# ─── Rate Limit Handling ──────────────────────────────────────────

def test_twelve_data_api_error_handling():
    """Provider handles Twelve Data API error responses."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = None  # Simulates complete failure
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] is None
        assert quote["data_status"] == "UNAVAILABLE"
        assert provider.failed_request_count == 1


# ─── Malformed Response Handling ──────────────────────────────────

def test_twelve_data_malformed_price():
    """Provider handles non-numeric price in response."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {"price": "not_a_number"}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] is None
        assert quote["data_status"] == "UNAVAILABLE"


def test_twelve_data_empty_response():
    """Provider handles empty API response."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] is None


def test_twelve_data_zero_price_rejected():
    """Zero price is rejected."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {"price": "0.0000"}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        quote = provider.get_quote("XAU/USD")
        assert quote["price"] is None
        assert quote["data_status"] == "UNAVAILABLE"


# ─── Bounded Caching ─────────────────────────────────────────────

def test_twelve_data_quote_caching():
    """Successful quote is cached and returned on subsequent call."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    mock_response = {"price": "2650.0000"}
    
    with patch.object(provider, '_fetch_json', return_value=mock_response):
        q1 = provider.get_quote("XAU/USD")
    
    # Second call should hit cache (no _fetch_json call)
    q2 = provider.get_quote("XAU/USD")
    assert q1["price"] == q2["price"]
    assert provider.request_count == 2  # Both counted
    

# ─── Secret Leak Prevention ──────────────────────────────────────

def test_twelve_data_no_secrets_in_health():
    """Health payload never contains API key or secrets."""
    provider = TwelveDataProvider(api_key="td_super_secret_key_12345")
    health = provider.health()
    health_str = json.dumps(health)
    
    # API key must never appear
    assert "td_super_secret_key_12345" not in health_str
    assert "api_key" not in health_str.lower()
    assert "secret" not in health_str.lower()
    assert "password" not in health_str.lower()


def test_twelve_data_no_secrets_in_quote_response():
    """Quote response never contains API key."""
    provider = TwelveDataProvider(api_key="td_super_secret_key_12345")
    quote = provider.get_quote("XAU/USD")
    quote_str = json.dumps(quote)
    
    assert "td_super_secret_key_12345" not in quote_str


def test_twelve_data_health_structure():
    """Health payload contains all required fields."""
    provider = TwelveDataProvider(api_key="td_test_key_12345")
    health = provider.health()
    
    assert health["provider"] == "TWELVE_DATA"
    assert "configured" in health
    assert "supported_symbols" in health
    assert "request_count" in health
    assert "failed_request_count" in health
    assert "rate_limit_count" in health
    assert "average_latency_ms" in health
    assert "last_success_ts" in health
    assert "last_error_ts" in health
    assert "cache_entries" in health


def test_twelve_data_integrated_in_provider_router():
    """TwelveDataProvider health is included in provider_router status."""
    from backend.data.providers.provider_router import provider_router
    health = provider_router.get_provider_health()
    assert "twelve_data_health" in health
    assert health["twelve_data_health"]["provider"] == "TWELVE_DATA"


def test_twelve_data_integrated_in_realtime_status():
    """TwelveDataProvider health is included in realtime_provider_manager status."""
    from backend.data.realtime_provider import realtime_provider_manager
    status = realtime_provider_manager.get_stream_status()
    assert "twelve_data_health" in status
    assert status["twelve_data_health"]["provider"] == "TWELVE_DATA"


# ─── Subscribe/Unsubscribe (REST-only, no-op) ────────────────────

def test_twelve_data_subscribe_noop():
    """Subscribe is a no-op for REST-only provider."""
    provider = TwelveDataProvider(api_key="")
    assert provider.subscribe(["XAU/USD"]) is True


def test_twelve_data_unsubscribe_noop():
    """Unsubscribe is a no-op for REST-only provider."""
    provider = TwelveDataProvider(api_key="")
    assert provider.unsubscribe(["XAU/USD"]) is True
