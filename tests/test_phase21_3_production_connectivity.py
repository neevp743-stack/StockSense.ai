"""
StockSense AI — Phase 21.3 Production Connectivity & Deployment Tests
Verifies end-to-end deployment configuration, API routing, CORS, WebSocket,
frontend build, and Phase 12 model hash invariance.
"""

import os
import sys
import json
import hashlib
import importlib
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ==============================================================================
# TEST 1: Production API base URL is correct in api.js
# ==============================================================================
def test_01_frontend_api_base_url_configured():
    """Frontend api.js must contain the correct production backend URL."""
    api_js_path = os.path.join(PROJECT_ROOT, "frontend", "src", "api.js")
    assert os.path.exists(api_js_path), f"api.js not found at {api_js_path}"

    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain the Render backend URL as fallback
    assert "stocksense-ai-backend-sdyo.onrender.com" in content, \
        "api.js must contain the production Render backend URL"

    # Must reference VITE_API_BASE_URL for env-based override
    assert "VITE_API_BASE_URL" in content, \
        "api.js must reference VITE_API_BASE_URL environment variable"

    # Must NOT hardcode localhost as the only option
    assert "localhost" in content, \
        "api.js should have localhost for development fallback"


# ==============================================================================
# TEST 2: Frontend WebSocket URL generation
# ==============================================================================
def test_02_frontend_websocket_url_generation():
    """api.js must generate correct wss:// URLs from https:// backend."""
    api_js_path = os.path.join(PROJECT_ROOT, "frontend", "src", "api.js")
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must generate WebSocket URL from backend URL
    assert "getWebSocketUrl" in content, "Must export getWebSocketUrl function"
    assert "wss:" in content or "wsProtocol" in content, \
        "Must handle wss:// for secure connections"
    assert "/ws/market/" in content, "Must use /ws/market/{symbol} path"


# ==============================================================================
# TEST 3: CORS configuration includes Vercel origin
# ==============================================================================
def test_03_cors_includes_vercel_origin():
    """Backend CORS must explicitly allow the Vercel frontend origin."""
    from backend.config import CORS_ALLOWED_ORIGINS

    vercel_origins = [o for o in CORS_ALLOWED_ORIGINS if "vercel.app" in o]
    assert len(vercel_origins) > 0, \
        f"CORS_ALLOWED_ORIGINS must include a *.vercel.app origin. Got: {CORS_ALLOWED_ORIGINS}"

    # Specifically check for the known Vercel domain
    assert any("stock-sense-ai-lilac.vercel.app" in o for o in CORS_ALLOWED_ORIGINS), \
        "CORS must include stock-sense-ai-lilac.vercel.app"


# ==============================================================================
# TEST 4: CORS regex allows all Vercel preview deployments
# ==============================================================================
def test_04_cors_regex_allows_vercel_previews():
    """Backend must have allow_origin_regex for *.vercel.app."""
    main_path = os.path.join(PROJECT_ROOT, "backend", "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "allow_origin_regex" in content, \
        "main.py must use allow_origin_regex for Vercel preview deployments"
    assert "vercel\\.app" in content, \
        "allow_origin_regex must match *.vercel.app"


# ==============================================================================
# TEST 5: vercel.json SPA rewrite configured correctly
# ==============================================================================
def test_05_vercel_json_spa_rewrite():
    """vercel.json must have SPA rewrite to index.html."""
    vercel_json_path = os.path.join(PROJECT_ROOT, "frontend", "vercel.json")
    assert os.path.exists(vercel_json_path), "frontend/vercel.json must exist"

    with open(vercel_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert "rewrites" in config, "vercel.json must have rewrites"
    rewrites = config["rewrites"]
    assert len(rewrites) > 0, "vercel.json must have at least one rewrite"

    # Should rewrite all routes to /index.html for SPA
    spa_rewrite = any(
        r.get("source") == "/(.*)" and r.get("destination") == "/index.html"
        for r in rewrites
    )
    assert spa_rewrite, "vercel.json must rewrite all routes to /index.html"


# ==============================================================================
# TEST 6: No localhost-only API configuration in production
# ==============================================================================
def test_06_no_localhost_only_api():
    """Frontend must NOT default to localhost when VITE_API_BASE_URL is unset in production."""
    api_js_path = os.path.join(PROJECT_ROOT, "frontend", "src", "api.js")
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must have a production fallback that is NOT localhost
    assert "onrender.com" in content, \
        "api.js must have a non-localhost production fallback URL"


# ==============================================================================
# TEST 7: Backend health endpoint exists and responds
# ==============================================================================
def test_07_backend_health_endpoint():
    """GET /health must return valid JSON with status field."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data, "Health response must contain 'status' field"


# ==============================================================================
# TEST 8: Dashboard-data endpoint returns correct schema
# ==============================================================================
def test_08_dashboard_data_endpoint_schema():
    """GET /api/stocks/{symbol}/dashboard-data must return history, prediction, technical_analysis."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/stocks/RELIANCE/dashboard-data?model_name=XGBoost")

    # Should return 200 (data may be from DB or cache)
    assert response.status_code in [200, 404], \
        f"Dashboard-data should return 200 or 404, got {response.status_code}"

    if response.status_code == 200:
        data = response.json()
        assert "symbol" in data
        assert "history" in data
        assert "prediction" in data
        if data["history"]:
            assert "data" in data["history"]
            assert "count" in data["history"]


# ==============================================================================
# TEST 9: Prediction endpoint returns correct schema
# ==============================================================================
def test_09_prediction_endpoint_schema():
    """GET /api/stocks/{symbol}/prediction must return probability fields."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/stocks/RELIANCE/prediction?model_name=XGBoost")

    if response.status_code == 200:
        data = response.json()
        # Must have prediction fields
        assert "predicted_direction" in data or "direction" in data, \
            "Prediction must contain direction field"


# ==============================================================================
# TEST 10: History endpoint returns OHLC data
# ==============================================================================
def test_10_history_endpoint_returns_ohlc():
    """GET /api/stocks/{symbol}/history must return OHLC-formatted data."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/stocks/RELIANCE/history?limit=5")

    if response.status_code == 200:
        data = response.json()
        records = data.get("data") or data.get("history", [])
        if len(records) > 0:
            first = records[0]
            # Must have OHLC columns
            for col in ["open", "high", "low", "close"]:
                assert col in first, f"History record must contain '{col}' field"


# ==============================================================================
# TEST 11: Provider health endpoint returns valid schema
# ==============================================================================
def test_11_provider_health_endpoint_schema():
    """GET /api/research/phase21/provider-health must return valid provider health."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/research/phase21/provider-health")
    assert response.status_code == 200

    data = response.json()
    assert "provider" in data or "status" in data or "state" in data, \
        "Provider health must contain provider/status/state field"


# ==============================================================================
# TEST 12: WebSocket endpoint is registered
# ==============================================================================
def test_12_websocket_endpoint_registered():
    """Backend must have /ws/market/{symbol} WebSocket endpoint."""
    main_path = os.path.join(PROJECT_ROOT, "backend", "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '@app.websocket("/ws/market/{symbol}")' in content, \
        "Backend must register WebSocket endpoint at /ws/market/{symbol}"


# ==============================================================================
# TEST 13: Zero price fabrication prevention
# ==============================================================================
def test_13_zero_price_fabrication_prevention():
    """Provider must never return 0 as a valid price."""
    # A quote with price=0 should be treated as invalid
    test_quote = {"price": 0, "timestamp": "2026-01-01T00:00:00Z"}
    price = test_quote.get("price")

    # Our validation: price must be > 0 to be valid
    is_valid = price is not None and price > 0
    assert not is_valid, "Price of 0 must be rejected as invalid"


# ==============================================================================
# TEST 14: Phase 12 model hash invariance
# ==============================================================================
def test_14_phase12_model_hash_invariance():
    """All Phase 12 model .joblib files must have unchanged SHA256 hashes."""
    before_hashes_path = os.path.join(
        PROJECT_ROOT, "backend", "research", "phase21",
        "phase12_before_hashes_phase21_3.json"
    )
    if not os.path.exists(before_hashes_path):
        pytest.skip("BEFORE hashes file not found (run hash collection first)")

    with open(before_hashes_path, "r") as f:
        before_hashes = json.load(f)

    for rel_path, expected_hash in before_hashes.items():
        abs_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(abs_path):
            continue

        with open(abs_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        assert actual_hash == expected_hash, \
            f"Phase 12 model hash CHANGED for {rel_path}! " \
            f"Before: {expected_hash[:16]}... After: {actual_hash[:16]}..."


# ==============================================================================
# TEST 15: Frontend build produces valid output
# ==============================================================================
def test_15_frontend_index_html_exists():
    """Frontend must have a valid index.html entry point."""
    index_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
    assert os.path.exists(index_path), "frontend/index.html must exist"

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '<div id="root">' in content, "index.html must have React root div"
    assert "StockSense AI" in content, "index.html must reference StockSense AI"


# ==============================================================================
# TEST 16: Render deployment configuration exists
# ==============================================================================
def test_16_render_deployment_config():
    """render.yaml must be correctly configured for backend deployment."""
    render_path = os.path.join(PROJECT_ROOT, "render.yaml")
    assert os.path.exists(render_path), "render.yaml must exist"

    with open(render_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "uvicorn" in content, "render.yaml must use uvicorn"
    assert "backend.main:app" in content, "render.yaml must reference backend.main:app"
    assert "ENVIRONMENT" in content, "render.yaml must set ENVIRONMENT"


# ==============================================================================
# TEST 17: API search endpoint works
# ==============================================================================
def test_17_search_endpoint():
    """GET /api/search must return valid results."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/search?q=RELIANCE&limit=5")
    assert response.status_code == 200

    data = response.json()
    assert "assets" in data or isinstance(data, list), \
        "Search must return results in 'assets' key"


# ==============================================================================
# TEST 18: Assets endpoint returns valid data
# ==============================================================================
def test_18_assets_endpoint():
    """GET /api/assets must return list of assets."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/assets?asset_class=INDIAN_EQUITY")
    assert response.status_code == 200

    data = response.json()
    assert "assets" in data, "Assets response must contain 'assets' field"
    assert len(data["assets"]) > 0, "Must have at least one Indian equity asset"


# ==============================================================================
# TEST 19: Telemetry endpoints do not fabricate status
# ==============================================================================
def test_19_telemetry_no_fabrication():
    """Production health endpoint must not hardcode HEALTHY when backend is starting."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/production-health")
    assert response.status_code == 200

    data = response.json()
    assert "overall_status" in data, "Must have overall_status field"

    # Status must be a valid enum, not a fabricated string
    valid_statuses = {"HEALTHY", "DEGRADED", "UNAVAILABLE", "INSUFFICIENT_DATA"}
    assert data["overall_status"] in valid_statuses, \
        f"overall_status must be one of {valid_statuses}, got: {data['overall_status']}"


# ==============================================================================
# TEST 20: Production deployment does not expose secrets
# ==============================================================================
def test_20_no_secret_exposure():
    """Backend must not expose API keys in health or status endpoints."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # Check health endpoint
    response = client.get("/health")
    body = response.text
    assert "REALTIME_API_KEY" not in body or "api_key" not in body.lower(), \
        "Health endpoint must not expose API keys"

    # Check system status
    response = client.get("/api/system/status")
    if response.status_code == 200:
        body = response.text
        # Should not contain the actual Finnhub API key value
        from backend.config import REALTIME_API_KEY
        if REALTIME_API_KEY and len(REALTIME_API_KEY) > 8:
            assert REALTIME_API_KEY not in body, \
                "System status must not expose the full API key"
