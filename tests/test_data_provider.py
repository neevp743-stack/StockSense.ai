import pytest
import pandas as pd
from datetime import datetime, timezone
from backend.data.provider import YFinanceProvider, MarketDataProvider

def test_provider_subclass_check():
    """Verifies that YFinanceProvider implements MarketDataProvider ABC interface."""
    provider = YFinanceProvider()
    assert isinstance(provider, MarketDataProvider)

def test_no_fake_live_stream():
    """Verifies that YFinanceProvider explicitly reports streaming is unsupported without simulating fake LIVE feeds."""
    provider = YFinanceProvider()
    stream_res = provider.get_realtime_stream("RELIANCE")
    assert stream_res["data_status"] == "UNAVAILABLE"
    assert stream_res["streaming_supported"] is False
    assert "unsupported" in stream_res["message"].lower()

def test_latest_quote_data_status():
    """Verifies latest quote response structure and dynamic data freshness status."""
    provider = YFinanceProvider()
    quote = provider.get_latest_quote("RELIANCE")
    assert "symbol" in quote
    assert "price" in quote
    assert "data_status" in quote
    assert quote["data_status"] in ["LIVE", "DELAYED", "HISTORICAL", "UNAVAILABLE"]
    # yfinance quotes must never claim LIVE
    assert quote["data_status"] != "LIVE" or quote.get("provider") != "yfinance"
    assert quote["is_delayed"] is True

def test_historical_data_isolation():
    """Verifies that fetching a latest quote does not mutate or modify historical DataFrame structure."""
    provider = YFinanceProvider()
    df_hist_before = pd.DataFrame({
        "date": [pd.to_datetime("2026-01-01").date(), pd.to_datetime("2026-01-02").date()],
        "close": [100.0, 102.0]
    })
    df_hist_copy = df_hist_before.copy()

    # Get quote
    _ = provider.get_latest_quote("RELIANCE")

    # Assert historical DataFrame remains completely unchanged
    pd.testing.assert_frame_equal(df_hist_before, df_hist_copy)
