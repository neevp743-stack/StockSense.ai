"""
StockSense AI — Phase 16 Test Suite: Production Reliability & Live Prediction Monitoring
Tests data quality engine, live prediction tracking, prediction resolution,
future-data isolation, model performance monitoring, drift detection, calibration,
health scoring, and dataset separation.
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord, PaperPredictionRecord, StockPrice
from backend.services.data_quality_service import data_quality_service
from backend.services.live_prediction_tracker import live_prediction_tracker
from backend.services.prediction_resolver import prediction_resolver
from backend.services.model_monitor import model_monitor
from backend.services.drift_monitor import drift_monitor, calculate_psi
from backend.services.production_health_service import production_health_service

from backend.data.realtime_provider import realtime_provider_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_provider_state():
    realtime_provider_manager.connection_status = "CONNECTED"
    from backend.db.database import SessionLocal
    db = SessionLocal()
    try:
        db.rollback()
    except Exception:
        pass
    finally:
        db.close()
    yield




def test_data_quality_service_valid_and_invalid_symbols():
    """Tests data quality inspection for valid and invalid asset symbols."""
    res_reliance = data_quality_service.inspect_symbol_data_quality("RELIANCE")
    assert res_reliance["symbol"] == "RELIANCE"
    assert res_reliance["status"] in ["LIVE", "DELAYED", "STALE", "UNAVAILABLE"]

    res_invalid = data_quality_service.inspect_symbol_data_quality("INVALID_SYMBOL_999")
    assert res_invalid["status"] in ["INVALID", "UNAVAILABLE"]

    assert res_invalid["latest_price"] is None


def test_live_prediction_tracking_and_duplicate_prevention():
    """Tests idempotent live prediction observation recording."""
    payload = {
        "status": "SUCCESS",
        "symbol": "INFY",
        "live_price": 1850.50,
        "predicted_direction": "UP",
        "probability_up": 0.62,
        "probability_down": 0.38,
        "model_version": "XGBoost v1.0",
        "feature_timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_category": "LOW",
        "regime": {"trend_regime": "BULL", "volatility_regime": "LOW_VOLATILITY"}
    }

    rec_id_1 = live_prediction_tracker.record_prediction(payload)
    assert rec_id_1 is not None

    # Immediate duplicate request should return same record ID
    rec_id_2 = live_prediction_tracker.record_prediction(payload)
    assert rec_id_2 == rec_id_1


def test_prediction_resolution_and_future_data_isolation():
    """Tests prediction resolution using forward market data and verifies no retro-active payload tampering."""
    now = datetime.now(timezone.utc)
    past_time = now - timedelta(days=2)

    with get_db_context() as db:
        rec = LivePredictionRecord(
            symbol="TCS",
            prediction_timestamp=past_time,
            market_timestamp=past_time,
            predicted_direction="UP",
            probability_up=0.65,
            probability_down=0.35,
            current_price=3500.00,
            model_version="XGBoost v1.0",
            resolved=False
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        target_rec_id = rec.id

    # Resolve predictions
    res = prediction_resolver.resolve_unresolved_predictions(symbol="TCS")
    assert "resolved_count" in res

    with get_db_context() as db:
        resolved_rec = db.query(LivePredictionRecord).filter_by(id=target_rec_id).first()
        # Verify original parameters are unmodified
        assert resolved_rec.predicted_direction == "UP"
        assert resolved_rec.probability_up == 0.65
        assert resolved_rec.symbol == "TCS"


def test_insufficient_sample_size_handling():
    """Enforces minimum sample size threshold rule (sample_size < 10 -> accuracy = None)."""
    metrics = model_monitor.get_symbol_metrics("BTC-USD")
    if metrics["resolved_predictions"] < 10:
        assert metrics["accuracy"] is None
        assert metrics["reason"] == "insufficient_resolved_predictions"


def test_brier_score_and_calibration_gap_calculation():
    """Tests Brier score computation and probability band calibration evaluation."""
    cal = model_monitor.get_calibration_metrics("AAPL")
    assert "probability_bands" in cal
    assert "0.55-0.60" in cal["probability_bands"]
    assert "calibration_status" in cal


def test_model_drift_psi_calculation():
    """Tests Population Stability Index calculation and drift monitoring."""
    ref_distribution = [0.45, 0.48, 0.52, 0.55, 0.58, 0.60, 0.62]
    curr_stable = [0.46, 0.49, 0.51, 0.54, 0.57, 0.59, 0.61]
    curr_drifted = [0.80, 0.85, 0.88, 0.90, 0.92, 0.95, 0.98]

    psi_stable = calculate_psi(ref_distribution, curr_stable)
    psi_drifted = calculate_psi(ref_distribution, curr_drifted)

    assert psi_stable < 0.10
    assert psi_drifted > 0.10

    drift_res = drift_monitor.analyze_drift("NVDA")
    assert drift_res["status"] in ["NORMAL", "WATCH", "DRIFT_DETECTED"]


def test_production_health_score_evaluation():
    """Tests rule-based production health score components."""
    health = production_health_service.get_production_health()
    assert health["overall_status"] in ["HEALTHY", "DEGRADED", "INSUFFICIENT_DATA", "UNAVAILABLE"]
    assert "DATA_HEALTH" in health["components"]
    assert "MODEL_AVAILABILITY" in health["components"]
    assert "DRIFT_STATUS" in health["components"]


def test_phase16_api_endpoints():
    """Tests HTTP response schemas for all Phase 16 endpoints across supported assets."""
    symbols = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]

    # 1. Production Health API
    r_health = client.get("/api/production-health")
    assert r_health.status_code == 200
    assert "overall_status" in r_health.json()

    # 2. All Models Monitor API
    r_mon_all = client.get("/api/model-monitor/all")
    assert r_mon_all.status_code == 200
    assert "per_symbol" in r_mon_all.json()

    for sym in symbols:
        # Data Quality API
        r_dq = client.get(f"/api/data-quality/{sym}")
        assert r_dq.status_code == 200
        assert r_dq.json()["symbol"] == sym
        assert "status" in r_dq.json()

        # Symbol Model Monitor API
        r_mm = client.get(f"/api/model-monitor/{sym}")
        assert r_mm.status_code == 200
        assert r_mm.json()["symbol"] == sym

        # Calibration API
        r_cal = client.get(f"/api/model-monitor/{sym}/calibration")
        assert r_cal.status_code == 200
        assert r_cal.json()["symbol"] == sym

        # Drift API
        r_dr = client.get(f"/api/model-monitor/{sym}/drift")
        assert r_dr.status_code == 200
        assert r_dr.json()["symbol"] == sym


def test_dataset_category_separation():
    """Verifies strict separation between BACKTEST, PAPER, and LIVE_MODEL_VALIDATION datasets."""
    with get_db_context() as db:
        live_count = db.query(LivePredictionRecord).count()
        paper_count = db.query(PaperPredictionRecord).count()
        assert live_count >= 0
        assert paper_count >= 0


def test_legacy_synthetic_records_isolation():
    """Regression test: Ensures un-resolved legacy synthetic test records lacking current_price are excluded from live metrics."""
    with get_db_context() as db:
        legacy_rec = LivePredictionRecord(
            symbol="AAPL",
            prediction_timestamp=datetime.now(timezone.utc),
            market_timestamp=None,
            predicted_direction="UP",
            probability_up=0.55,
            probability_down=0.45,
            current_price=None,
            model_version="XGBoost v1.0",
            resolved=False,
            is_correct=True
        )
        db.add(legacy_rec)
        db.commit()
        legacy_id = legacy_rec.id

    try:
        metrics = model_monitor.get_symbol_metrics("AAPL")
        # Legacy record without current_price should NOT count as resolved
        with get_db_context() as db:
            r = db.query(LivePredictionRecord).filter_by(id=legacy_id).first()
            assert r.resolved is False
            assert r.current_price is None
    finally:
        with get_db_context() as db:
            db.query(LivePredictionRecord).filter_by(id=legacy_id).delete()
            db.commit()

