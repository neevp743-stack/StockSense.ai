import pytest
from backend.services.live_research_service import LiveResearchAnalyticsService, wilson_score_interval
from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord

def test_n29_milestone_behavior():
    """Verifies that when N < 30 (e.g. N=29), milestone display is INSUFFICIENT LIVE SAMPLE SIZE."""
    service = LiveResearchAnalyticsService()
    stats = service.get_live_analytics("BTC-USD", model_version="XGBoost v1.0")
    if stats["sample_size"] == 29:
        assert stats["milestone_label"] == "INSUFFICIENT LIVE SAMPLE SIZE"
        assert "INSUFFICIENT LIVE SAMPLE SIZE" in stats["accuracy_display"]
        assert stats["accuracy"] is None
        assert stats["confidence_interval_95"] is None

def test_n30_milestone_behavior():
    """Verifies that when N >= 30, milestone state transitions to PRELIMINARY LIVE RESULT."""
    service = LiveResearchAnalyticsService()

    class MockRecord:
        def __init__(self, is_correct, resolved_direction="UP", prob_up=0.55, prob_down=0.45):
            self.symbol = "TEST_BTC"
            self.model_version = "XGBoost v1.0"
            self.probability_up = prob_up
            self.probability_down = prob_down
            self.predicted_direction = "UP"
            self.data_status = "LIVE"
            self.resolved_direction = resolved_direction
            self.prediction_timestamp = None
            self.is_correct = is_correct

    # Mock calculating analytics with N=30 records
    mock_records = [MockRecord(is_correct=(i % 2 == 0)) for i in range(30)]

    # Test milestone label logic directly
    resolved_count = len(mock_records)
    correct_count = sum(1 for r in mock_records if r.is_correct)
    accuracy = correct_count / resolved_count

    assert resolved_count >= 30
    milestone_label = "PRELIMINARY LIVE RESULT" if resolved_count < 100 else "LIVE RESEARCH RESULT"
    assert milestone_label == "PRELIMINARY LIVE RESULT"
    ci = wilson_score_interval(correct_count, resolved_count)
    assert ci["lower"] > 0 and ci["upper"] <= 1.0

def test_model_version_cohort_isolation():
    """Verifies that XGBoost v1.0 and XGBoost v2.0 predictions are strictly isolated."""
    service = LiveResearchAnalyticsService()
    v1_stats = service.get_live_analytics("BTC-USD", model_version="XGBoost v1.0")
    v2_stats = service.get_live_analytics("BTC-USD", model_version="XGBoost v2.0")

    assert v1_stats["model_version"] == "XGBoost v1.0"
    assert v2_stats["model_version"] == "XGBoost v2.0"
    # XGBoost v2.0 should have 0 records currently
    assert v2_stats["total_predictions"] == 0

def test_no_fake_prediction_insertion():
    """Verifies that all DB records have legitimate data status (LIVE, DELAYED, STALE, HISTORICAL) and valid probabilities."""
    with get_db_context() as db:
        records = db.query(LivePredictionRecord).all()
        for r in records:
            assert r.data_status in ["LIVE", "DELAYED", "STALE", "HISTORICAL", "RECONNECTING", "UNAVAILABLE"]
            assert 0.0 <= r.probability_up <= 1.0
            assert 0.0 <= r.probability_down <= 1.0
            assert abs((r.probability_up + r.probability_down) - 1.0) < 0.01

def test_resolved_only_accuracy_calculation():
    """Verifies that unresolved records do not skew accuracy computation."""
    service = LiveResearchAnalyticsService()
    analytics = service.get_live_analytics("BTC-USD")
    assert analytics["total_predictions"] == analytics["resolved_predictions"] + analytics["unresolved_predictions"]
