import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import init_db

init_db()
client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "StockSense AI API"
    assert "disclaimer" in data

def test_get_stocks_universe():
    res = client.get("/api/stocks")
    assert res.status_code == 200
    data = res.json()
    assert "universe" in data
    assert len(data["universe"]) >= 5

def test_get_models_endpoint():
    res = client.get("/api/models")
    assert res.status_code == 200
    assert "models" in res.json()

def test_get_predictions_endpoint():
    res = client.get("/api/predictions")
    assert res.status_code == 200
    assert "predictions" in res.json()
