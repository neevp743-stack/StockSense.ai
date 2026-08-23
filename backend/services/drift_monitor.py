"""
StockSense AI — Model Drift Monitor (Phase 16)
Monitors prediction probability distributions, regime shifts, and feature stability.
Calculates Population Stability Index (PSI) and distribution metrics.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord

logger = logging.getLogger(__name__)


def calculate_psi(reference: List[float], current: List[float], num_bins: int = 5) -> float:
    """
    Calculates Population Stability Index (PSI) between reference and current samples.
    """
    if not reference or not current or len(reference) < 5 or len(current) < 5:
        return 0.0

    bins = np.linspace(0.0, 1.0, num_bins + 1)
    ref_counts, _ = np.histogram(reference, bins=bins)
    curr_counts, _ = np.histogram(current, bins=bins)

    ref_pct = ref_counts / len(reference)
    curr_pct = curr_counts / len(current)

    psi_val = 0.0
    for r, c in zip(ref_pct, curr_pct):
        r_safe = max(r, 0.001)
        c_safe = max(c, 0.001)
        psi_val += (c_safe - r_safe) * np.log(c_safe / r_safe)

    return float(np.round(psi_val, 4))


class DriftMonitor:
    """
    Monitors probability distribution drift, direction ratio shifts, and regime drift.
    """

    def analyze_drift(self, symbol: str) -> Dict[str, Any]:
        """
        Calculates drift metrics comparing recent prediction window vs historical baseline window.
        """
        symbol_clean = symbol.upper().strip()

        with get_db_context() as db:
            records = db.query(LivePredictionRecord).filter(
                LivePredictionRecord.symbol == symbol_clean
            ).order_by(LivePredictionRecord.prediction_timestamp.desc()).all()

        if len(records) < 10:
            return {
                "symbol": symbol_clean,
                "status": "NORMAL",
                "sample_size": len(records),
                "psi_score": 0.0,
                "probability_drift": {
                    "psi": 0.0,
                    "ref_mean": 0.50,
                    "curr_mean": 0.50
                },
                "direction_distribution": {
                    "up_pct": 50.0,
                    "down_pct": 50.0
                },
                "evidence": "Insufficient live prediction history to detect statistical drift (<10 samples)."
            }

        probs = [r.probability_up for r in records]
        half = len(probs) // 2
        curr_probs = probs[:half]
        ref_probs = probs[half:]

        psi_score = calculate_psi(ref_probs, curr_probs)
        ref_mean = round(float(np.mean(ref_probs)), 4)
        curr_mean = round(float(np.mean(curr_probs)), 4)
        mean_shift = round(abs(curr_mean - ref_mean), 4)

        # Direction Ratio
        up_count = sum(1 for r in records if r.predicted_direction == "UP")
        up_pct = round((up_count / len(records)) * 100.0, 2)
        down_pct = round(100.0 - up_pct, 2)

        # Classify Status based on PSI and Mean Shift
        if psi_score > 0.25 or mean_shift > 0.15:
            status = "DRIFT_DETECTED"
            evidence = f"Significant probability distribution drift detected (PSI={psi_score}, Mean Shift={mean_shift})."
        elif psi_score > 0.10 or mean_shift > 0.08:
            status = "WATCH"
            evidence = f"Moderate distribution shift observed (PSI={psi_score}, Mean Shift={mean_shift}). Monitoring required."
        else:
            status = "NORMAL"
            evidence = f"Distribution stable (PSI={psi_score}, Mean Shift={mean_shift})."

        return {
            "symbol": symbol_clean,
            "status": status,
            "sample_size": len(records),
            "psi_score": psi_score,
            "probability_drift": {
                "psi": psi_score,
                "ref_mean": ref_mean,
                "curr_mean": curr_mean,
                "mean_shift": mean_shift
            },
            "direction_distribution": {
                "up_pct": up_pct,
                "down_pct": down_pct
            },
            "evidence": evidence
        }


# Global Singleton Service
drift_monitor = DriftMonitor()
