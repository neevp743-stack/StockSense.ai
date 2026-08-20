import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.live_research_service import live_research_service, wilson_score_interval
from backend.services.live_prediction_service import live_prediction_service
from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord

client = TestClient(app)

def test_wilson_score_interval_math():
    """Tests Wilson score 95% confidence interval formula accuracy."""
    ci = wilson_score_interval(15, 30)
    assert 0.0 <= ci["lower"] <= ci["center"] <= ci["upper"] <= 1.0
    assert ci["center"] == pytest.approx(0.50, abs=0.05)

def test_live_analytics_milestones():
    """Verifies sample size milestones (<30, >=30, >=100, >=500)."""
    analytics = live_research_service.get_live_analytics("BTC-USD")
    n = analytics["sample_size"]
    if n < 30:
        assert analytics["milestone_label"] == "INSUFFICIENT LIVE SAMPLE SIZE"
        assert analytics["accuracy"] is None
    elif n < 100:
        assert analytics["milestone_label"] == "PRELIMINARY LIVE RESULT"
        assert analytics["accuracy"] is not None
    elif n < 500:
        assert analytics["milestone_label"] == "LIVE RESEARCH RESULT"
    else:
        assert analytics["milestone_label"] == "LARGE LIVE SAMPLE"

def test_live_predictions_history_pagination():
    """Tests GET /api/research/live-predictions/{symbol} pagination endpoint."""
    response = client.get("/api/research/live-predictions/BTC-USD?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "page" in data
    assert "limit" in data
    assert "total_records" in data
    assert "items" in data
    assert len(data["items"]) <= 5

def test_csv_export_endpoint():
    """Tests GET /api/research/live-predictions/{symbol}/csv endpoint."""
    response = client.get("/api/research/live-predictions/BTC-USD/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "symbol,prediction_timestamp,feature_timestamp" in content

def test_baseline_calculation():
    """Verifies baseline comparison calculation logic."""
    analytics = live_research_service.get_live_analytics("BTC-USD")
    baselines = analytics["baselines"]
    assert "majority_baseline" in baselines
    assert "random_baseline" in baselines
    assert baselines["random_baseline"] == 0.5000

def test_confidence_bucket_breakdown():
    """Verifies confidence bucket analysis returns valid bucket ranges."""
    analytics = live_research_service.get_live_analytics("BTC-USD")
    buckets = analytics["confidence_buckets"]
    assert len(buckets) == 5
    bucket_labels = [b["bucket"] for b in buckets]
    assert bucket_labels == ["50-55%", "55-60%", "60-65%", "65-70%", "70%+"]

def test_daily_performance_aggregation():
    """Verifies daily performance aggregation structure."""
    analytics = live_research_service.get_live_analytics("BTC-USD")
    daily = analytics["daily_performance"]
    assert isinstance(daily, list)

def test_invalid_probability_rejection():
    """Verifies that invalid probability sums or negative probabilities are rejected/bounded."""
    with get_db_context() as db:
        invalid_rec = db.query(LivePredictionRecord).filter(
            (LivePredictionRecord.probability_up < 0) | (LivePredictionRecord.probability_up > 1.0)
        ).first()
        assert invalid_rec is None
