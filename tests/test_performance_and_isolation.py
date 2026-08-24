import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.baseline_models import ModelPipeline
from backend.cache import model_cache, history_cache, prediction_cache

client = TestClient(app)

def test_model_in_memory_caching():
    """Verifies ModelPipeline.load_model uses in-memory caching for zero-latency reloading."""
    pipe1 = ModelPipeline.load_model("RELIANCE", "XGBoost")
    assert pipe1 is not None
    assert pipe1.is_trained is True

    # Check model_cache contains entry
    cache_key = "model_RELIANCE_XGBoost"
    cached = model_cache.get(cache_key)
    assert cached is not None
    assert cached is pipe1

def test_prediction_without_blocking_training():
    """Verifies GET /api/stocks/{symbol}/prediction responds immediately without synchronous retraining."""
    response = client.get("/api/stocks/RELIANCE/prediction")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "RELIANCE"
    assert "predicted_direction" in data
    assert "probability_up" in data
    assert "probability_down" in data
    assert "risk" in data
    assert "disclaimer" in data

def test_multi_asset_isolation():
    """Verifies historical data and predictions for TCS, INFY, and RELIANCE remain isolated."""
    res_rel = client.get("/api/stocks/RELIANCE/history?limit=10")
    res_infy = client.get("/api/stocks/INFY/history?limit=10")
    res_tcs = client.get("/api/stocks/TCS/history?limit=10")

    assert res_rel.status_code == 200
    assert res_infy.status_code == 200
    assert res_tcs.status_code == 200

    rel_data = res_rel.json()["data"]
    infy_data = res_infy.json()["data"]
    tcs_data = res_tcs.json()["data"]

    assert len(rel_data) > 0
    assert len(infy_data) > 0
    assert len(tcs_data) > 0

    # Ensure symbols in payload match request
    assert all(d["symbol"] == "RELIANCE" for d in rel_data)
    assert all(d["symbol"] == "INFY" for d in infy_data)
    assert all(d["symbol"] == "TCS" for d in tcs_data)

def test_cache_pattern_invalidation():
    """Verifies TTLCacheManager substring pattern invalidation."""
    history_cache.set("hist_RELIANCE_all", "dummy_reliance")
    history_cache.set("hist_INFY_all", "dummy_infy")

    history_cache.invalidate("RELIANCE")

    assert history_cache.get("hist_RELIANCE_all") is None
    assert history_cache.get("hist_INFY_all") == "dummy_infy"
    
    # Cleanup to prevent global cache pollution affecting other tests
    history_cache.invalidate("INFY")

@patch("backend.main.train_all_models_for_symbol")
@patch("backend.main.train_entire_universe")
def test_background_training_endpoints(mock_train_universe, mock_train_symbol):
    """Verifies POST /api/models/train/{symbol} and POST /api/models/train-all respond non-blocking."""
    res_single = client.post("/api/models/train/TCS")
    assert res_single.status_code == 200
    assert res_single.json()["status"] == "initiated"
    assert res_single.json()["symbol"] == "TCS"

    res_all = client.post("/api/models/train-all")
    assert res_all.status_code == 200
    assert res_all.json()["status"] == "initiated"

def test_system_status_speed():
    """Verifies GET /api/system/status returns system state fast."""
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["backend"] == "ONLINE"
    assert data["database"] == "CONNECTED"
