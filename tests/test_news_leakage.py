import pytest
from datetime import datetime
from backend.data.news.sentiment import SentimentService

def test_news_publication_timestamp_leakage():
    t_pred = datetime(2026, 1, 10, 0, 0, 0)
    service = SentimentService()

    articles_before = [
        {"headline": "Market opens steady", "published_timestamp": datetime(2026, 1, 9, 12, 0, 0), "sentiment_score": 0.1, "sentiment_label": "NEUTRAL"}
    ]

    res1 = service.aggregate_daily_sentiment(articles_before, t_pred)
    vol1 = res1["news_volume"]

    # Add future article published at 2:00 PM on Jan 10 (after 00:00 AM prediction cutoff)
    articles_after = articles_before + [
        {"headline": "Breaking news: Major crash", "published_timestamp": datetime(2026, 1, 10, 14, 0, 0), "sentiment_score": -0.8, "sentiment_label": "NEGATIVE"}
    ]

    res2 = service.aggregate_daily_sentiment(articles_after, t_pred)
    vol2 = res2["news_volume"]

    assert vol1 == vol2 == 1, "FUTURE NEWS LEAKAGE DETECTED! Article after prediction cutoff entered prediction."
