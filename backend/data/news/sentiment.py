"""
StockSense AI — Sentiment Analysis Service
Provides headline sentiment scoring (FinBERT/Rule-Based) and daily sentiment feature aggregation.
Enforces strictly timestamp-safe filtering (published_timestamp <= prediction_timestamp).
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

class SentimentService:

    def __init__(self):
        self.model_name = "Rule-Based FinBERT Heuristic"

    def analyze_headline(self, headline: str) -> Dict[str, Any]:
        """
        Analyzes headline sentiment score (-1.0 to +1.0) and assigns label.
        """
        text = headline.lower()
        pos_words = ["surge", "jump", "growth", "profit", "bullish", "rally", "record", "gain", "high", "upgrade", "outperform"]
        neg_words = ["drop", "fall", "loss", "bearish", "plunge", "decline", "warn", "risk", "lawsuit", "downgrade", "slash"]

        pos_count = sum(1 for w in pos_words if w in text)
        neg_count = sum(1 for w in neg_words if w in text)

        if pos_count > neg_count:
            score = round(min(1.0, 0.3 + 0.2 * (pos_count - neg_count)), 2)
            label = "POSITIVE"
        elif neg_count > pos_count:
            score = round(max(-1.0, -0.3 - 0.2 * (neg_count - pos_count)), 2)
            label = "NEGATIVE"
        else:
            score = 0.0
            label = "NEUTRAL"

        return {
            "score": score,
            "label": label
        }

    def aggregate_daily_sentiment(
        self, 
        articles: List[Dict[str, Any]], 
        prediction_timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Aggregates articles strictly published BEFORE or AT prediction_timestamp.
        Calculates:
        - daily_mean_sentiment
        - daily_median_sentiment
        - pos_count, neg_count, neu_count
        - news_volume
        """
        valid_articles = []
        for art in articles:
            pub_ts = art.get("published_timestamp")
            if isinstance(pub_ts, str):
                try:
                    pub_ts = datetime.fromisoformat(pub_ts)
                except Exception:
                    continue
            if pub_ts and pub_ts <= prediction_timestamp:
                valid_articles.append(art)

        if not valid_articles:
            return {
                "mean_sentiment": 0.0,
                "median_sentiment": 0.0,
                "pos_count": 0,
                "neg_count": 0,
                "neu_count": 0,
                "news_volume": 0
            }

        scores = []
        pos_c, neg_c, neu_c = 0, 0, 0

        for art in valid_articles:
            if "sentiment_score" not in art:
                res = self.analyze_headline(art.get("headline", ""))
                art["sentiment_score"] = res["score"]
                art["sentiment_label"] = res["label"]

            s = art["sentiment_score"]
            scores.append(s)
            lbl = art["sentiment_label"]
            if lbl == "POSITIVE":
                pos_c += 1
            elif lbl == "NEGATIVE":
                neg_c += 1
            else:
                neu_c += 1

        return {
            "mean_sentiment": float(np.mean(scores)),
            "median_sentiment": float(np.median(scores)),
            "pos_count": pos_c,
            "neg_count": neg_c,
            "neu_count": neu_c,
            "news_volume": len(scores)
        }
