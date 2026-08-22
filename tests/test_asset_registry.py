import pytest
from backend.assets.asset_registry import (
    ASSET_REGISTRY, ASSET_CLASSES, get_asset_info, get_assets_by_class, get_all_assets
)

def test_all_21_assets_configured():
    """Verifies that at least 21 multi-asset configurations are registered in universe."""
    all_assets = get_all_assets()
    assert len(all_assets) >= 21, f"Expected at least 21 registered assets, got {len(all_assets)}"

def test_asset_classes_membership():
    """Verifies that every registered asset belongs to a valid asset class."""
    valid_classes = set(ASSET_CLASSES.keys())
    for info in ASSET_REGISTRY.values():
        assert info["asset_class"] in valid_classes, f"Invalid asset class {info['asset_class']} for {info['symbol']}"

def test_asset_metadata_completeness():
    """Verifies that all required metadata fields are present for every asset."""
    required_fields = [
        "symbol", "display_name", "asset_class", "exchange", "market",
        "currency", "currency_symbol", "provider_symbol", "active", "trading_calendar", "timezone"
    ]
    for sym, info in ASSET_REGISTRY.items():
        for f in required_fields:
            assert f in info, f"Missing field '{f}' in asset registry for '{sym}'"

def test_asset_lookup():
    """Verifies lookup by symbol and provider symbol."""
    reliance = get_asset_info("RELIANCE")
    assert reliance is not None
    assert reliance["provider_symbol"] == "RELIANCE.NS"

    btc = get_asset_info("BTC-USD")
    assert btc is not None
    assert btc["asset_class"] == "CRYPTO"

def test_get_assets_by_class():
    """Verifies asset class filtering."""
    us_equities = get_assets_by_class("US_EQUITY")
    assert len(us_equities) >= 5
    symbols = [a["symbol"] for a in us_equities]
    assert "AAPL" in symbols
    assert "NVDA" in symbols
