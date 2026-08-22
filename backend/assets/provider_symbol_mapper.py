"""
StockSense AI — Centralized Provider Symbol Mapper
Maps internal symbols to external provider symbols (YFinance / Finnhub / AlphaVantage)
and auto-detects asset metadata on demand.
"""

from typing import Dict, Any, Tuple

# Known Indian Equities mapping
INDIAN_EQUITY_SYMBOLS = {
    "RELIANCE": "Reliance Industries Ltd",
    "TCS": "Tata Consultancy Services Ltd",
    "INFY": "Infosys Limited",
    "HDFCBANK": "HDFC Bank Limited",
    "ICICIBANK": "ICICI Bank Limited",
    "SBIN": "State Bank of India",
    "ITC": "ITC Limited",
    "LT": "Larsen & Toubro Ltd",
    "BHARTIARTL": "Bharti Airtel Ltd",
    "MARUTI": "Maruti Suzuki India Ltd",
    "KOTAKBANK": "Kotak Mahindra Bank Ltd",
    "AXISBANK": "Axis Bank Ltd",
    "LTIM": "LTIMindtree Ltd",
    "HCLTECH": "HCL Technologies Ltd",
    "ASIANPAINT": "Asian Paints Ltd",
    "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
    "TITAN": "Titan Company Ltd",
    "BAJFINANCE": "Bajaj Finance Ltd",
    "ULTRACEMCO": "UltraTech Cement Ltd",
    "NTPC": "NTPC Ltd",
    "ONGC": "Oil & Natural Gas Corporation Ltd",
    "POWERGRID": "Power Grid Corporation of India Ltd",
    "TATAMOTORS": "Tata Motors Ltd",
    "TATASTEEL": "Tata Steel Ltd",
    "WIPRO": "Wipro Ltd",
    "ADANIENT": "Adani Enterprises Ltd",
    "ADANIPORTS": "Adani Ports and Special Economic Zone Ltd",
    "COALINDIA": "Coal India Ltd",
    "GRASIM": "Grasim Industries Ltd",
    "HINDALCO": "Hindalco Industries Ltd",
    "INDUSINDBK": "IndusInd Bank Ltd",
    "JSWSTEEL": "JSW Steel Ltd",
    "NESTLEIND": "Nestle India Ltd",
    "HEROMOTOCO": "Hero MotoCorp Ltd",
    "BAJAJ-AUTO": "Bajaj Auto Ltd",
    "EICHERMOT": "Eicher Motors Ltd",
    "BPCL": "Bharat Petroleum Corporation Ltd",
    "CIPLA": "Cipla Ltd",
    "DRREDDY": "Dr. Reddy's Laboratories Ltd",
    "DIVISLAB": "Divi's Laboratories Ltd",
    "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
    "BRITANNIA": "Britannia Industries Ltd",
    "BEL": "Bharat Electronics Ltd",
    "HAL": "Hindustan Aeronautics Ltd",
    "TRENT": "Trent Ltd",
    "ZOMATO": "Zomato Ltd",
    "PAYTM": "One 97 Communications Ltd (Paytm)",
    "JIOFIN": "Jio Financial Services Ltd",
    "DLF": "DLF Ltd",
    "VBL": "Varun Beverages Ltd"
}

# Known US Equities mapping
US_EQUITY_SYMBOLS = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla, Inc.",
    "AMZN": "Amazon.com Inc.",
    "GOOGL": "Alphabet Inc. (Class A)",
    "GOOG": "Alphabet Inc. (Class C)",
    "META": "Meta Platforms, Inc.",
    "BRK-B": "Berkshire Hathaway Inc.",
    "LLY": "Eli Lilly and Company",
    "AVGO": "Broadcom Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "UNH": "UnitedHealth Group Inc.",
    "WMT": "Walmart Inc.",
    "XOM": "Exxon Mobil Corporation",
    "MA": "Mastercard Incorporated",
    "HD": "The Home Depot, Inc.",
    "PG": "The Procter & Gamble Company",
    "COST": "Costco Wholesale Corporation",
    "JNJ": "Johnson & Johnson",
    "ORCL": "Oracle Corporation",
    "BAC": "Bank of America Corp",
    "CRM": "Salesforce, Inc.",
    "ABBV": "AbbVie Inc.",
    "CVX": "Chevron Corporation",
    "NFLX": "Netflix, Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo, Inc."
}

# Known Crypto mapping
CRYPTO_SYMBOLS = {
    "BTC-USD": "Bitcoin / US Dollar",
    "ETH-USD": "Ethereum / US Dollar",
    "SOL-USD": "Solana / US Dollar",
    "BNB-USD": "BNB / US Dollar",
    "XRP-USD": "XRP / US Dollar",
    "ADA-USD": "Cardano / US Dollar",
    "DOGE-USD": "Dogecoin / US Dollar",
    "AVAX-USD": "Avalanche / US Dollar",
    "LINK-USD": "Chainlink / US Dollar",
    "DOT-USD": "Polkadot / US Dollar"
}

# Known Forex mapping
FOREX_SYMBOLS = {
    "USDINR=X": "US Dollar / Indian Rupee",
    "EURUSD=X": "Euro / US Dollar",
    "GBPUSD=X": "British Pound / US Dollar",
    "USDJPY=X": "US Dollar / Japanese Yen",
    "AUDUSD=X": "Australian Dollar / US Dollar",
    "USDCAD=X": "US Dollar / Canadian Dollar"
}

# Known Index mapping
INDEX_SYMBOLS = {
    "^NSEI": "NIFTY 50 Index",
    "^NSEBANK": "NIFTY Bank Index",
    "^BSESN": "SENSEX Index",
    "^GSPC": "S&P 500 Index",
    "^IXIC": "NASDAQ Composite Index",
    "^DJI": "Dow Jones Industrial Average"
}

def get_provider_symbol(symbol: str) -> str:
    """
    Returns the provider-specific ticker symbol.
    Example: RELIANCE -> RELIANCE.NS, AAPL -> AAPL, BTC-USD -> BTC-USD.
    """
    clean_sym = symbol.upper().strip()

    # If it ends with .NS, .BO, =X, -USD, or starts with ^, it's already a provider symbol
    if clean_sym.endswith(".NS") or clean_sym.endswith(".BO") or clean_sym.endswith("=X") or clean_sym.startswith("^"):
        return clean_sym

    # If it's a known Indian equity, append .NS for YFinance
    if clean_sym in INDIAN_EQUITY_SYMBOLS:
        return f"{clean_sym}.NS"

    return clean_sym

def get_internal_symbol(provider_symbol: str) -> str:
    """
    Strips provider-specific suffixes to return internal canonical symbol.
    Example: RELIANCE.NS -> RELIANCE.
    """
    clean_sym = provider_symbol.upper().strip()
    if clean_sym.endswith(".NS"):
        return clean_sym[:-3]
    if clean_sym.endswith(".BO"):
        return clean_sym[:-3]
    return clean_sym

def infer_asset_metadata(symbol: str) -> Dict[str, Any]:
    """
    Dynamically infers asset class, exchange, market, currency, and display name
    for any requested stock symbol.
    """
    clean_sym = symbol.upper().strip()
    internal_sym = get_internal_symbol(clean_sym)
    provider_sym = get_provider_symbol(clean_sym)

    # 1. Check Indian Equities
    if internal_sym in INDIAN_EQUITY_SYMBOLS or clean_sym.endswith(".NS"):
        disp_name = INDIAN_EQUITY_SYMBOLS.get(internal_sym, f"{internal_sym} Ltd")
        return {
            "symbol": internal_sym,
            "display_name": disp_name,
            "asset_class": "INDIAN_EQUITY",
            "exchange": "NSE",
            "market": "India",
            "currency": "INR",
            "currency_symbol": "₹",
            "provider_symbol": f"{internal_sym}.NS",
            "active": True,
            "trading_calendar": "NSE",
            "timezone": "Asia/Kolkata"
        }

    # 2. Check Crypto
    if internal_sym in CRYPTO_SYMBOLS or "-USD" in clean_sym:
        disp_name = CRYPTO_SYMBOLS.get(internal_sym, f"{internal_sym} Crypto")
        return {
            "symbol": internal_sym,
            "display_name": disp_name,
            "asset_class": "CRYPTO",
            "exchange": "CRYPTO_GLOBAL",
            "market": "Global Crypto",
            "currency": "USD",
            "currency_symbol": "$",
            "provider_symbol": internal_sym,
            "active": True,
            "trading_calendar": "24/7",
            "timezone": "UTC"
        }

    # 3. Check Forex
    if internal_sym in FOREX_SYMBOLS or "=X" in clean_sym:
        disp_name = FOREX_SYMBOLS.get(internal_sym, f"{internal_sym} Pair")
        return {
            "symbol": internal_sym,
            "display_name": disp_name,
            "asset_class": "FOREX",
            "exchange": "FOREX_OTC",
            "market": "Forex",
            "currency": "USD",
            "currency_symbol": "$",
            "provider_symbol": internal_sym,
            "active": True,
            "trading_calendar": "FOREX_24/5",
            "timezone": "UTC"
        }

    # 4. Check Indices
    if internal_sym in INDEX_SYMBOLS or clean_sym.startswith("^"):
        disp_name = INDEX_SYMBOLS.get(internal_sym, f"{internal_sym} Index")
        exchange = "NSE" if "^NSE" in internal_sym or "^BSE" in internal_sym else "NASDAQ"
        currency = "INR" if "^NSE" in internal_sym or "^BSE" in internal_sym else "USD"
        return {
            "symbol": internal_sym,
            "display_name": disp_name,
            "asset_class": "INDEX",
            "exchange": exchange,
            "market": "Global",
            "currency": currency,
            "currency_symbol": "₹" if currency == "INR" else "$",
            "provider_symbol": internal_sym,
            "active": True,
            "trading_calendar": "US_EQUITY" if currency == "USD" else "NSE",
            "timezone": "America/New_York" if currency == "USD" else "Asia/Kolkata"
        }

    # 5. Check US Equities / Default Fallback
    disp_name = US_EQUITY_SYMBOLS.get(internal_sym, f"{internal_sym} Inc.")
    return {
        "symbol": internal_sym,
        "display_name": disp_name,
        "asset_class": "US_EQUITY",
        "exchange": "NASDAQ",
        "market": "US",
        "currency": "USD",
        "currency_symbol": "$",
        "provider_symbol": internal_sym,
        "active": True,
        "trading_calendar": "US_EQUITY",
        "timezone": "America/New_York"
    }
