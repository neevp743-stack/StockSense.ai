"""
StockSense AI — Scalable Asset Registry Configuration
Maintains asset classes, expanded multi-asset universe, and dynamic symbol resolution.
"""

from typing import Dict, Any, List, Optional
from backend.assets.provider_symbol_mapper import (
    INDIAN_EQUITY_SYMBOLS, US_EQUITY_SYMBOLS, CRYPTO_SYMBOLS, 
    FOREX_SYMBOLS, INDEX_SYMBOLS, infer_asset_metadata, get_internal_symbol
)

ASSET_CLASSES = {
    "INDIAN_EQUITY": {
        "name": "Indian Equities (NSE)",
        "default_currency": "INR",
        "currency_symbol": "₹",
        "trading_calendar": "NSE"
    },
    "US_EQUITY": {
        "name": "US Equities (NASDAQ/NYSE)",
        "default_currency": "USD",
        "currency_symbol": "$",
        "trading_calendar": "US_EQUITY"
    },
    "CRYPTO": {
        "name": "Cryptocurrency 24/7",
        "default_currency": "USD",
        "currency_symbol": "$",
        "trading_calendar": "24/7"
    },
    "FOREX": {
        "name": "Foreign Exchange Pairs",
        "default_currency": "USD",
        "currency_symbol": "$",
        "trading_calendar": "FOREX_24/5"
    },
    "INDEX": {
        "name": "Global Market Indices",
        "default_currency": "USD",
        "currency_symbol": "$",
        "trading_calendar": "INDEX_SESSION"
    }
}

# Pre-populate Expanded Initial Universe
ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Populate Indian Equities
for sym, name in INDIAN_EQUITY_SYMBOLS.items():
    ASSET_REGISTRY[sym] = {
        "symbol": sym,
        "display_name": name,
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": f"{sym}.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    }

# Populate US Equities
for sym, name in US_EQUITY_SYMBOLS.items():
    ASSET_REGISTRY[sym] = {
        "symbol": sym,
        "display_name": name,
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": sym,
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    }

# Populate Crypto
for sym, name in CRYPTO_SYMBOLS.items():
    ASSET_REGISTRY[sym] = {
        "symbol": sym,
        "display_name": name,
        "asset_class": "CRYPTO",
        "exchange": "CRYPTO_GLOBAL",
        "market": "Global Crypto",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": sym,
        "active": True,
        "trading_calendar": "24/7",
        "timezone": "UTC"
    }

# Populate Forex
for sym, name in FOREX_SYMBOLS.items():
    ASSET_REGISTRY[sym] = {
        "symbol": sym,
        "display_name": name,
        "asset_class": "FOREX",
        "exchange": "FOREX_OTC",
        "market": "Forex",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": sym,
        "active": True,
        "trading_calendar": "FOREX_24/5",
        "timezone": "UTC"
    }

# Populate Indices
for sym, name in INDEX_SYMBOLS.items():
    ASSET_REGISTRY[sym] = {
        "symbol": sym,
        "display_name": name,
        "asset_class": "INDEX",
        "exchange": "NSE" if "^NSE" in sym or "^BSE" in sym else "NASDAQ",
        "market": "India" if "^NSE" in sym or "^BSE" in sym else "US",
        "currency": "INR" if "^NSE" in sym or "^BSE" in sym else "USD",
        "currency_symbol": "₹" if "^NSE" in sym or "^BSE" in sym else "$",
        "provider_symbol": sym,
        "active": True,
        "trading_calendar": "NSE" if "^NSE" in sym or "^BSE" in sym else "US_EQUITY",
        "timezone": "Asia/Kolkata" if "^NSE" in sym or "^BSE" in sym else "America/New_York"
    }

def get_asset_info(symbol: str) -> Optional[Dict[str, Any]]:
    """Retrieves asset metadata by symbol or provider symbol, dynamically registering if unknown."""
    if not symbol:
        return None
    clean_sym = get_internal_symbol(symbol)

    if clean_sym in ASSET_REGISTRY:
        return ASSET_REGISTRY[clean_sym]
    
    for s, info in ASSET_REGISTRY.items():
        if info["provider_symbol"].upper() == clean_sym.upper():
            return info

    # Dynamically resolve and auto-register new requested symbol
    inferred = infer_asset_metadata(clean_sym)
    ASSET_REGISTRY[inferred["symbol"]] = inferred
    return inferred

def get_assets_by_class(asset_class: str) -> List[Dict[str, Any]]:
    """Returns all active assets belonging to a specified asset class."""
    clean_cls = asset_class.upper().strip()
    return [info for info in ASSET_REGISTRY.values() if info["asset_class"] == clean_cls and info["active"]]

def get_all_assets() -> List[Dict[str, Any]]:
    """Returns all registered active assets."""
    return [info for info in ASSET_REGISTRY.values() if info["active"]]

def search_assets(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Case-insensitive search over symbol and company display_name.
    """
    if not query or not query.strip():
        return get_all_assets()[:limit]

    q = query.lower().strip()
    matches = []

    # Priority 1: Exact symbol match
    for sym, info in ASSET_REGISTRY.items():
        if sym.lower() == q:
            matches.append(info)

    # Priority 2: Symbol starts with query
    for sym, info in ASSET_REGISTRY.items():
        if sym.lower().startswith(q) and info not in matches:
            matches.append(info)

    # Priority 3: Name contains query
    for sym, info in ASSET_REGISTRY.items():
        if q in info["display_name"].lower() and info not in matches:
            matches.append(info)

    # Priority 4: Dynamic fallback resolution if query looks like a valid stock ticker and no matches found
    if not matches and len(q) >= 2 and q.isalnum():
        dynamic_asset = get_asset_info(query)
        if dynamic_asset:
            matches.append(dynamic_asset)

    return matches[:limit]
