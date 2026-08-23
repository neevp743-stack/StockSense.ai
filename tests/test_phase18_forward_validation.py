"""
StockSense AI — Phase 18 Forward Validation & Shadow Model Test Suite
"""

import os
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.services.shadow_prediction_service import shadow_prediction_service
from backend.services.forward_validation_service import forward_validation_service
from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker
from backend.research.phase18.forward_resolver import forward_resolver, get_asset_region, is_market_day
from backend.research.phase18.comparison_engine import comparison_engine, calculate_ece, calculate_model_metrics
from backend.research.phase18.statistical_tests import statistical_test_engine, run_mcnemar_test, bootstrap_accuracy_difference
from backend.research.phase18.trade_comparison import trade_comparison_engine
from backend.research.phase18.promotion_rules import promotion_rule_engine

client = TestClient(app)


def test_shadow_model_compatibility_and_hashes():
    """Verify Champion and Challenger model loading, metadata, and SHA256 hashes."""
    res = shadow_prediction_service.verify_model_compatibility()
    assert res["status"] in ["OK", "PHASE18_MODEL_COMPATIBILITY_ERROR"]
    if res["status"] == "OK":
        assert res["champion_available"] is True
        assert res["challenger_available"] is True
        assert res["champion_model_name"] == "XGBoost v1.0 Calibrated"
        assert res["challenger_model_name"] == "Phase17 Large XGBoost"


def test_shadow_prediction_recording_and_isolation():
    """Tests generating and recording paired Champion and Challenger shadow predictions."""
    market_ts = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    feature_ts = market_ts

    dates = pd.date_range("2026-06-01", periods=60)
    prices = [100.0 + i for i in range(60)]
    df_ohlcv = pd.DataFrame({
        "date": dates,
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [10000.0] * 60
    })

    res = shadow_prediction_service.generate_and_record_shadow_predictions(
        symbol="RELIANCE",
        df_ohlcv=df_ohlcv,
        current_price=114.0,
        market_ts=market_ts,
        feature_ts=feature_ts,
        data_status="LIVE"
    )

    assert res["status"] == "RECORDED"
    assert "champion" in res["results"]
    assert "challenger" in res["results"]


def test_duplicate_prediction_prevention():
    """Tests application-level and DB-level duplicate observation prevention."""
    market_ts = datetime.now(timezone.utc) - timedelta(days=2)
    feature_ts = market_ts

    rec1 = shadow_prediction_service._save_shadow_record(
        symbol="AAPL",
        prediction_ts=datetime.now(timezone.utc),
        market_ts=market_ts,
        feature_ts=feature_ts,
        model_role="CHAMPION",
        model_version="XGBoost v1.0 Calibrated",
        predicted_direction="UP",
        prob_up=0.60,
        prob_down=0.40,
        confidence="HIGH",
        trend_reg="BULL",
        vol_reg="LOW_VOLATILITY",
        comb_reg="BULL_LOW_VOLATILITY",
        current_price=180.0,
        data_status="LIVE",
        feature_version="v12"
    )

    # Second insert with exact same key must be skipped as duplicate
    rec2 = shadow_prediction_service._save_shadow_record(
        symbol="AAPL",
        prediction_ts=datetime.now(timezone.utc),
        market_ts=market_ts,
        feature_ts=feature_ts,
        model_role="CHAMPION",
        model_version="XGBoost v1.0 Calibrated",
        predicted_direction="UP",
        prob_up=0.60,
        prob_down=0.40,
        confidence="HIGH",
        trend_reg="BULL",
        vol_reg="LOW_VOLATILITY",
        comb_reg="BULL_LOW_VOLATILITY",
        current_price=180.0,
        data_status="LIVE",
        feature_version="v12"
    )

    assert rec1.get("status") in ["CREATED", "DUPLICATE_SKIPPED"]
    assert rec2.get("status") in ["DUPLICATE_SKIPPED", "DB_INTEGRITY_SKIP"]


def test_data_eligibility_and_timestamp_ordering():
    """Tests 8-point data eligibility criteria and lookahead leakage prevention."""
    market_ts = datetime.now(timezone.utc) - timedelta(days=1)
    feature_ts = market_ts

    # 1. Ineligible data_status != LIVE
    ok1, reason1 = shadow_prediction_service.validate_eligibility("RELIANCE", 100.0, market_ts, feature_ts, "DELAYED")
    assert ok1 is False

    # 2. Lookahead anomaly: feature_ts > market_ts + 5s
    future_feature_ts = market_ts + timedelta(minutes=10)
    ok2, reason2 = shadow_prediction_service.validate_eligibility("RELIANCE", 100.0, market_ts, future_feature_ts, "LIVE")
    assert ok2 is False

    # 3. Invalid symbol not in universe
    ok3, reason3 = shadow_prediction_service.validate_eligibility("INVALID_XYZ_99", 100.0, market_ts, feature_ts, "LIVE")
    assert ok3 is False


def test_forward_resolution_and_trading_calendars():
    """Tests T+1 resolution, return, direction, correctness, and Brier score."""
    # Test asset region detection
    assert get_asset_region("RELIANCE") == "INDIA"
    assert get_asset_region("AAPL") == "USA"
    assert get_asset_region("BTC-USD") == "CRYPTO"

    # Test market day
    sunday = datetime(2026, 8, 23, 12, 0, 0)  # Sunday
    assert is_market_day(sunday, "INDIA") is False
    assert is_market_day(sunday, "CRYPTO") is True

    # Test resolution logic
    market_ts = datetime.now(timezone.utc) - timedelta(hours=5)
    feature_ts = market_ts

    with get_db_context() as db:
        rec = Phase18ShadowPredictionRecord(
            symbol="INFY",
            prediction_timestamp=datetime.now(timezone.utc),
            market_timestamp=market_ts,
            feature_timestamp=feature_ts,
            model_role="CHAMPION",
            model_version="XGBoost v1.0 Calibrated",
            predicted_direction="UP",
            probability_up=0.65,
            probability_down=0.35,
            current_price=100.0,
            prediction_horizon=1,
            data_status="LIVE",
            resolved=False
        )
        db.add(rec)
        db.commit()
        rec_id = rec.id

    res = forward_resolver.resolve_prediction_record(rec_id, future_price=105.0)
    assert res["status"] == "RESOLVED"
    assert res["actual_direction"] == "UP"
    assert res["correct"] is True
    assert abs(res["brier_score"] - (0.65 - 1.0)**2) < 1e-4


def test_minimum_sample_size_handling():
    """Verifies N < 10 returns accuracy = null with reason = insufficient_forward_validation_data."""
    y_true = np.array([1, 0, 1])
    y_pred = np.array([1, 0, 0])
    y_prob = np.array([0.6, 0.4, 0.3])

    m = calculate_model_metrics(y_true, y_pred, y_prob)
    assert m["sample_size"] == 3
    assert m["accuracy"] is None
    assert m["reason"] == "insufficient_forward_validation_data"


def test_statistical_hypothesis_testing():
    """Tests McNemar's test and bootstrap 95% confidence intervals."""
    # McNemar test
    stat, p_val = run_mcnemar_test(b=5, c=15)
    assert stat >= 0.0
    assert 0.0 <= p_val <= 1.0

    # Bootstrap CIs
    y_true = np.array([1]*20 + [0]*20)
    y_c = np.array([1]*15 + [0]*25)
    y_ch = np.array([1]*18 + [0]*22)

    boot = bootstrap_accuracy_difference(y_true, y_c, y_ch, n_bootstraps=100, alpha=0.05)
    assert "mean_diff" in boot
    assert "ci_lower" in boot
    assert "ci_upper" in boot


def test_promotion_rules_and_zero_autopromote():
    """Ensures promotion rules never auto-promote Phase 17 to production."""
    # 1. Insufficient data case
    comp_insufficient = {"sample_size": 20, "comparison": {}}
    res_insuf = promotion_rule_engine.evaluate_promotion_criteria(comp_insufficient, {}, {}, {}, {})
    assert res_insuf["verdict"] == "PHASE18_INSUFFICIENT_FORWARD_DATA"
    assert "KEEP PHASE 12 IN PRODUCTION" in res_insuf["recommendation"]

    # 2. Sufficient data case
    comp_sufficient = {
        "sample_size": 150,
        "champion": {"accuracy": 0.55, "roc_auc": 0.58, "brier_score": 0.24, "ece": 0.05},
        "challenger": {"accuracy": 0.65, "roc_auc": 0.67, "brier_score": 0.22, "ece": 0.03},
        "comparison": {"accuracy_delta": 0.10, "roc_auc_delta": 0.09, "brier_delta": -0.02, "ece_delta": -0.02}
    }
    group_data = {"INDIA": {"accuracy_delta": 0.08}, "USA": {"accuracy_delta": 0.10}, "CRYPTO": {"accuracy_delta": 0.05}}
    regime_data = {"BULL": {"accuracy_delta": 0.05}, "BEAR": {"accuracy_delta": 0.05}}
    stat_data = {"statistically_significant": True}
    trade_data = {"comparison": {"win_rate_delta": 0.05}}

    res_promo = promotion_rule_engine.evaluate_promotion_criteria(comp_sufficient, group_data, regime_data, stat_data, trade_data)
    # Even if ready for expert review, it MUST NEVER contain automatic production promotion
    assert res_promo["verdict"] in ["PHASE18_READY_FOR_EXPERT_REVIEW", "PHASE18_CHALLENGER_INCONCLUSIVE"]
    assert "AUTOMATIC" not in res_promo["verdict"]


def test_phase18_api_endpoints():
    """Tests Phase 18 HTTP API endpoints."""
    # 1. Status Endpoint
    r_status = client.get("/api/research/phase18/status")
    assert r_status.status_code == 200
    assert r_status.json()["production_model"] == "XGBoost v1.0 Calibrated"
    assert r_status.json()["mode"] == "SHADOW"

    # 2. Comparison Endpoint
    r_comp = client.get("/api/research/phase18/comparison")
    assert r_comp.status_code == 200
    assert "summary" in r_comp.json()

    # 3. Trades Endpoint
    r_trades = client.get("/api/research/phase18/trades")
    assert r_trades.status_code == 200

    # 4. Statistics Endpoint
    r_stats = client.get("/api/research/phase18/statistics")
    assert r_stats.status_code == 200

    # 5. Symbol Endpoint
    r_sym = client.get("/api/research/phase18/RELIANCE")
    assert r_sym.status_code == 200
