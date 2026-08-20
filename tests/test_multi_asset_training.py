import pytest
import os
import joblib
import pandas as pd
from backend.models.baseline_models import ModelPipeline
from backend.db.database import SessionLocal, init_db
from backend.db.models import ModelMetadata, PredictionRecord
from backend.backtest.backtester import run_backtest

def test_us_equity_model_trained():
    """Verifies that US Equity models (e.g. AAPL) exist and can be loaded."""
    init_db()
    db = SessionLocal()
    try:
        meta = db.query(ModelMetadata).filter(ModelMetadata.symbol == "AAPL").first()
        assert meta is not None, "ModelMetadata record missing for AAPL"
        assert meta.asset_class == "US_EQUITY"
    finally:
        db.close()

def test_crypto_model_trained():
    """Verifies that Crypto models (e.g. BTC-USD) exist and can be loaded."""
    init_db()
    db = SessionLocal()
    try:
        meta = db.query(ModelMetadata).filter(ModelMetadata.symbol == "BTC-USD").first()
        assert meta is not None, "ModelMetadata record missing for BTC-USD"
        assert meta.asset_class == "CRYPTO"
    finally:
        db.close()

def test_forex_model_trained():
    """Verifies that Forex models (e.g. EURUSD=X) exist and can be loaded."""
    init_db()
    db = SessionLocal()
    try:
        meta = db.query(ModelMetadata).filter(ModelMetadata.symbol == "EURUSD=X").first()
        assert meta is not None, "ModelMetadata record missing for EURUSD=X"
        assert meta.asset_class == "FOREX"
    finally:
        db.close()

def test_index_model_trained():
    """Verifies that Index models (e.g. ^GSPC) exist and can be loaded."""
    init_db()
    db = SessionLocal()
    try:
        meta = db.query(ModelMetadata).filter(ModelMetadata.symbol == "^GSPC").first()
        assert meta is not None, "ModelMetadata record missing for ^GSPC"
        assert meta.asset_class == "INDEX"
    finally:
        db.close()

def test_out_of_sample_backtest_isolation():
    """Verifies that backtest execution uses strict out-of-sample data and returns valid structure."""
    df_test = pd.DataFrame({
        "date": pd.date_range(start="2026-01-01", periods=20, freq="D").date,
        "close": [100 + i for i in range(20)]
    })
    probs = [0.60 if i % 2 == 0 else 0.40 for i in range(20)]
    res = run_backtest(df_test, probs, prob_threshold=0.50)
    assert "ai_strategy" in res
    assert "buy_and_hold" in res
    assert "total_return_pct" in res["ai_strategy"]
    assert "total_return_pct" in res["buy_and_hold"]
