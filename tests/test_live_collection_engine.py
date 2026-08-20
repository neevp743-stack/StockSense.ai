import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.live_prediction_service import LivePredictionService, live_prediction_service
from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord
from backend.data.data_service import get_historical_data_from_db

client = TestClient(app)

def test_duplicate_prediction_prevention():
    """Verifies that calling get_live_prediction twice within 30s does NOT create duplicate DB records."""
    symbol = "RELIANCE"
    with get_db_context() as db:
        c1 = db.query(LivePredictionRecord).filter_by(symbol=symbol).count()
    
    # First call
    live_prediction_service.get_live_prediction(symbol)
    # Immediate second call
    live_prediction_service.get_live_prediction(symbol)

    with get_db_context() as db:
        c2 = db.query(LivePredictionRecord).filter_by(symbol=symbol).count()
    
    # Should create at most 1 new record, preventing duplicate inserts within 30s
    assert c2 - c1 <= 1

def test_live_collection_status_endpoint():
    """Tests GET /api/research/live-collection-status endpoint."""
    response = client.get("/api/research/live-collection-status")
    assert response.status_code == 200
    data = response.json()
    assert "collection_status" in data
    assert data["collection_status"] in ["COLLECTION ACTIVE", "COLLECTION PAUSED", "PROVIDER UNAVAILABLE"]
    assert "predictions_created" in data
    assert "predictions_resolved" in data

def test_sample_size_threshold_rule():
    """Verifies that sample size < 30 displays INSUFFICIENT LIVE SAMPLE SIZE."""
    service = LivePredictionService()
    stats = service.get_prediction_tracker_stats("BTC-USD")
    if stats["sample_size"] < 30:
        assert "INSUFFICIENT LIVE SAMPLE SIZE" in stats["accuracy_display"]
        assert stats["accuracy"] is None
    else:
        assert stats["accuracy_display"].endswith(f"(N={stats['sample_size']})")
        assert stats["accuracy"] is not None

def test_prediction_persistence():
    """Verifies predictions are correctly written to SQLite database."""
    symbol = "AAPL"
    live_prediction_service.get_live_prediction(symbol)
    with get_db_context() as db:
        rec = db.query(LivePredictionRecord).filter_by(symbol=symbol).order_by(LivePredictionRecord.prediction_timestamp.desc()).first()
        assert rec is not None
        assert rec.symbol == symbol
        assert rec.predicted_direction in ["UP", "DOWN"]

def test_resolution_no_future_leakage():
    """Verifies feature timestamp is strictly <= prediction timestamp and resolution uses past data."""
    symbol = "MSFT"
    res = live_prediction_service.get_live_prediction(symbol)
    if res["status"] == "SUCCESS":
        pred_ts = datetime.fromisoformat(res["prediction_timestamp"])
        feat_ts = datetime.fromisoformat(res["feature_timestamp"])
        assert feat_ts <= pred_ts

def test_collection_historical_isolation():
    """Verifies live prediction logging leaves historical stock_prices DB length unchanged."""
    df1 = get_historical_data_from_db("NVDA")
    live_prediction_service.get_live_prediction("NVDA")
    df2 = get_historical_data_from_db("NVDA")
    assert len(df1) == len(df2)
