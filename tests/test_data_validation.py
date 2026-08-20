import pytest
import pandas as pd
from backend.data.data_validator import validate_market_data

def test_validate_market_data_valid_df():
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    df = pd.DataFrame({
        "date": dates,
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "close": [102.0] * 10,
        "volume": [1000.0] * 10
    })
    report = validate_market_data(df, "TEST")
    assert report["is_valid"] is True
    assert report["total_rows"] == 10
    assert report["missing_values_count"] == 0

def test_validate_market_data_invalid_prices():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "open": [100.0, -50.0, 100.0, 100.0, 100.0],
        "high": [105.0, 105.0, 90.0, 105.0, 105.0],  # high < low in row 2
        "low": [95.0, 95.0, 95.0, 95.0, 95.0],
        "close": [102.0, 102.0, 102.0, 102.0, 102.0],
        "volume": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0]
    })
    report = validate_market_data(df, "TEST")
    assert report["is_valid"] is False
    assert report["invalid_price_rows_count"] > 0
