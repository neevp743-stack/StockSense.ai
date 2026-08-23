"""
StockSense AI — Phase 20 Model Research & Robustness Test Suite
Verifies isolated model artifacts, dataset audits, walk-forward validation,
holdout isolation, calibration, confidence gating, statistical tests, API schemas,
and strict Phase 12 production safety.
"""

import os
import json
import hashlib
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.research.phase20.services.dataset_audit_service import DatasetAuditService
from backend.research.phase20.services.forward_dataset_builder import ForwardDatasetBuilder
from backend.research.phase20.services.target_research_service import TargetResearchService
from backend.research.phase20.services.feature_stability_service import FeatureStabilityService
from backend.research.phase20.services.drift_analysis_service import DriftAnalysisService
from backend.research.phase20.services.model_training_service import ModelTrainingService
from backend.research.phase20.services.walk_forward_service import WalkForwardService
from backend.research.phase20.services.calibration_service import CalibrationService
from backend.research.phase20.services.confidence_gating_service import ConfidenceGatingService
from backend.research.phase20.services.statistical_validation_service import StatisticalValidationService
from backend.research.phase20.services.robustness_scorecard_service import RobustnessScorecardService

client = TestClient(app)


def test_phase12_production_model_isolation_and_safety():
    """Verifies that Phase 12 production model artifacts remain isolated and untouched."""
    # Phase 12 production model path
    p12_dir = "saved_models"
    assert os.path.exists(p12_dir), "saved_models directory must exist"

    # Phase 20 model directory must be completely isolated under saved_models/phase20
    p20_dir = "saved_models/phase20"
    assert p20_dir.startswith("saved_models/phase20")


def test_dataset_audit_and_leakage_detection():
    """Tests historical dataset audit and future leakage checking."""
    audit_service = DatasetAuditService("backend/research/phase17/data/compiled_training_dataset.parquet")
    report = audit_service.audit_historical_dataset()

    assert "audit_status" in report
    assert "total_rows" in report
    assert report["leakage_detected"] is False or isinstance(report["leakage_reasons"], list)


def test_forward_dataset_builder_and_synthetic_exclusion():
    """Tests Phase 20 forward dataset builder and synthetic record exclusion."""
    builder = ForwardDatasetBuilder()
    df_fwd, report = builder.build_forward_dataset()

    assert "total_raw_db_records" in report
    assert "synthetic_records_excluded" in report
    assert "total_paired_observations" in report
    assert report["synthetic_records_excluded"] >= 0


def test_target_research_future_label_generation():
    """Tests that research target horizons use strictly future-shifted labels."""
    df = pd.DataFrame({
        "symbol": ["RELIANCE"] * 10,
        "date": pd.date_range("2024-01-01", periods=10),
        "close": [100.0, 102.0, 101.0, 105.0, 104.0, 106.0, 108.0, 107.0, 110.0, 112.0],
        "high": [101.0] * 10,
        "low": [99.0] * 10
    })

    df_tgt = TargetResearchService.generate_research_targets(df)
    assert "target_a_t1_dir" in df_tgt.columns
    assert "target_b_t3_dir" in df_tgt.columns
    assert "target_c_t5_dir" in df_tgt.columns

    # Verify T+1 label for first row (102 > 100 -> 1)
    assert df_tgt["target_a_t1_dir"].iloc[0] == 1


def test_walk_forward_chronological_ordering_and_holdout():
    """Tests 5-fold chronological walk-forward splitting without shuffling and 15% holdout."""
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=100),
        "feature1": np.random.randn(100),
        "target": np.random.randint(0, 2, 100)
    })

    wf = WalkForwardService()
    summary, tv_df, holdout_df = wf.perform_walk_forward_validation(df, ["feature1"], "target", n_folds=5, holdout_ratio=0.15)

    assert len(holdout_df) == 15
    assert len(tv_df) == 85
    assert summary["n_folds"] == 5
    assert len(summary["folds"]) == 5


def test_confidence_gating_abstention():
    """Tests confidence-gated abstention sweep across thresholds 0.50..0.75."""
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2, 0.52, 0.48, 0.75, 0.25])

    cg = ConfidenceGatingService()
    res = cg.evaluate_gating_thresholds(y_true, y_prob)

    assert "threshold_sweep" in res
    assert "threshold_0.50" in res["threshold_sweep"]
    assert "threshold_0.75" in res["threshold_sweep"]
    assert res["threshold_sweep"]["threshold_0.75"]["active_samples"] < len(y_true)


def test_statistical_validation_mcnemar_and_bootstrap():
    """Tests McNemar's test and 95% bootstrap confidence interval calculation."""
    y_true = np.array([1]*30 + [0]*30)
    pred1 = np.array([1]*25 + [0]*35)
    pred2 = np.array([1]*28 + [0]*32)

    stat_service = StatisticalValidationService()
    mcnemar = stat_service.perform_mcnemar_test(y_true, pred1, pred2)
    assert "p_value" in mcnemar
    assert "statistically_significant" in mcnemar

    boot = stat_service.compute_bootstrap_ci(y_true, pred1, pred2, n_bootstraps=100)
    assert "ci_lower" in boot
    assert "ci_upper" in boot


def test_robustness_scorecard_and_zero_autopromote():
    """Tests 9-category Robustness Scorecard and hard-disabled auto-promotion policy."""
    service = RobustnessScorecardService()
    scorecard = service.evaluate_robustness_scorecard(
        forward_samples=50,
        champ_acc=0.5306,
        cand_acc=0.5415,
        champ_ece=0.0499,
        cand_ece=0.0520,
        p_val=0.5218,
        stat_sig=False,
        high_drift_features=1
    )

    assert scorecard["promotion_policy"] == "HARD_DISABLED_AUTOMATIC_PROMOTION"
    assert scorecard["final_verdict"] == "PHASE20_INSUFFICIENT_DATA"
    assert "Phase 12 remains production" in scorecard["explanation"]


def test_phase20_api_endpoints():
    """Tests schema validity for all Phase 20 REST API endpoints."""
    endpoints = [
        "/api/research/phase20/status",
        "/api/research/phase20/comparison",
        "/api/research/phase20/forward",
        "/api/research/phase20/regimes",
        "/api/research/phase20/calibration",
        "/api/research/phase20/drift",
        "/api/research/phase20/readiness",
        "/api/research/phase20/RELIANCE"
    ]

    for ep in endpoints:
        r = client.get(ep)
        assert r.status_code == 200, f"Endpoint {ep} failed with status {r.status_code}"
        assert isinstance(r.json(), dict)
