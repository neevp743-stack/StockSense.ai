"""
StockSense AI — Comparison Engine (Phase 18)
Evaluates paired Champion vs Challenger metrics across forward observations, rolling windows,
asset groups (India, USA, Crypto), market regimes, and confidence calibration bins.
Enforces strict minimum sample size handling (N < 10 -> accuracy = null).
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss, log_loss

from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker
from backend.research.phase18.forward_resolver import get_asset_region

logger = logging.getLogger(__name__)


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculates Expected Calibration Error (ECE)."""
    if len(y_true) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        in_bin = (y_prob >= bin_boundaries[i]) & (y_prob < bin_boundaries[i + 1])
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)


def calculate_model_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """Calculates comprehensive classification and calibration metrics."""
    n = len(y_true)
    if n < 10:
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
            "avg_probability": float(np.mean(y_prob)) if n > 0 else None,
            "reason": "insufficient_forward_validation_data"
        }

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.50
    except Exception:
        auc = 0.50

    brier = float(brier_score_loss(y_true, y_prob))
    
    # Clip proba for log loss
    y_prob_clipped = np.clip(y_prob, 1e-15, 1 - 1e-15)
    try:
        loss = float(log_loss(y_true, y_prob_clipped))
    except Exception:
        loss = 0.6931

    ece_val = calculate_ece(y_true, y_prob)

    return {
        "sample_size": n,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "brier_score": brier,
        "log_loss": loss,
        "ece": ece_val,
        "avg_probability": float(np.mean(y_prob))
    }


class ComparisonEngine:
    """
    Core performance evaluation and Champion vs Challenger comparative engine.
    """

    def evaluate_paired_comparison(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates paired Champion vs Challenger predictions matched on equivalent observations.
        """
        pairs = shadow_prediction_tracker.get_paired_records(symbol=symbol, resolved_only=True)
        n = len(pairs)

        if n < 10:
            return {
                "sample_size": n,
                "status": "INSUFFICIENT_DATA",
                "reason": "insufficient_forward_validation_data",
                "champion": {"accuracy": None, "sample_size": n},
                "challenger": {"accuracy": None, "sample_size": n},
                "comparison": {}
            }

        y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in pairs])

        # Champion arrays
        y_pred_champ = np.array([1 if p[0].predicted_direction == "UP" else 0 for p in pairs])
        y_prob_champ = np.array([p[0].probability_up for p in pairs])

        # Challenger arrays
        y_pred_chall = np.array([1 if p[1].predicted_direction == "UP" else 0 for p in pairs])
        y_prob_chall = np.array([p[1].probability_up for p in pairs])

        m_champ = calculate_model_metrics(y_true, y_pred_champ, y_prob_champ)
        m_chall = calculate_model_metrics(y_true, y_pred_chall, y_prob_chall)

        acc_delta = (m_chall["accuracy"] - m_champ["accuracy"]) if m_chall["accuracy"] is not None and m_champ["accuracy"] is not None else None
        auc_delta = (m_chall["roc_auc"] - m_champ["roc_auc"]) if m_chall["roc_auc"] is not None and m_champ["roc_auc"] is not None else None
        brier_delta = (m_chall["brier_score"] - m_champ["brier_score"]) if m_chall["brier_score"] is not None and m_champ["brier_score"] is not None else None
        ece_delta = (m_chall["ece"] - m_champ["ece"]) if m_chall["ece"] is not None and m_champ["ece"] is not None else None

        return {
            "sample_size": n,
            "status": "EVALUATED",
            "champion": m_champ,
            "challenger": m_chall,
            "comparison": {
                "accuracy_delta": acc_delta,
                "roc_auc_delta": auc_delta,
                "brier_delta": brier_delta,  # Negative is better
                "ece_delta": ece_delta,      # Negative is better
                "challenger_superior_accuracy": bool(acc_delta > 0) if acc_delta is not None else False,
                "challenger_superior_auc": bool(auc_delta > 0) if auc_delta is not None else False,
                "challenger_superior_brier": bool(brier_delta < 0) if brier_delta is not None else False
            }
        }

    def evaluate_rolling_windows(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Evaluates rolling window performance across N in [20, 50, 100, 250]."""
        pairs = shadow_prediction_tracker.get_paired_records(symbol=symbol, resolved_only=True)
        results = {}
        windows = [20, 50, 100, 250]

        for w in windows:
            if len(pairs) < w:
                results[f"N_{w}"] = {
                    "sample_size": len(pairs),
                    "target_window": w,
                    "status": "INSUFFICIENT_DATA",
                    "accuracy": None
                }
            else:
                recent_pairs = pairs[-w:]
                y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in recent_pairs])
                y_pred_c = np.array([1 if p[0].predicted_direction == "UP" else 0 for p in recent_pairs])
                y_prob_c = np.array([p[0].probability_up for p in recent_pairs])
                y_pred_ch = np.array([1 if p[1].predicted_direction == "UP" else 0 for p in recent_pairs])
                y_prob_ch = np.array([p[1].probability_up for p in recent_pairs])

                mc = calculate_model_metrics(y_true, y_pred_c, y_prob_c)
                mch = calculate_model_metrics(y_true, y_pred_ch, y_prob_ch)
                results[f"N_{w}"] = {
                    "sample_size": w,
                    "champion": mc,
                    "challenger": mch,
                    "accuracy_delta": mch["accuracy"] - mc["accuracy"]
                }

        return results

    def evaluate_asset_groups(self) -> Dict[str, Any]:
        """Groups paired results into INDIA, USA, and CRYPTO asset classes."""
        pairs = shadow_prediction_tracker.get_paired_records(resolved_only=True)
        grouped = {"INDIA": [], "USA": [], "CRYPTO": []}

        for p in pairs:
            reg = get_asset_region(p[0].symbol)
            if reg in grouped:
                grouped[reg].append(p)

        out = {}
        for reg, p_list in grouped.items():
            n = len(p_list)
            if n < 10:
                out[reg] = {"sample_size": n, "status": "INSUFFICIENT_DATA", "accuracy": None}
            else:
                y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in p_list])
                y_pred_c = np.array([1 if p[0].predicted_direction == "UP" else 0 for p in p_list])
                y_prob_c = np.array([p[0].probability_up for p in p_list])
                y_pred_ch = np.array([1 if p[1].predicted_direction == "UP" else 0 for p in p_list])
                y_prob_ch = np.array([p[1].probability_up for p in p_list])

                mc = calculate_model_metrics(y_true, y_pred_c, y_prob_c)
                mch = calculate_model_metrics(y_true, y_pred_ch, y_prob_ch)
                out[reg] = {
                    "sample_size": n,
                    "champion": mc,
                    "challenger": mch,
                    "accuracy_delta": mch["accuracy"] - mc["accuracy"],
                    "auc_delta": mch["roc_auc"] - mc["roc_auc"],
                    "brier_delta": mch["brier_score"] - mc["brier_score"]
                }

        return out

    def evaluate_regimes(self) -> Dict[str, Any]:
        """Evaluates paired metrics broken down by Phase 13 market regimes."""
        pairs = shadow_prediction_tracker.get_paired_records(resolved_only=True)
        regimes = ["BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY", "LOW_VOLATILITY"]
        out = {}

        for r in regimes:
            # Match trend or volatility regime
            r_pairs = [p for p in pairs if p[0].trend_regime == r or p[0].volatility_regime == r]
            n = len(r_pairs)
            if n < 10:
                out[r] = {"sample_size": n, "status": "INSUFFICIENT_DATA", "accuracy": None}
            else:
                y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in r_pairs])
                y_pred_c = np.array([1 if p[0].predicted_direction == "UP" else 0 for p in r_pairs])
                y_prob_c = np.array([p[0].probability_up for p in r_pairs])
                y_pred_ch = np.array([1 if p[1].predicted_direction == "UP" else 0 for p in r_pairs])
                y_prob_ch = np.array([p[1].probability_up for p in r_pairs])

                mc = calculate_model_metrics(y_true, y_pred_c, y_prob_c)
                mch = calculate_model_metrics(y_true, y_pred_ch, y_prob_ch)
                out[r] = {
                    "sample_size": n,
                    "champion": mc,
                    "challenger": mch,
                    "accuracy_delta": mch["accuracy"] - mc["accuracy"]
                }

        return out

    def evaluate_confidence_bins(self) -> Dict[str, Any]:
        """Evaluates confidence bin accuracy and calibration gaps."""
        pairs = shadow_prediction_tracker.get_paired_records(resolved_only=True)
        bins = [(0.50, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 0.80), (0.80, 1.00)]
        out = {"champion": {}, "challenger": {}}

        if not pairs:
            return out

        y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in pairs])
        prob_c = np.array([p[0].probability_up for p in pairs])
        prob_ch = np.array([p[1].probability_up for p in pairs])

        for (b_min, b_max) in bins:
            bin_name = f"{b_min:.2f}-{b_max:.2f}"
            # Champion
            mask_c = (prob_c >= b_min) & (prob_c < b_max)
            n_c = int(np.sum(mask_c))
            if n_c > 0:
                acc_c = float(np.mean(y_true[mask_c]))
                avg_p_c = float(np.mean(prob_c[mask_c]))
                out["champion"][bin_name] = {
                    "count": n_c,
                    "actual_accuracy": acc_c,
                    "avg_probability": avg_p_c,
                    "calibration_gap": acc_c - avg_p_c
                }

            # Challenger
            mask_ch = (prob_ch >= b_min) & (prob_ch < b_max)
            n_ch = int(np.sum(mask_ch))
            if n_ch > 0:
                acc_ch = float(np.mean(y_true[mask_ch]))
                avg_p_ch = float(np.mean(prob_ch[mask_ch]))
                out["challenger"][bin_name] = {
                    "count": n_ch,
                    "actual_accuracy": acc_ch,
                    "avg_probability": avg_p_ch,
                    "calibration_gap": acc_ch - avg_p_ch
                }

        return out


comparison_engine = ComparisonEngine()
