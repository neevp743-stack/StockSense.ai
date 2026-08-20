import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import REALTIME_API_KEY, SECRET_KEY, ENVIRONMENT, CORS_ALLOWED_ORIGINS
from backend.db.database import get_db_context
from backend.db.models import StockPrice

client = TestClient(app)

def test_health_endpoint():
    """Verifies GET /health endpoint response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data

def test_system_status_endpoint():
    """Verifies GET /api/system/status endpoint response."""
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "ONLINE"
    assert data["database"] == "CONNECTED"
    assert "realtime_provider" in data
    assert "realtime_status" in data
    assert "model" in data

def test_secret_key_leak_protection():
    """Verifies that API keys and secrets are NEVER returned by system status or root endpoints."""
    res_status = client.get("/api/system/status").json()
    res_root = client.get("/").json()
    res_health = client.get("/health").json()

    # Convert payloads to strings and check for REALTIME_API_KEY leakage
    status_str = str(res_status)
    root_str = str(res_root)
    health_str = str(res_health)

    if REALTIME_API_KEY:
        assert REALTIME_API_KEY not in status_str
        assert REALTIME_API_KEY not in root_str
        assert REALTIME_API_KEY not in health_str

    assert SECRET_KEY not in status_str
    assert SECRET_KEY not in root_str
    assert SECRET_KEY not in health_str

def test_cors_configuration():
    """Verifies CORS origins are configured list of strings."""
    assert isinstance(CORS_ALLOWED_ORIGINS, list)
    assert len(CORS_ALLOWED_ORIGINS) > 0

def test_production_database_isolation():
    """Verifies system status calls do not mutate stock_prices table."""
    with get_db_context() as db:
        initial_count = db.query(StockPrice).count()

    client.get("/api/system/status")

    with get_db_context() as db:
        final_count = db.query(StockPrice).count()

    assert initial_count == final_count
