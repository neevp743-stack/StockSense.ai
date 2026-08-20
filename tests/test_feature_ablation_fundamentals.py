import pytest
from backend.data.fundamentals.provider import YFinanceFundamentalProvider
from backend.data.news.provider import YFinanceNewsProvider

def test_feature_ablation_data_availability_status():
    fund_prov = YFinanceFundamentalProvider()
    res_fund = fund_prov.get_historical_fundamentals("RELIANCE.NS")
    assert res_fund["status"] == "FUNDAMENTAL DATA UNAVAILABLE"
    assert "unavailable" in res_fund["message"].lower()

    news_prov = YFinanceNewsProvider()
    res_news = news_prov.get_historical_news("RELIANCE.NS", "2024-01-01", "2026-01-01")
    assert res_news["status"] in ["AVAILABLE", "NEWS DATA UNAVAILABLE"]
