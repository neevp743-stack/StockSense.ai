"""
StockSense AI — Phase 21.4 Market Data Provider Package
"""

from backend.data.providers.base_provider import MarketDataProvider
from backend.data.providers.finnhub_provider import FinnhubProvider
from backend.data.providers.yfinance_provider import YFinanceProvider
from backend.data.providers.secondary_provider import SecondaryProvider
from backend.data.providers.coinbase_ws_provider import CoinbaseWSProvider
from backend.data.providers.twelve_data_provider import TwelveDataProvider
from backend.data.providers.provider_router import ProviderRouter, provider_router

__all__ = [
    "MarketDataProvider",
    "FinnhubProvider",
    "YFinanceProvider",
    "SecondaryProvider",
    "CoinbaseWSProvider",
    "TwelveDataProvider",
    "ProviderRouter",
    "provider_router"
]
