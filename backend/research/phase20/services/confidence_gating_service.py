"""
StockSense AI — Phase 20 Confidence-Gated Abstention Service
Evaluates confidence threshold gating (0.50, 0.55, 0.60, 0.65, 0.70, 0.75).
Allows model to abstain (output HOLD/NO-SIGNAL) when evidence is weak.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, precision_score, recall_score, brier_score_loss


class ConfidenceGatingService:
    """Evaluates coverage, accuracy, precision, recall, and trading stats across abstention thresholds."""

    def evaluate_gating_thresholds(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        thresholds: List[float] = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
    ) -> Dict[str, Any]:
        """
        Evaluates predictions gated at various confidence thresholds.
        """
        total = len(y_true)
        if total == 0:
            return {"thresholds": {}}

        results = {}
        conf = np.maximum(y_prob, 1.0 - y_prob)
        y_pred_raw = (y_prob >= 0.5).astype(int)

        for thresh in thresholds:
            active_mask = conf >= thresh
            active_count = int(np.sum(active_mask))
            coverage = float(active_count / total)

            if active_count > 0:
                y_act_true = y_true[active_mask]
                y_act_pred = y_pred_raw[active_mask]
                y_act_prob = y_prob[active_mask]

                acc = float(accuracy_score(y_act_true, y_act_pred))
                prec = float(precision_score(y_act_true, y_act_pred, zero_division=0))
                rec = float(recall_score(y_act_true, y_act_pred, zero_division=0))
                brier = float(brier_score_loss(y_act_true, y_act_prob))
            else:
                acc = None
                prec = None
                rec = None
                brier = None

            results[f"threshold_{thresh:.2f}"] = {
                "threshold": thresh,
                "coverage_ratio": round(coverage, 4),
                "active_samples": active_count,
                "abstained_samples": total - active_count,
                "accuracy": round(acc, 4) if acc is not None else None,
                "precision": round(prec, 4) if prec is not None else None,
                "recall": round(rec, 4) if rec is not None else None,
                "brier_score": round(brier, 4) if brier is not None else None
            }

        return {
            "total_evaluations": total,
            "threshold_sweep": results,
            "recommended_threshold": 0.60
        }
