"""
StockSense AI — Phase 19 Calibration & Confidence Analysis Engine
Evaluates probability calibration, Expected Calibration Error (ECE), 10 reliability bins,
and probability confidence band breakdowns (0.50-0.55, 0.55-0.60, 0.60-0.70, 0.70-0.80, 0.80+).
"""

import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import brier_score_loss, accuracy_score


class CalibrationAnalysisEngine:
    """Evaluates probability calibration curves and confidence band accuracy."""

    CONFIDENCE_BINS = [
        {"label": "0.50-0.55", "min": 0.50, "max": 0.55},
        {"label": "0.55-0.60", "min": 0.55, "max": 0.60},
        {"label": "0.60-0.70", "min": 0.60, "max": 0.70},
        {"label": "0.70-0.80", "min": 0.70, "max": 0.80},
        {"label": "0.80+", "min": 0.80, "max": 1.01}
    ]

    def compute_confidence_analysis(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates performance across probability confidence bands for both models."""
        champ_bins = {}
        chall_bins = {}

        for b in self.CONFIDENCE_BINS:
            label = b["label"]
            low, high = b["min"], b["max"]

            # Filter for Champion in bin
            champ_recs = [r for r in paired_records if low <= float(r["champion"]["probability_up"]) < high or (high == 1.01 and float(r["champion"]["probability_up"]) >= 0.80)]
            champ_bins[label] = self._evaluate_bin(champ_recs, "champion")

            # Filter for Challenger in bin
            chall_recs = [r for r in paired_records if low <= float(r["challenger"]["probability_up"]) < high or (high == 1.01 and float(r["challenger"]["probability_up"]) >= 0.80)]
            chall_bins[label] = self._evaluate_bin(chall_recs, "challenger")

        return {
            "total_records": len(paired_records),
            "champion_confidence_bands": champ_bins,
            "challenger_confidence_bands": chall_bins
        }

    def _evaluate_bin(self, recs: List[Dict[str, Any]], model_key: str) -> Dict[str, Any]:
        n = len(recs)
        if n == 0:
            return {
                "sample_count": 0,
                "actual_success_rate": None,
                "avg_probability": None,
                "calibration_gap": None,
                "brier_score": None,
                "accuracy": None
            }

        y_true = [1 if r["actual_direction"] == "UP" else 0 for r in recs]
        y_pred = [1 if r[model_key]["predicted_direction"] == "UP" else 0 for r in recs]
        y_prob = [float(r[model_key]["probability_up"]) for r in recs]

        actual_success_rate = float(np.mean(y_true))
        avg_prob = float(np.mean(y_prob))
        calib_gap = abs(avg_prob - actual_success_rate)
        brier = float(brier_score_loss(y_true, y_prob)) if n > 0 else 0.0
        acc = float(accuracy_score(y_true, y_pred))

        return {
            "sample_count": n,
            "actual_success_rate": round(actual_success_rate, 4),
            "avg_probability": round(avg_prob, 4),
            "calibration_gap": round(calib_gap, 4),
            "brier_score": round(brier, 4),
            "accuracy": round(acc, 4)
        }

    def compute_calibration_analysis(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates Brier Score, ECE, and 10 reliability bins for frontend visualization."""
        total = len(paired_records)
        bins = np.linspace(0.0, 1.0, 11)

        if total == 0:
            empty_reliability = [
                {
                    "bin_index": i,
                    "bin_range": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                    "sample_count": 0,
                    "actual_frequency": None,
                    "mean_predicted_probability": round(float((bins[i] + bins[i+1]) / 2.0), 4),
                    "calibration_gap": None
                }
                for i in range(10)
            ]
            return {
                "sample_size": 0,
                "champion": {"brier_score": None, "ece": None, "reliability_bins": empty_reliability},
                "challenger": {"brier_score": None, "ece": None, "reliability_bins": empty_reliability},
                "comparison": {"brier_delta": None, "ece_delta": None}
            }

        champ_res = self._compute_model_calibration(paired_records, "champion")
        chall_res = self._compute_model_calibration(paired_records, "challenger")

        return {
            "sample_size": total,
            "champion": champ_res,
            "challenger": chall_res,
            "comparison": {
                "brier_delta": (chall_res["brier_score"] - champ_res["brier_score"]) if (chall_res["brier_score"] is not None and champ_res["brier_score"] is not None) else None,
                "ece_delta": (chall_res["ece"] - champ_res["ece"]) if (chall_res["ece"] is not None and champ_res["ece"] is not None) else None
            }
        }

    def _compute_model_calibration(self, records: List[Dict[str, Any]], model_key: str) -> Dict[str, Any]:
        total = len(records)
        y_true = [1 if r["actual_direction"] == "UP" else 0 for r in records]
        y_prob = [float(r[model_key]["probability_up"]) for r in records]

        brier = float(brier_score_loss(y_true, y_prob))

        bins = np.linspace(0.0, 1.0, 11)
        reliability_bins = []
        ece = 0.0

        for i in range(10):
            bin_lower, bin_upper = bins[i], bins[i+1]
            bin_idxs = [j for j, p in enumerate(y_prob) if bin_lower <= p < bin_upper or (i == 9 and p == bin_upper)]
            bin_count = len(bin_idxs)

            if bin_count > 0:
                bin_acc = float(np.mean([y_true[j] for j in bin_idxs]))
                bin_conf = float(np.mean([y_prob[j] for j in bin_idxs]))
                gap = abs(bin_acc - bin_conf)
                ece += (bin_count / total) * gap
            else:
                bin_acc = None
                bin_conf = float((bin_lower + bin_upper) / 2.0)
                gap = None

            reliability_bins.append({
                "bin_index": i,
                "bin_range": f"{bin_lower:.1f}-{bin_upper:.1f}",
                "sample_count": bin_count,
                "actual_frequency": bin_acc,
                "mean_predicted_probability": round(bin_conf, 4),
                "calibration_gap": round(gap, 4) if gap is not None else None
            })

        return {
            "brier_score": round(brier, 4),
            "ece": round(float(ece), 4),
            "mean_predicted_probability": round(float(np.mean(y_prob)), 4),
            "observed_frequency": round(float(np.mean(y_true)), 4),
            "overall_calibration_gap": round(abs(np.mean(y_prob) - np.mean(y_true)), 4),
            "reliability_bins": reliability_bins
        }


calibration_analysis_engine = CalibrationAnalysisEngine()
