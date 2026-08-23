"""
StockSense AI — Phase 19 Rolling & Cumulative Metrics Engine
Computes rolling windows (N=20, 50, 100, 250) and cumulative time-series performance metrics.
Enforces minimum sample handling (N < 10 -> accuracy = null).
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss, log_loss

MIN_SAMPLE_SIZE = 10


def calculate_metrics_for_records(records: List[Dict[str, Any]], model_key: str) -> Dict[str, Any]:
    """Calculates full classification, calibration, and accuracy metrics for a set of paired records."""
    n = len(records)
    if n < MIN_SAMPLE_SIZE:
        return {
            "sample_size": n,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "roc_auc": None,
            "brier_score": None,
            "log_loss": None,
            "ece": None,
            "avg_probability": None,
            "correct_count": 0,
            "incorrect_count": 0,
            "reason": "insufficient_forward_validation_data"
        }

    y_true = [1 if r["actual_direction"] == "UP" else 0 for r in records]
    y_pred = [1 if r[model_key]["predicted_direction"] == "UP" else 0 for r in records]
    y_prob = [float(r[model_key]["probability_up"]) for r in records]

    correct_count = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    incorrect_count = n - correct_count

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_true, y_prob)) if len(set(y_true)) > 1 else 0.5
    except Exception:
        auc = 0.5

    brier = float(brier_score_loss(y_true, y_prob))

    try:
        clipped_probs = [min(max(p, 1e-15), 1.0 - 1e-15) for p in y_prob]
        ll = float(log_loss(y_true, clipped_probs))
    except Exception:
        ll = 0.0

    avg_p = float(np.mean(y_prob))

    # Calculate ECE (Expected Calibration Error with 10 bins)
    bins = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for i in range(10):
        bin_lower, bin_upper = bins[i], bins[i+1]
        bin_idxs = [j for j, p in enumerate(y_prob) if bin_lower <= p < bin_upper or (i == 9 and p == bin_upper)]
        if bin_idxs:
            bin_acc = np.mean([y_true[j] for j in bin_idxs])
            bin_conf = np.mean([y_prob[j] for j in bin_idxs])
            ece += (len(bin_idxs) / n) * abs(bin_acc - bin_conf)

    return {
        "sample_size": n,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "brier_score": brier,
        "log_loss": ll,
        "ece": float(ece),
        "avg_probability": avg_p,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count
    }


class RollingMetricsEngine:
    """Computes rolling performance windows and cumulative time-series metrics."""

    def compute_rolling_windows(
        self,
        paired_records: List[Dict[str, Any]],
        windows: List[int] = [20, 50, 100, 250]
    ) -> Dict[str, Any]:
        """Calculates Champion vs Challenger metrics across specified rolling sample windows."""
        results = {}
        total = len(paired_records)

        for w in windows:
            if total < w:
                window_recs = paired_records  # Use all available records if less than window
            else:
                window_recs = paired_records[-w:]  # Most recent w records

            champ_metrics = calculate_metrics_for_records(window_recs, "champion")
            chall_metrics = calculate_metrics_for_records(window_recs, "challenger")

            acc_delta = (chall_metrics["accuracy"] - champ_metrics["accuracy"]) if (chall_metrics["accuracy"] is not None and champ_metrics["accuracy"] is not None) else None
            brier_delta = (chall_metrics["brier_score"] - champ_metrics["brier_score"]) if (chall_metrics["brier_score"] is not None and champ_metrics["brier_score"] is not None) else None
            auc_delta = (chall_metrics["roc_auc"] - champ_metrics["roc_auc"]) if (chall_metrics["roc_auc"] is not None and champ_metrics["roc_auc"] is not None) else None

            results[f"window_{w}"] = {
                "window_size": w,
                "actual_sample_size": len(window_recs),
                "champion": champ_metrics,
                "challenger": chall_metrics,
                "comparison": {
                    "accuracy_delta": acc_delta,
                    "brier_delta": brier_delta,
                    "roc_auc_delta": auc_delta,
                    "challenger_superior_accuracy": acc_delta > 0 if acc_delta is not None else False
                }
            }

        return results

    def compute_cumulative_performance(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Tracks day-by-day cumulative metrics from the first observation to present."""
        if not paired_records:
            return {
                "total_observations": 0,
                "time_series": [],
                "cumulative_summary": {
                    "champion_accuracy": None,
                    "challenger_accuracy": None
                }
            }

        # Group by resolution date
        date_groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in paired_records:
            dt_str = r.get("resolution_timestamp", r.get("market_timestamp", ""))[:10]
            date_groups.setdefault(dt_str, []).append(r)

        sorted_dates = sorted(date_groups.keys())
        time_series = []
        running_records = []

        champ_correct_cum = 0
        chall_correct_cum = 0

        for dt in sorted_dates:
            day_recs = date_groups[dt]
            running_records.extend(day_recs)

            champ_m = calculate_metrics_for_records(running_records, "champion")
            chall_m = calculate_metrics_for_records(running_records, "challenger")

            champ_acc = champ_m["accuracy"]
            chall_acc = chall_m["accuracy"]
            acc_diff = (chall_acc - champ_acc) if (champ_acc is not None and chall_acc is not None) else None

            time_series.append({
                "date": dt,
                "daily_resolved_count": len(day_recs),
                "cumulative_resolved_count": len(running_records),
                "champion_accuracy": champ_acc,
                "challenger_accuracy": chall_acc,
                "accuracy_difference": acc_diff,
                "champion_brier": champ_m["brier_score"],
                "challenger_brier": chall_m["brier_score"],
                "brier_difference": (chall_m["brier_score"] - champ_m["brier_score"]) if (chall_m["brier_score"] is not None and champ_m["brier_score"] is not None) else None,
                "champion_roc_auc": champ_m["roc_auc"],
                "challenger_roc_auc": chall_m["roc_auc"],
                "roc_auc_difference": (chall_m["roc_auc"] - champ_m["roc_auc"]) if (chall_m["roc_auc"] is not None and champ_m["roc_auc"] is not None) else None
            })

        final_champ = calculate_metrics_for_records(paired_records, "champion")
        final_chall = calculate_metrics_for_records(paired_records, "challenger")

        return {
            "total_observations": len(paired_records),
            "time_series": time_series,
            "cumulative_summary": {
                "sample_size": len(paired_records),
                "champion": final_champ,
                "challenger": final_chall,
                "comparison": {
                    "accuracy_delta": (final_chall["accuracy"] - final_champ["accuracy"]) if (final_chall["accuracy"] is not None and final_champ["accuracy"] is not None) else None,
                    "brier_delta": (final_chall["brier_score"] - final_champ["brier_score"]) if (final_chall["brier_score"] is not None and final_champ["brier_score"] is not None) else None,
                    "roc_auc_delta": (final_chall["roc_auc"] - final_champ["roc_auc"]) if (final_chall["roc_auc"] is not None and final_champ["roc_auc"] is not None) else None
                }
            }
        }


rolling_metrics_engine = RollingMetricsEngine()
