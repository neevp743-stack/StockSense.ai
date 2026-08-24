"""
StockSense AI — Phase 21.2 Market Data Provider Interface
Abstract Base Class for provider-agnostic market data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd


class MarketDataProvider(ABC):
    """Abstract Base Class for Multi-Asset Market Data Providers."""

    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider identifier name string (e.g., FINNHUB, YFINANCE, SECONDARY)."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if provider credentials and endpoints are validly configured."""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches latest quote for a single symbol.
        Must return dict containing: symbol, provider, price, timestamp, data_status, latency_ms, error.
        """
        pass

    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetches latest quotes for multiple symbols (batched where supported).
        Returns mapping from symbol to quote dict.
        """
        pass

    @abstractmethod
    def get_historical(self, symbol: str, start: Optional[str] = None, end: Optional[str] = None, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
        """Fetches historical OHLCV data strictly for DB storage, training, and backtesting."""
        pass

    @abstractmethod
    def subscribe(self, symbols: List[str]) -> bool:
        """Subscribes to live streaming tick updates for the specified symbols."""
        pass

    @abstractmethod
    def unsubscribe(self, symbols: List[str]) -> bool:
        """Unsubscribes from live streaming tick updates for the specified symbols."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns provider operational health metrics."""
        pass
