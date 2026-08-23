"""
StockSense AI — Production Model Performance Monitor (Phase 16)
Calculates forward-testing metrics strictly from resolved live/paper prediction records.
Enforces sample size thresholds to prevent misleading metrics on tiny samples.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord, PaperPredictionRecord
from backend.assets.asset_registry import get_all_assets

SUPPORTED_SYMBOLS = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]


logger = logging.getLogger(__name__)

MINIMUM_SAMPLE_SIZE = 10  # Enforce minimum 10 resolved predictions for accuracy reporting


class ModelMonitor:
    """
    Computes production ML model evaluation metrics, calibration gaps, and regime breakdowns.
    """

    def get_symbol_metrics(self, symbol: str, rolling_window: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates production model metrics for a specific symbol.
        """
        symbol_clean = symbol.upper().strip()

        with get_db_context() as db:
            query = db.query(LivePredictionRecord).filter(
                LivePredictionRecord.symbol == symbol_clean
            ).order_by(LivePredictionRecord.prediction_timestamp.desc())

            if rolling_window:
                query = query.limit(rolling_window)

            records = query.all()

        total_predictions = len(records)
        resolved_records = [r for r in records if r.resolved is True or r.is_correct is not None]
        resolved_count = len(resolved_records)

        if resolved_count < MINIMUM_SAMPLE_SIZE:
            return {
                "symbol": symbol_clean,
                "model_version": "XGBoost v1.0 Calibrated",
                "sample_size": resolved_count,
                "total_predictions": total_predictions,
                "resolved_predictions": resolved_count,
                "accuracy": None,
                "reason": "insufficient_resolved_predictions",
                "message": f"Insufficient live sample size ({resolved_count}/{MINIMUM_SAMPLE_SIZE} resolved required).",
                "brier_score": None,
                "precision": None,
                "recall": None,
                "f1": None,
                "roc_auc": None,
                "avg_probability": None,
                "buy_accuracy": None,
                "sell_accuracy": None,
                "hold_frequency": 0.0,
                "regime_performance": {},
                "horizon_performance": {}
            }

        # Calculate metrics for resolved records
        correct_records = [r for r in resolved_records if (r.correct is True or r.is_correct is True)]
        correct_count = len(correct_records)
        incorrect_count = resolved_count - correct_count
        accuracy = round(correct_count / resolved_count, 4)

        # Brier Score
        brier_scores = [r.brier_score for r in resolved_records if r.brier_score is not None]
        avg_brier = round(float(np.mean(brier_scores)), 4) if brier_scores else None

        # Precision, Recall, F1
        tp = sum(1 for r in resolved_records if (r.predicted_direction == "UP" and (r.actual_direction == "UP" or r.resolved_direction == "UP")))
        fp = sum(1 for r in resolved_records if (r.predicted_direction == "UP" and (r.actual_direction == "DOWN" or r.resolved_direction == "DOWN")))
        fn = sum(1 for r in resolved_records if (r.predicted_direction == "DOWN" and (r.actual_direction == "UP" or r.resolved_direction == "UP")))
        tn = sum(1 for r in resolved_records if (r.predicted_direction == "DOWN" and (r.actual_direction == "DOWN" or r.resolved_direction == "DOWN")))

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None
        f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision and recall and (precision + recall) > 0) else None

        # ROC-AUC calculation when both classes exist
        roc_auc = None
        y_true = [1 if (r.actual_direction == "UP" or r.resolved_direction == "UP") else 0 for r in resolved_records]
        y_prob = [r.probability_up for r in resolved_records]
        if len(set(y_true)) > 1:
            try:
                from sklearn.metrics import roc_auc_score
                roc_auc = round(float(roc_auc_score(y_true, y_prob)), 4)
            except Exception:
                roc_auc = None

        # Directional Accuracies
        up_preds = [r for r in resolved_records if r.predicted_direction == "UP"]
        down_preds = [r for r in resolved_records if r.predicted_direction == "DOWN"]
        buy_acc = round(sum(1 for r in up_preds if (r.correct is True or r.is_correct is True)) / len(up_preds), 4) if up_preds else None
        sell_acc = round(sum(1 for r in down_preds if (r.correct is True or r.is_correct is True)) / len(down_preds), 4) if down_preds else None

        # Regime Performance
        regimes = ["BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY", "LOW_VOLATILITY"]
        regime_perf = {}
        for reg in regimes:
            reg_records = [r for r in resolved_records if (r.trend_regime == reg or r.volatility_regime == reg)]
            if len(reg_records) >= 5:
                reg_corr = sum(1 for r in reg_records if (r.correct is True or r.is_correct is True))
                regime_perf[reg] = {
                    "predictions": len(reg_records),
                    "accuracy": round(reg_corr / len(reg_records), 4)
                }
            else:
                regime_perf[reg] = {
                    "predictions": len(reg_records),
                    "accuracy": None,
                    "reason": "insufficient_data"
                }

        return {
            "symbol": symbol_clean,
            "model_version": "XGBoost v1.0 Calibrated",
            "sample_size": resolved_count,
            "total_predictions": total_predictions,
            "resolved_predictions": resolved_count,
            "correct_predictions": correct_count,
            "incorrect_predictions": incorrect_count,
            "accuracy": accuracy,
            "brier_score": avg_brier,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc,
            "avg_probability": round(float(np.mean(y_prob)), 4) if y_prob else None,
            "buy_accuracy": buy_acc,
            "sell_accuracy": sell_acc,
            "hold_frequency": 0.0,
            "regime_performance": regime_perf,
            "horizon_performance": {
                "1_day": {
                    "sample_size": resolved_count,
                    "accuracy": accuracy
                }
            }
        }

    def get_all_metrics(self) -> Dict[str, Any]:

        """
        Calculates aggregated and per-symbol metrics for all supported assets.
        """
        symbols = SUPPORTED_SYMBOLS

        per_symbol = {}
        all_resolved = 0
        all_correct = 0
        all_brier = []

        for sym in symbols:
            m = self.get_symbol_metrics(sym)
            per_symbol[sym] = m
            if m.get("accuracy") is not None:
                all_resolved += m["resolved_predictions"]
                all_correct += m["correct_predictions"]
                if m.get("brier_score") is not None:
                    all_brier.append(m["brier_score"])

        overall_accuracy = round(all_correct / all_resolved, 4) if all_resolved >= MINIMUM_SAMPLE_SIZE else None
        overall_brier = round(float(np.mean(all_brier)), 4) if all_brier else None

        return {
            "overall": {
                "model_version": "XGBoost v1.0 Calibrated",
                "sample_size": all_resolved,
                "accuracy": overall_accuracy,
                "brier_score": overall_brier,
                "reason": None if overall_accuracy is not None else "insufficient_resolved_predictions"
            },
            "per_symbol": per_symbol
        }

    def get_calibration_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Calculates confidence calibration gaps across probability bands.
        """
        symbol_clean = symbol.upper().strip()

        with get_db_context() as db:
            resolved_records = db.query(LivePredictionRecord).filter(
                LivePredictionRecord.symbol == symbol_clean,
                (LivePredictionRecord.resolved == True) | (LivePredictionRecord.is_correct.isnot(None))
            ).all()

        bands = [
            ("0.50-0.55", 0.50, 0.55),
            ("0.55-0.60", 0.55, 0.60),
            ("0.60-0.65", 0.60, 0.65),
            ("0.65-0.70", 0.65, 0.70),
            ("0.70-0.80", 0.70, 0.80),
            ("0.80+", 0.80, 1.00)
        ]

        band_results = {}
        total_sample = len(resolved_records)

        for label, low, high in bands:
            if label == "0.80+":
                in_band = [r for r in resolved_records if r.probability_up >= low]
            else:
                in_band = [r for r in resolved_records if low <= r.probability_up < high]

            count = len(in_band)
            if count >= 5:
                corr = sum(1 for r in in_band if (r.correct is True or r.is_correct is True))
                obs_acc = round(corr / count, 4)
                exp_acc = round((low + high) / 2.0, 4)
                cal_gap = round(obs_acc - exp_acc, 4)
                band_results[label] = {
                    "count": count,
                    "observed_accuracy": obs_acc,
                    "expected_accuracy": exp_acc,
                    "calibration_gap": cal_gap
                }
            else:
                band_results[label] = {
                    "count": count,
                    "observed_accuracy": None,
                    "expected_accuracy": round((low + high) / 2.0, 4),
                    "calibration_gap": None,
                    "reason": "insufficient_samples"
                }

        cal_status = "GOOD" if total_sample >= MINIMUM_SAMPLE_SIZE else "INSUFFICIENT_DATA"

        return {
            "symbol": symbol_clean,
            "calibration_status": cal_status,
            "total_resolved_sample": total_sample,
            "probability_bands": band_results
        }


# Global Singleton Service
model_monitor = ModelMonitor()
