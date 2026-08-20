"""
StockSense AI — Live Research Monitoring & Statistical Validation Service
Provides paginated history, CSV data export, Wilson score 95% confidence intervals,
baseline comparison, confidence bucket analysis, daily performance logging, and sample milestone tracking.
"""

import math
import csv
import io
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord

logger = logging.getLogger(__name__)

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> Dict[str, float]:
    """Calculates Wilson score interval for binomial proportion."""
    if n == 0:
        return {"lower": 0.0, "upper": 0.0, "center": 0.0}
    p_hat = k / n
    z = 1.96  # 95% confidence
    denominator = 1 + (z**2) / n
    center_adjusted = (p_hat + (z**2) / (2 * n)) / denominator
    spread = (z * math.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * n)) / n)) / denominator
    return {
        "center": round(center_adjusted, 4),
        "lower": round(max(0.0, center_adjusted - spread), 4),
        "upper": round(min(1.0, center_adjusted + spread), 4)
    }

class LiveResearchAnalyticsService:
    """Service providing live research monitoring, analytics, and statistical validation."""

    def get_live_predictions_history(self, symbol: str, page: int = 1, limit: int = 50, model_version: Optional[str] = None) -> Dict[str, Any]:
        """Returns paginated database prediction records isolated by model version."""
        symbol_clean = symbol.upper().strip()
        page = max(1, page)
        limit = max(1, min(200, limit))
        offset = (page - 1) * limit

        try:
            with get_db_context() as db:
                query = db.query(LivePredictionRecord).filter(LivePredictionRecord.symbol == symbol_clean)
                if model_version:
                    query = query.filter(LivePredictionRecord.model_version == model_version)

                total_records = query.count()
                records = query.order_by(LivePredictionRecord.prediction_timestamp.desc()).offset(offset).limit(limit).all()

                items = []
                for r in records:
                    items.append({
                        "id": r.id,
                        "symbol": r.symbol,
                        "prediction_timestamp": r.prediction_timestamp.isoformat() if r.prediction_timestamp else None,
                        "feature_timestamp": r.feature_timestamp.isoformat() if r.feature_timestamp else None,
                        "model_version": r.model_version,
                        "probability_up": r.probability_up,
                        "probability_down": r.probability_down,
                        "predicted_direction": r.predicted_direction,
                        "data_status": r.data_status,
                        "resolved_direction": r.resolved_direction,
                        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                        "is_correct": r.is_correct
                    })

                total_pages = math.ceil(total_records / limit) if total_records > 0 else 1
                return {
                    "symbol": symbol_clean,
                    "model_version": model_version,
                    "page": page,
                    "limit": limit,
                    "total_records": total_records,
                    "total_pages": total_pages,
                    "items": items
                }
        except Exception as e:
            logger.error(f"Error fetching prediction history: {e}")
            return {"symbol": symbol_clean, "model_version": model_version, "page": page, "limit": limit, "total_records": 0, "total_pages": 1, "items": []}

    def export_live_predictions_csv(self, symbol: str, model_version: Optional[str] = None) -> str:
        """Generates CSV export string for symbol prediction records."""
        symbol_clean = symbol.upper().strip()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "symbol", "prediction_timestamp", "feature_timestamp", "model_version",
            "probability_up", "probability_down", "predicted_direction", "data_status",
            "resolved_direction", "resolved_at", "is_correct"
        ])

        try:
            with get_db_context() as db:
                query = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.symbol == symbol_clean
                )
                if model_version:
                    query = query.filter(LivePredictionRecord.model_version == model_version)

                records = query.order_by(LivePredictionRecord.prediction_timestamp.asc()).all()

                for r in records:
                    writer.writerow([
                        r.symbol,
                        r.prediction_timestamp.isoformat() if r.prediction_timestamp else "",
                        r.feature_timestamp.isoformat() if r.feature_timestamp else "",
                        r.model_version,
                        r.probability_up,
                        r.probability_down,
                        r.predicted_direction,
                        r.data_status,
                        r.resolved_direction or "",
                        r.resolved_at.isoformat() if r.resolved_at else "",
                        "1" if r.is_correct is True else ("0" if r.is_correct is False else "")
                    ])
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")

        return output.getvalue()

    def get_live_analytics(self, symbol: str, model_version: Optional[str] = "XGBoost v1.0") -> Dict[str, Any]:
        """Calculates statistical research monitoring analytics strictly isolated by model version cohort."""
        symbol_clean = symbol.upper().strip()
        try:
            with get_db_context() as db:
                query = db.query(LivePredictionRecord).filter(LivePredictionRecord.symbol == symbol_clean)
                if model_version:
                    query = query.filter(LivePredictionRecord.model_version == model_version)

                records = query.all()
                total_preds = len(records)
                resolved_records = [r for r in records if r.resolved_direction is not None]
                resolved_count = len(resolved_records)
                unresolved_count = total_preds - resolved_count
                correct_count = sum(1 for r in resolved_records if r.is_correct is True)
                wrong_count = sum(1 for r in resolved_records if r.is_correct is False)

                accuracy = (correct_count / resolved_count) if resolved_count > 0 else None

                # Sample Size Milestone
                if resolved_count < 30:
                    milestone_label = "INSUFFICIENT LIVE SAMPLE SIZE"
                    accuracy_display = f"INSUFFICIENT LIVE SAMPLE SIZE (N={resolved_count}/30)"
                elif resolved_count < 100:
                    milestone_label = "PRELIMINARY LIVE RESULT"
                    accuracy_display = f"{(accuracy * 100):.1f}% (N={resolved_count})"
                elif resolved_count < 500:
                    milestone_label = "LIVE RESEARCH RESULT"
                    accuracy_display = f"{(accuracy * 100):.1f}% (N={resolved_count})"
                else:
                    milestone_label = "LARGE LIVE SAMPLE"
                    accuracy_display = f"{(accuracy * 100):.1f}% (N={resolved_count})"

                # Baselines
                majority_direction = "UP"
                if resolved_count > 0:
                    up_actuals = sum(1 for r in resolved_records if r.resolved_direction == "UP")
                    down_actuals = resolved_count - up_actuals
                    majority_direction = "UP" if up_actuals >= down_actuals else "DOWN"
                    majority_acc = max(up_actuals, down_actuals) / resolved_count
                else:
                    majority_acc = 0.50

                random_acc = 0.50
                diff_vs_majority = (accuracy - majority_acc) if accuracy is not None else None
                diff_vs_random = (accuracy - random_acc) if accuracy is not None else None

                # Confidence Buckets
                buckets_def = [
                    ("50-55%", 0.50, 0.55),
                    ("55-60%", 0.55, 0.60),
                    ("60-65%", 0.60, 0.65),
                    ("65-70%", 0.65, 0.70),
                    ("70%+", 0.70, 1.00),
                ]
                bucket_results = []
                for b_name, b_min, b_max in buckets_def:
                    b_recs = [r for r in records if b_min <= max(r.probability_up, r.probability_down) < (b_max + 1e-5)]
                    b_total = len(b_recs)
                    b_res = [r for r in b_recs if r.resolved_direction is not None]
                    b_res_count = len(b_res)
                    b_correct = sum(1 for r in b_res if r.is_correct is True)
                    b_acc = (b_correct / b_res_count) if b_res_count > 0 else None
                    bucket_results.append({
                        "bucket": b_name,
                        "total_predictions": b_total,
                        "resolved_predictions": b_res_count,
                        "correct_predictions": b_correct,
                        "accuracy": round(b_acc, 4) if b_acc is not None else None,
                        "accuracy_display": f"{(b_acc * 100):.1f}%" if (b_acc is not None and b_res_count >= 5) else "N/A"
                    })

                # Daily Aggregation
                daily_map: Dict[str, Dict[str, int]] = {}
                for r in records:
                    date_str = r.prediction_timestamp.strftime("%Y-%m-%d") if r.prediction_timestamp else "Unknown"
                    if date_str not in daily_map:
                        daily_map[date_str] = {"total": 0, "resolved": 0, "correct": 0, "wrong": 0}
                    daily_map[date_str]["total"] += 1
                    if r.resolved_direction is not None:
                        daily_map[date_str]["resolved"] += 1
                        if r.is_correct:
                            daily_map[date_str]["correct"] += 1
                        else:
                            daily_map[date_str]["wrong"] += 1

                daily_table = []
                for d_str in sorted(daily_map.keys(), reverse=True):
                    d_info = daily_map[d_str]
                    d_acc = (d_info["correct"] / d_info["resolved"]) if d_info["resolved"] > 0 else None
                    daily_table.append({
                        "date": d_str,
                        "total": d_info["total"],
                        "resolved": d_info["resolved"],
                        "correct": d_info["correct"],
                        "wrong": d_info["wrong"],
                        "accuracy_display": f"{(d_acc * 100):.1f}%" if d_acc is not None else "N/A"
                    })

                # Wilson Score Confidence Interval
                ci_95 = wilson_score_interval(correct_count, resolved_count) if resolved_count >= 30 else None

                return {
                    "symbol": symbol_clean,
                    "model_version": model_version or "XGBoost v1.0",
                    "milestone_label": milestone_label,
                    "total_predictions": total_preds,
                    "resolved_predictions": resolved_count,
                    "unresolved_predictions": unresolved_count,
                    "correct_predictions": correct_count,
                    "wrong_predictions": wrong_count,
                    "accuracy": round(accuracy, 4) if (accuracy is not None and resolved_count >= 30) else None,
                    "accuracy_display": accuracy_display,
                    "sample_size": resolved_count,
                    "sample_size_threshold_met": resolved_count >= 30,
                    "confidence_interval_95": ci_95,
                    "baselines": {
                        "ai_accuracy": round(accuracy, 4) if accuracy is not None else None,
                        "majority_baseline": round(majority_acc, 4),
                        "random_baseline": 0.5000,
                        "diff_vs_majority": round(diff_vs_majority, 4) if diff_vs_majority is not None else None,
                        "diff_vs_random": round(diff_vs_random, 4) if diff_vs_random is not None else None,
                    },
                    "confidence_buckets": bucket_results,
                    "daily_performance": daily_table
                }
        except Exception as e:
            logger.error(f"Error calculating live analytics: {e}")
            return {
                "symbol": symbol_clean,
                "model_version": model_version or "XGBoost v1.0",
                "milestone_label": "INSUFFICIENT LIVE SAMPLE SIZE",
                "total_predictions": 0,
                "resolved_predictions": 0,
                "unresolved_predictions": 0,
                "correct_predictions": 0,
                "wrong_predictions": 0,
                "accuracy": None,
                "accuracy_display": "INSUFFICIENT LIVE SAMPLE SIZE (N=0/30)",
                "sample_size": 0,
                "sample_size_threshold_met": False,
                "confidence_interval_95": None,
                "baselines": {"ai_accuracy": None, "majority_baseline": 0.5, "random_baseline": 0.5, "diff_vs_majority": None, "diff_vs_random": None},
                "confidence_buckets": [],
                "daily_performance": []
            }

# Global Singleton Service
live_research_service = LiveResearchAnalyticsService()

