"""
StockSense AI — Phase 19 Test Suite: Forward Monitoring, Validation, & Decision-Support System
Tests 17-point data eligibility audit, synthetic exclusion, paired observation matching, deduplication,
rolling windows, per-symbol & asset-group aggregation, regime analysis, calibration, McNemar test,
bootstrap 95% CIs, trade comparison, promotion readiness scorecard, API schemas, and production model isolation.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.research.phase19.services.forward_data_service import forward_data_service
from backend.research.phase19.services.rolling_metrics import rolling_metrics_engine, calculate_metrics_for_records
from backend.research.phase19.services.regime_analysis import regime_and_asset_engine, get_symbol_region
from backend.research.phase19.services.calibration_analysis import calibration_analysis_engine
from backend.research.phase19.services.trade_performance import trade_performance_engine
from backend.research.phase19.services.statistical_validation import statistical_validation_engine
from backend.research.phase19.services.promotion_readiness import promotion_readiness_engine
from backend.research.phase19.services.decision_engine import phase19_decision_engine
from backend.services.phase19_service import phase19_service

client = TestClient(app)


def test_data_eligibility_audit_and_synthetic_exclusion():
    """Tests 17-point data eligibility audit and synthetic/test record exclusion."""
    mkt_ts = datetime.now(timezone.utc) - timedelta(days=2)

    with get_db_context() as db:
        # 1. Genuine LIVE Champion & Challenger pair
        rec_c = Phase18ShadowPredictionRecord(
            symbol="RELIANCE", prediction_timestamp=datetime.now(timezone.utc),
            market_timestamp=mkt_ts, feature_timestamp=mkt_ts,
            model_role="CHAMPION", model_version="XGBoost v1.0 Calibrated",
            predicted_direction="UP", probability_up=0.65, probability_down=0.35,
            confidence="HIGH", trend_regime="BULL", volatility_regime="LOW_VOLATILITY",
            current_price=2500.0, prediction_horizon=1, data_status="LIVE",
            resolved=True, resolution_timestamp=mkt_ts + timedelta(days=1),
            actual_price=2550.0, actual_direction="UP", actual_return=0.02,
            correct=True, brier_score=0.1225
        )
        rec_ch = Phase18ShadowPredictionRecord(
            symbol="RELIANCE", prediction_timestamp=datetime.now(timezone.utc),
            market_timestamp=mkt_ts, feature_timestamp=mkt_ts,
            model_role="CHALLENGER", model_version="Phase17 Large XGBoost",
            predicted_direction="UP", probability_up=0.70, probability_down=0.30,
            confidence="HIGH", trend_regime="BULL", volatility_regime="LOW_VOLATILITY",
            current_price=2500.0, prediction_horizon=1, data_status="LIVE",
            resolved=True, resolution_timestamp=mkt_ts + timedelta(days=1),
            actual_price=2550.0, actual_direction="UP", actual_return=0.02,
            correct=True, brier_score=0.0900
        )

        # 2. Synthetic fixture record (must be excluded)
        rec_syn = Phase18ShadowPredictionRecord(
            symbol="TEST_MOCK_XYZ", prediction_timestamp=datetime.now(timezone.utc),
            market_timestamp=mkt_ts, feature_timestamp=mkt_ts,
            model_role="CHALLENGER", model_version="Phase17 Large XGBoost",
            predicted_direction="UP", probability_up=0.80, probability_down=0.20,
            current_price=100.0, prediction_horizon=1, data_status="DELAYED",
            resolved=True, resolution_timestamp=mkt_ts + timedelta(days=1),
            actual_price=110.0, actual_direction="UP", actual_return=0.10,
            correct=True, brier_score=0.04
        )

        db.add_all([rec_c, rec_ch, rec_syn])
        db.commit()
        syn_id = rec_syn.id

    report, eligible = forward_data_service.perform_eligibility_audit()

    assert report["audit_status"] == "PASSED"
    assert report["synthetic_records_excluded"] >= 1
    # Ensure synthetic record was excluded from eligible records
    eligible_ids = [r.id for r in eligible]
    assert syn_id not in eligible_ids


def test_paired_dataset_construction_and_deduplication():
    """Tests paired Champion/Challenger observation matching on exact market timestamp."""
    paired = forward_data_service.get_paired_dataset(resolved_only=True)
    assert isinstance(paired, list)
    for p in paired:
        assert "champion" in p
        assert "challenger" in p
        assert p["champion"]["model_version"] == "XGBoost v1.0 Calibrated"
        assert p["challenger"]["model_version"] == "Phase17 Large XGBoost"


def test_rolling_metrics_and_insufficient_sample_threshold():
    """Tests rolling window metrics and minimum sample threshold handling (N < 10 -> accuracy = null)."""
    # Sample size < 10
    few_recs = [
        {
            "actual_direction": "UP",
            "champion": {"predicted_direction": "UP", "probability_up": 0.6},
            "challenger": {"predicted_direction": "UP", "probability_up": 0.7}
        }
    ] * 5

    res_few = calculate_metrics_for_records(few_recs, "champion")
    assert res_few["accuracy"] is None
    assert res_few["reason"] == "insufficient_forward_validation_data"

    # Sample size >= 10
    enough_recs = [
        {
            "actual_direction": "UP" if i % 2 == 0 else "DOWN",
            "champion": {"predicted_direction": "UP", "probability_up": 0.6},
            "challenger": {"predicted_direction": "UP" if i % 3 == 0 else "DOWN", "probability_up": 0.7}
        }
        for i in range(12)
    ]

    res_enough = calculate_metrics_for_records(enough_recs, "champion")
    assert res_enough["accuracy"] is not None
    assert res_enough["sample_size"] == 12


def test_per_symbol_and_asset_group_analysis():
    """Tests asset regional classification and per-symbol / asset group breakdowns."""
    assert get_symbol_region("RELIANCE") == "INDIA"
    assert get_symbol_region("AAPL") == "USA"
    assert get_symbol_region("BTC-USD") == "CRYPTO"

    paired = forward_data_service.get_paired_dataset(resolved_only=True)
    group_res = regime_and_asset_engine.compute_asset_group_results(paired)

    assert "INDIA" in group_res
    assert "USA" in group_res
    assert "CRYPTO" in group_res
    assert "ALL-ASSETS" in group_res


def test_regime_and_calibration_analysis():
    """Tests evaluation across Phase 13 regimes and probability calibration analysis."""
    paired = forward_data_service.get_paired_dataset(resolved_only=True)

    reg_res = regime_and_asset_engine.compute_regime_results(paired)
    assert "BULL" in reg_res
    assert "BEAR" in reg_res
    assert "SIDEWAYS" in reg_res

    calib_res = calibration_analysis_engine.compute_calibration_analysis(paired)
    assert "champion" in calib_res
    assert "challenger" in calib_res
    assert len(calib_res["champion"]["reliability_bins"]) == 10


def test_statistical_validation_mcnemar_and_bootstrap():
    """Tests McNemar test, 95% bootstrap confidence interval, and effect size calculation."""
    paired = forward_data_service.get_paired_dataset(resolved_only=True)
    stat_res = statistical_validation_engine.compute_statistical_tests(paired, alpha=0.05, n_bootstraps=100)

    assert "mcnemar" in stat_res
    assert "bootstrap_ci" in stat_res
    assert "statistically_significant" in stat_res


def test_trade_performance_comparison():
    """Tests Phase 14 trade setup comparison between Champion & Challenger predictions."""
    paired = forward_data_service.get_paired_dataset(resolved_only=True)
    trade_res = trade_performance_engine.compare_trade_setups(paired)

    assert "champion" in trade_res
    assert "challenger" in trade_res
    assert "comparison" in trade_res


def test_promotion_readiness_scorecard_and_zero_autopromote():
    """Tests 12-point promotion scorecard and verifies automatic promotion is hard-disabled."""
    full_res = phase19_decision_engine.run_full_phase19_analysis()
    prom_res = full_res["promotion_readiness"]

    assert prom_res["promotion_policy"] == "NOT_AUTOMATIC"
    assert prom_res["final_verdict"] in [
        "PHASE19_INSUFFICIENT_FORWARD_DATA",
        "PHASE19_CHALLENGER_REJECTED",
        "PHASE19_CHALLENGER_INCONCLUSIVE",
        "PHASE19_CHALLENGER_READY_FOR_EXPERT_REVIEW"
    ]
    assert len(prom_res["scorecard"]) == 12


def test_phase19_api_endpoints():
    """Tests all Phase 19 REST API endpoints for valid schemas and metadata."""
    endpoints = [
        "/api/research/phase19/status",
        "/api/research/phase19/summary",
        "/api/research/phase19/rolling",
        "/api/research/phase19/symbols",
        "/api/research/phase19/regimes",
        "/api/research/phase19/calibration",
        "/api/research/phase19/trades",
        "/api/research/phase19/statistics",
        "/api/research/phase19/promotion-readiness",
        "/api/research/phase19/data-quality"
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        data = res.json()
        assert data.get("mode") == "RESEARCH"
        assert data.get("production_model") == "XGBoost v1.0 Calibrated"
        assert data.get("challenger_model") == "Phase 17 Large XGBoost"


def test_production_model_isolation_mandate():
    """Verifies Phase 12 remains the active production model and Phase 17 remains shadow only."""
    status_res = phase19_service.get_status()
    assert status_res["production_model"] == "XGBoost v1.0 Calibrated"
    assert status_res["promotion_policy"] == "NOT_AUTOMATIC"
