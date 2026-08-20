"""
StockSense AI — Asset Registry Configuration
Defines supported asset classes, 21 initial multi-asset configurations, and metadata lookup.
"""

from typing import Dict, Any, List, Optional

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

# Configured Initial Universe (21 Assets)
ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {
    # 1. Indian Equities (NSE)
    "RELIANCE": {
        "symbol": "RELIANCE",
        "display_name": "Reliance Industries Ltd",
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "RELIANCE.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "TCS": {
        "symbol": "TCS",
        "display_name": "Tata Consultancy Services Ltd",
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "TCS.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "INFY": {
        "symbol": "INFY",
        "display_name": "Infosys Limited",
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "INFY.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "HDFCBANK": {
        "symbol": "HDFCBANK",
        "display_name": "HDFC Bank Limited",
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "HDFCBANK.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "ICICIBANK": {
        "symbol": "ICICIBANK",
        "display_name": "ICICI Bank Limited",
        "asset_class": "INDIAN_EQUITY",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "ICICIBANK.NS",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },

    # 2. US Equities
    "AAPL": {
        "symbol": "AAPL",
        "display_name": "Apple Inc.",
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "AAPL",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "MSFT": {
        "symbol": "MSFT",
        "display_name": "Microsoft Corporation",
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "MSFT",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "NVDA": {
        "symbol": "NVDA",
        "display_name": "NVIDIA Corporation",
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "NVDA",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "AMZN": {
        "symbol": "AMZN",
        "display_name": "Amazon.com Inc.",
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "AMZN",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "display_name": "Alphabet Inc.",
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "GOOGL",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },

    # 3. Cryptocurrency (24/7)
    "BTC-USD": {
        "symbol": "BTC-USD",
        "display_name": "Bitcoin / US Dollar",
        "asset_class": "CRYPTO",
        "exchange": "CRYPTO_GLOBAL",
        "market": "Global Crypto",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "BTC-USD",
        "active": True,
        "trading_calendar": "24/7",
        "timezone": "UTC"
    },
    "ETH-USD": {
        "symbol": "ETH-USD",
        "display_name": "Ethereum / US Dollar",
        "asset_class": "CRYPTO",
        "exchange": "CRYPTO_GLOBAL",
        "market": "Global Crypto",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "ETH-USD",
        "active": True,
        "trading_calendar": "24/7",
        "timezone": "UTC"
    },

    # 4. Foreign Exchange (Forex)
    "USDINR=X": {
        "symbol": "USDINR=X",
        "display_name": "US Dollar / Indian Rupee",
        "asset_class": "FOREX",
        "exchange": "FOREX_OTC",
        "market": "Forex",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "USDINR=X",
        "active": True,
        "trading_calendar": "FOREX_24/5",
        "timezone": "UTC"
    },
    "EURUSD=X": {
        "symbol": "EURUSD=X",
        "display_name": "Euro / US Dollar",
        "asset_class": "FOREX",
        "exchange": "FOREX_OTC",
        "market": "Forex",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "EURUSD=X",
        "active": True,
        "trading_calendar": "FOREX_24/5",
        "timezone": "UTC"
    },
    "GBPUSD=X": {
        "symbol": "GBPUSD=X",
        "display_name": "British Pound / US Dollar",
        "asset_class": "FOREX",
        "exchange": "FOREX_OTC",
        "market": "Forex",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "GBPUSD=X",
        "active": True,
        "trading_calendar": "FOREX_24/5",
        "timezone": "UTC"
    },
    "USDJPY=X": {
        "symbol": "USDJPY=X",
        "display_name": "US Dollar / Japanese Yen",
        "asset_class": "FOREX",
        "exchange": "FOREX_OTC",
        "market": "Forex",
        "currency": "JPY",
        "currency_symbol": "¥",
        "provider_symbol": "USDJPY=X",
        "active": True,
        "trading_calendar": "FOREX_24/5",
        "timezone": "UTC"
    },

    # 5. Global Market Indices
    "^NSEI": {
        "symbol": "^NSEI",
        "display_name": "NIFTY 50 Index",
        "asset_class": "INDEX",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "^NSEI",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "^NSEBANK": {
        "symbol": "^NSEBANK",
        "display_name": "NIFTY Bank Index",
        "asset_class": "INDEX",
        "exchange": "NSE",
        "market": "India",
        "currency": "INR",
        "currency_symbol": "₹",
        "provider_symbol": "^NSEBANK",
        "active": True,
        "trading_calendar": "NSE",
        "timezone": "Asia/Kolkata"
    },
    "^GSPC": {
        "symbol": "^GSPC",
        "display_name": "S&P 500 Index",
        "asset_class": "INDEX",
        "exchange": "US_INDEX",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "^GSPC",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "^IXIC": {
        "symbol": "^IXIC",
        "display_name": "NASDAQ Composite Index",
        "asset_class": "INDEX",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "^IXIC",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    },
    "^DJI": {
        "symbol": "^DJI",
        "display_name": "Dow Jones Industrial Average",
        "asset_class": "INDEX",
        "exchange": "NYSE",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": "^DJI",
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    }
}

def get_asset_info(symbol: str) -> Optional[Dict[str, Any]]:
    """Retrieves asset metadata by symbol or provider symbol."""
    clean_sym = symbol.upper().strip()
    if clean_sym in ASSET_REGISTRY:
        return ASSET_REGISTRY[clean_sym]
    
    for s, info in ASSET_REGISTRY.items():
        if info["provider_symbol"].upper() == clean_sym:
            return info
    return None

def get_assets_by_class(asset_class: str) -> List[Dict[str, Any]]:
    """Returns all active assets belonging to a specified asset class."""
    clean_cls = asset_class.upper().strip()
    return [info for info in ASSET_REGISTRY.values() if info["asset_class"] == clean_cls and info["active"]]

def get_all_assets() -> List[Dict[str, Any]]:
    """Returns all registered active assets."""
    return [info for info in ASSET_REGISTRY.values() if info["active"]]
