"""
StockSense AI — Phase 20 Probability Calibration Service
Evaluates Platt scaling, Isotonic regression, and Beta calibration on validation folds.
Calculates Expected Calibration Error (ECE), Brier Score, Log Loss, 10 reliability bins, and confidence band breakdowns.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.metrics import brier_score_loss, log_loss, accuracy_score


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Tuple[float, List[Dict[str, Any]]]:
    """Computes Expected Calibration Error (ECE) and 10 reliability bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_assignments = np.digitize(y_prob, bins) - 1
    bin_assignments = np.clip(bin_assignments, 0, n_bins - 1)

    total_samples = len(y_true)
    ece = 0.0
    reliability_bins = []

    for i in range(n_bins):
        bin_mask = bin_assignments == i
        bin_size = int(np.sum(bin_mask))
        bin_lower = float(bins[i])
        bin_upper = float(bins[i + 1])

        if bin_size > 0:
            avg_confidence = float(np.mean(y_prob[bin_mask]))
            avg_accuracy = float(np.mean(y_true[bin_mask]))
            gap = float(abs(avg_accuracy - avg_confidence))
            ece += (bin_size / max(total_samples, 1)) * gap
        else:
            avg_confidence = float((bin_lower + bin_upper) / 2.0)
            avg_accuracy = 0.0
            gap = 0.0

        reliability_bins.append({
            "bin": i + 1,
            "bin_lower": round(bin_lower, 2),
            "bin_upper": round(bin_upper, 2),
            "sample_count": bin_size,
            "mean_confidence": round(avg_confidence, 4),
            "mean_accuracy": round(avg_accuracy, 4),
            "calibration_gap": round(gap, 4)
        })

    return round(float(ece), 4), reliability_bins


class CalibrationService:
    """Evaluates calibration quality across Platt scaling, Isotonic, and Beta calibration."""

    def evaluate_model_calibration(self, y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
        """
        Calculates ECE, Brier score, Log Loss, reliability curve, and confidence band breakdowns.
        """
        if len(y_true) == 0:
            return {
                "ece": None, "brier_score": None, "log_loss": None,
                "reliability_bins": [], "confidence_bands": {}
            }

        brier = float(brier_score_loss(y_true, y_prob))
        eps = 1e-15
        y_prob_clipped = np.clip(y_prob, eps, 1 - eps)
        ll = float(log_loss(y_true, y_prob_clipped, labels=[0, 1]))
        ece, bins = compute_ece(y_true, y_prob)

        # Confidence band breakdown
        conf_bands = {}
        bands = [
            ("0.50-0.55", 0.50, 0.55),
            ("0.55-0.60", 0.55, 0.60),
            ("0.60-0.70", 0.60, 0.70),
            ("0.70-0.80", 0.70, 0.80),
            ("0.80+", 0.80, 1.01)
        ]

        conf = np.maximum(y_prob, 1.0 - y_prob)
        for label, low, high in bands:
            mask = (conf >= low) & (conf < high)
            cnt = int(np.sum(mask))
            if cnt > 0:
                acc = float(accuracy_score(y_true[mask], (y_prob[mask] >= 0.5).astype(int)))
            else:
                acc = 0.0
            conf_bands[label] = {
                "sample_count": cnt,
                "accuracy": round(acc, 4) if cnt > 0 else None
            }

        return {
            "brier_score": round(brier, 4),
            "log_loss": round(ll, 4),
            "ece": round(ece, 4),
            "reliability_bins": bins,
            "confidence_bands": conf_bands
        }
