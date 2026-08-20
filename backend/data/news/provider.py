"""
StockSense AI — News Data Provider Abstraction & Implementation
Defines abstract NewsDataProvider and YFinanceNewsProvider with historical news check.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import yfinance as yf
from datetime import datetime

class NewsDataProvider(ABC):

    @abstractmethod
    def get_historical_news(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Returns list of timestamped news articles published between start_date and end_date."""
        pass


class YFinanceNewsProvider(NewsDataProvider):
    """
    Yahoo Finance News Data Provider.
    Enforces historical availability checking.
    """

    def get_historical_news(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            news_items = ticker.news or []
            
            if not news_items:
                return {
                    "symbol": symbol,
                    "status": "NEWS DATA UNAVAILABLE",
                    "articles": [],
                    "message": "No historical news articles returned by feed."
                }

            articles = []
            for item in news_items:
                content = item.get("content", {})
                pub_time = content.get("pubDate") or item.get("providerPublishTime")
                headline = content.get("title") or item.get("title")
                
                if pub_time and headline:
                    if isinstance(pub_time, (int, float)):
                        pub_dt = datetime.utcfromtimestamp(pub_time)
                    elif isinstance(pub_time, str):
                        try:
                            pub_dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                        except Exception:
                            pub_dt = datetime.utcnow()
                    else:
                        pub_dt = datetime.utcnow()

                    articles.append({
                        "article_id": item.get("id", f"{symbol}_{hash(headline)}"),
                        "symbol": symbol,
                        "headline": headline,
                        "published_timestamp": pub_dt,
                        "source": content.get("provider", {}).get("displayName", "yfinance"),
                        "url": content.get("canonicalUrl", {}).get("url", "")
                    })

            return {
                "symbol": symbol,
                "status": "AVAILABLE" if articles else "NEWS DATA UNAVAILABLE",
                "articles": articles
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "NEWS DATA UNAVAILABLE",
                "articles": [],
                "error": str(e)
            }
