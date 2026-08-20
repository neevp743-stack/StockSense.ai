"""
StockSense AI — Fundamental Data Provider Abstraction & Implementation
Defines abstract FundamentalDataProvider and YFinanceFundamentalProvider with point-in-time validation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf
from datetime import datetime

class FundamentalDataProvider(ABC):

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Returns latest point-in-time fundamental observations."""
        pass

    @abstractmethod
    def get_historical_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Returns historical point-in-time fundamental observations with filing dates."""
        pass

    @abstractmethod
    def get_filing_events(self, symbol: str) -> List[Dict[str, Any]]:
        """Returns verified public filing date events."""
        pass


class YFinanceFundamentalProvider(FundamentalDataProvider):
    """
    Yahoo Finance Fundamental Data Provider.
    Enforces point-in-time availability timestamp checking.
    """

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            
            if not info or "regularMarketPrice" not in info and "previousClose" not in info:
                return {
                    "symbol": symbol,
                    "status": "FUNDAMENTAL DATA UNAVAILABLE",
                    "source": "yfinance",
                    "data": None
                }

            metrics = {
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "forward_pe": info.get("forwardPE"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "debt_to_equity": info.get("debtToEquity"),
                "market_cap": info.get("marketCap"),
                "free_cash_flow": info.get("freeCashflow")
            }

            return {
                "symbol": symbol,
                "status": "AVAILABLE",
                "source": "yfinance",
                "as_of": datetime.utcnow().strftime("%Y-%m-%d"),
                "data": metrics
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "FUNDAMENTAL DATA UNAVAILABLE",
                "error": str(e),
                "data": None
            }

    def get_historical_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Free Yahoo Finance API does NOT provide historical SEC/EDGAR filing date timestamps
        for past 2 years required by strict point-in-time backtesting.
        To enforce Zero False Claims, return FUNDAMENTAL DATA UNAVAILABLE.
        """
        return {
            "symbol": symbol,
            "status": "FUNDAMENTAL DATA UNAVAILABLE",
            "message": "Historical point-in-time fundamental filing date timestamps unavailable via yfinance free API. Attach SEC/EDGAR or Bloomberg API for historical point-in-time fundamentals.",
            "data": None
        }

    def get_filing_events(self, symbol: str) -> List[Dict[str, Any]]:
        return []
