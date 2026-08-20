import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.live_prediction_service import LivePredictionService, live_prediction_service
from backend.data.realtime_provider import RealTimeWebSocketProvider, LiveTickCache
from backend.data.data_service import get_historical_data_from_db

client = TestClient(app)

def test_live_prediction_with_trained_model():
    """Tests live prediction output for a trained asset (RELIANCE)."""
    res = live_prediction_service.get_live_prediction("RELIANCE", model_name="XGBoost")
    assert res["symbol"] == "RELIANCE"
    assert res["status"] == "SUCCESS"
    assert "probability_up" in res
    assert "probability_down" in res
    assert "prediction_timestamp" in res
    assert "feature_timestamp" in res

def test_live_prediction_without_trained_model():
    """Tests live prediction output for an untrained asset (NONEXISTENT)."""
    res = live_prediction_service.get_live_prediction("NONEXISTENT", model_name="XGBoost")
    assert res["symbol"] == "NONEXISTENT"
    assert res["status"] == "MODEL NOT TRAINED FOR THIS ASSET"
    assert res["data_status"] == "UNAVAILABLE"

def test_unavailable_realtime_provider():
    """Tests fallback behavior when real-time provider is unconfigured."""
    service = LivePredictionService()
    res = service.get_live_prediction("TCS")
    assert "data_status" in res
    assert res["data_status"] in ["DELAYED", "HISTORICAL", "UNAVAILABLE"]

def test_stale_tick_protection():
    """Verifies that stale ticks update data_status to STALE."""
    cache = LiveTickCache(stale_threshold_seconds=1)
    cache.update_tick("INFY", 1500.0)
    import time
    time.sleep(1.1)
    tick = cache.get_latest_tick("INFY")
    assert tick["data_status"] == "STALE"

def test_no_future_data_usage():
    """Verifies feature timestamp is strictly <= prediction timestamp."""
    res = live_prediction_service.get_live_prediction("HDFCBANK")
    if res["status"] == "SUCCESS":
        pred_ts = datetime.fromisoformat(res["prediction_timestamp"])
        feat_ts = datetime.fromisoformat(res["feature_timestamp"])
        assert feat_ts <= pred_ts

def test_historical_dataset_isolation():
    """Verifies live predictions leave SQLite stock_prices DB length unchanged."""
    df1 = get_historical_data_from_db("ICICIBANK")
    live_prediction_service.get_live_prediction("ICICIBANK")
    df2 = get_historical_data_from_db("ICICIBANK")
    assert len(df1) == len(df2)

def test_prediction_timestamp_correctness():
    """Verifies prediction timestamp is valid ISO format."""
    res = live_prediction_service.get_live_prediction("AAPL")
    assert "prediction_timestamp" in res
    ts = datetime.fromisoformat(res["prediction_timestamp"])
    assert ts is not None

def test_model_version_tracking():
    """Verifies model version string is tracked."""
    res = live_prediction_service.get_live_prediction("MSFT", model_name="XGBoost")
    assert "model_version" in res
    assert "XGBoost" in res["model_version"]

def test_probability_validity():
    """Verifies 0 <= probability <= 1 and probability_up + probability_down = 1.0."""
    res = live_prediction_service.get_live_prediction("NVDA")
    if res["status"] == "SUCCESS":
        p_up = res["probability_up"]
        p_down = res["probability_down"]
        assert 0.0 <= p_up <= 1.0
        assert 0.0 <= p_down <= 1.0
        assert abs((p_up + p_down) - 1.0) < 1e-3

def test_prediction_resolution():
    """Tests resolution function execution."""
    res = live_prediction_service.resolve_pending_predictions()
    assert "resolved_count" in res
    assert isinstance(res["resolved_count"], int)

def test_live_prediction_api_endpoint():
    """Tests GET /api/assets/{symbol}/live-prediction API endpoint."""
    response = client.get("/api/assets/RELIANCE/live-prediction")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "RELIANCE"
    assert "probability_up" in data
    assert "data_status" in data
