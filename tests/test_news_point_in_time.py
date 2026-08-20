import pytest
from datetime import datetime
from backend.data.news.sentiment import SentimentService

def test_news_point_in_time_filtering():
    t_pred = datetime(2026, 1, 10, 10, 0, 0)
    service = SentimentService()

    articles = [
        {"headline": "Company reports record profit growth", "published_timestamp": datetime(2026, 1, 9, 14, 0, 0)},
        {"headline": "Stock plunges following lawsuit", "published_timestamp": datetime(2026, 1, 10, 15, 0, 0)} # Future relative to 10:00 AM
    ]

    res = service.aggregate_daily_sentiment(articles, t_pred)
    assert res["news_volume"] == 1
    assert res["pos_count"] == 1
    assert res["neg_count"] == 0
