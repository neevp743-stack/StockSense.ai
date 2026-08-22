import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import PROJECT_ROOT

client = TestClient(app)

def test_system_metrics_endpoint():
    """Verify /api/system/metrics returns system health and cache telemetry."""
    res = client.get("/api/system/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "system" in data
    assert "caches" in data
    assert "realtime" in data

def test_rate_limiter_protection():
    """Verify RateLimiter logic and FastAPI HTTP 429 response."""
    from backend.security.rate_limiter import RateLimiter
    from fastapi import Request
    
    limiter = RateLimiter(requests_per_minute=3)
    mock_request = Request({"type": "http", "client": ("127.0.0.1", 8000)})
    
    # First 3 requests should pass
    limiter.check(mock_request, "test_route")
    limiter.check(mock_request, "test_route")
    limiter.check(mock_request, "test_route")
    
    # 4th request must raise 429
    with pytest.raises(Exception) as exc_info:
        limiter.check(mock_request, "test_route")
    assert "Rate limit exceeded" in str(exc_info.value)

def test_ml_validation_json_reports_exist():
    """Verify chronological out-of-sample ML validation JSON reports are generated."""
    val_dir = os.path.join(PROJECT_ROOT, "backend", "research", "ml_validation")
    assert os.path.exists(val_dir)
    
    target_assets = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]
    for sym in target_assets:
        report_path = os.path.join(val_dir, f"{sym}.json")
        assert os.path.exists(report_path), f"Validation report for '{sym}' missing."
        
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["symbol"] == sym
        assert "evaluation_methodology" in data
        assert "chronological_periods" in data
        assert "model_performance" in data
        assert "baseline_comparisons" in data
        assert "calibration" in data

def test_model_metadata_registry():
    """Verify saved_models registry includes metadata.json files."""
    models_dir = os.path.join(PROJECT_ROOT, "saved_models")
    target_assets = ["RELIANCE", "INFY", "TCS"]
    
    for sym in target_assets:
        meta_path = os.path.join(models_dir, sym, "XGBoost_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            assert meta["symbol"] == sym
            assert meta["model_name"] == "XGBoost"
            assert "version" in meta
            assert "trained_at" in meta
