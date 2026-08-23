"""
StockSense AI — Phase 17 Configurable Historical Market Universe
Defines large-scale multi-asset universe across India (NIFTY 50/100), US (S&P 500), and Crypto.
Handles ticker mapping, exchange conventions, and dynamic JSON/environment configuration.
"""

import os
import json
from typing import List, Dict, Any

# 1. NIFTY 50 & Top NIFTY 100 Indian Equities
INDIA_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT",
    "BHARTIARTL", "MARUTI", "KOTAKBANK", "AXISBANK", "LTIM", "HCLTECH", "ASIANPAINT",
    "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "NTPC", "ONGC", "POWERGRID",
    "TATAMOTORS", "TATASTEEL", "WIPRO", "ADANIENT", "ADANIPORTS", "COALINDIA", "GRASIM",
    "HINDALCO", "INDUSINDBK", "JSWSTEEL", "NESTLEIND", "HEROMOTOCO", "BAJAJ-AUTO",
    "EICHERMOT", "BPCL", "CIPLA", "DRREDDY", "DIVISLAB", "APOLLOHOSP", "BRITANNIA",
    "BEL", "HAL", "TRENT", "ZOMATO", "JIOFIN", "DLF", "VBL", "PIDILITIND",
    "SIEMENS", "HAVELLS", "AMBUJACEM", "BANKBARODA", "PNB", "CANBK", "GODREJCP"
]

# 2. S&P 500 & Top US Equities
US_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "AVGO",
    "JPM", "ELY", "V", "UNH", "MA", "XOM", "PG", "HD", "JNJ", "COST", "BAC",
    "ABBV", "CRM", "AMD", "NFLX", "CVX", "MRK", "WMT", "KO", "PEP", "ADBE",
    "TCM", "QCOM", "LIN", "BAC", "ACN", "MCD", "INTC", "CSCO", "DIS", "TXN",
    "PM", "NOW", "INTU", "AMAT", "DHR", "ISRG", "CAT", "PFE", "GE", "UBER"
]

# 3. Liquid Crypto Assets
CRYPTO_SYMBOLS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "AVAX-USD"
]

# 4. Master Combined Universe
ALL_SYMBOLS = sorted(list(set(INDIA_SYMBOLS + US_SYMBOLS + CRYPTO_SYMBOLS)))


def get_universe(region: str = "ALL") -> List[str]:
    """
    Returns configured symbol list for given region/asset class or ALL.
    Supports dynamic JSON universe file override via UNIVERSE_JSON_PATH env variable.
    """
    json_path = os.getenv("UNIVERSE_JSON_PATH")
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                custom_data = json.load(f)
                if isinstance(custom_data, list):
                    return custom_data
                elif isinstance(custom_data, dict) and region in custom_data:
                    return custom_data[region]
        except Exception:
            pass

    region_clean = region.upper().strip()
    if region_clean in ["INDIA", "IN", "NIFTY"]:
        return INDIA_SYMBOLS
    elif region_clean in ["USA", "US", "SP500"]:
        return US_SYMBOLS
    elif region_clean in ["CRYPTO", "CRYPTO_SYMBOLS"]:
        return CRYPTO_SYMBOLS
    return ALL_SYMBOLS


def get_provider_symbol(symbol: str) -> str:
    """
    Maps internal symbol to provider-compatible ticker (e.g. RELIANCE -> RELIANCE.NS).
    """
    sym_clean = symbol.upper().strip()
    if sym_clean in INDIA_SYMBOLS or (not sym_clean.endswith(".NS") and not "-" in sym_clean and sym_clean not in US_SYMBOLS):
        if not sym_clean.endswith(".NS"):
            return f"{sym_clean}.NS"
    return sym_clean


def get_internal_symbol_from_provider(provider_symbol: str) -> str:
    """
    Strips provider extensions to return standardized internal symbol.
    """
    if provider_symbol.endswith(".NS"):
        return provider_symbol.replace(".NS", "")
    return provider_symbol
