import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.indicators.technical_analysis import calculate_technical_indicators, detect_support_resistance
from backend.db.database import get_db_context
from backend.db.models import StockPrice

client = TestClient(app)

def create_sample_df():
    dates = pd.date_range("2025-01-01", periods=30, freq="D")
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(30))
    df = pd.DataFrame({
        "date": dates,
        "open": prices - 0.5,
        "high": prices + 1.5,
        "low": prices - 1.5,
        "close": prices,
        "volume": np.random.randint(1000, 5000, size=30)
    })
    return df

def test_backend_technical_indicators_calculation():
    """Verifies backend technical indicators calculation math."""
    df = create_sample_df()
    df_ind = calculate_technical_indicators(df)

    assert "sma_20" in df_ind.columns
    assert "ema_12" in df_ind.columns
    assert "vwap" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "bollinger_upper" in df_ind.columns
    assert "atr_14" in df_ind.columns
    assert "stoch_k" in df_ind.columns
    assert "obv" in df_ind.columns

    # Verify bounds
    last_rsi = df_ind["rsi_14"].iloc[-1]
    assert 0.0 <= last_rsi <= 100.0

def test_detect_support_resistance():
    """Verifies automatic support and resistance pivot detection."""
    df = create_sample_df()
    sup_res = detect_support_resistance(df)

    assert "support_levels" in sup_res
    assert "resistance_levels" in sup_res
    assert "current_price" in sup_res
    assert isinstance(sup_res["support_levels"], list)
    assert isinstance(sup_res["resistance_levels"], list)

def test_technical_analysis_api_endpoint():
    """Tests GET /api/assets/{symbol}/technical-analysis endpoint."""
    response = client.get("/api/assets/BTC-USD/technical-analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC-USD"
    assert "support_levels" in data
    assert "resistance_levels" in data
    assert "latest_indicators" in data
    indicators = data["latest_indicators"]
    assert "rsi_14" in indicators
    assert "macd" in indicators
    assert "sma_20" in indicators

def test_unavailable_data_handling():
    """Verifies 404 response for invalid asset technical analysis request."""
    response = client.get("/api/assets/NON_EXISTENT_ASSET_12345/technical-analysis")
    assert response.status_code == 404

def test_historical_live_data_isolation():
    """Verifies that querying technical analysis does not alter stock_prices database rows."""
    with get_db_context() as db:
        initial_count = db.query(StockPrice).count()

    client.get("/api/assets/BTC-USD/technical-analysis")

    with get_db_context() as db:
        final_count = db.query(StockPrice).count()

    assert initial_count == final_count
