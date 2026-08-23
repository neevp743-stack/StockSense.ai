"""
StockSense AI — Statistical Tests Engine (Phase 18)
Implements McNemar's test for paired classification outcomes, bootstrap confidence intervals,
and effect size calculations at alpha = 0.05.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.stats import chi2

from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker

logger = logging.getLogger(__name__)


def run_mcnemar_test(b: int, c: int) -> Tuple[float, float]:
    """
    Runs McNemar's test with continuity correction.
    b: Champion correct & Challenger wrong
    c: Champion wrong & Challenger correct
    Returns (statistic, p_value)
    """
    if b + c == 0:
        return 0.0, 1.0

    stat = ((abs(b - c) - 1.0) ** 2) / (b + c)
    p_val = float(1.0 - chi2.cdf(stat, df=1))
    return float(stat), float(p_val)


def bootstrap_accuracy_difference(
    y_true: np.ndarray,
    y_pred_champ: np.ndarray,
    y_pred_chall: np.ndarray,
    n_bootstraps: int = 1000,
    alpha: float = 0.05
) -> Dict[str, float]:
    """Calculates bootstrap 95% confidence interval for accuracy difference (Challenger - Champion)."""
    n = len(y_true)
    if n == 0:
        return {"mean_diff": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

    np.random.seed(42)
    diffs = []
    for _ in range(n_bootstraps):
        idx = np.random.choice(n, size=n, replace=True)
        acc_champ = np.mean(y_true[idx] == y_pred_champ[idx])
        acc_chall = np.mean(y_true[idx] == y_pred_chall[idx])
        diffs.append(acc_chall - acc_champ)

    diffs = np.array(diffs)
    mean_diff = float(np.mean(diffs))
    lower_pct = (alpha / 2.0) * 100.0
    upper_pct = (1.0 - alpha / 2.0) * 100.0

    ci_lower = float(np.percentile(diffs, lower_pct))
    ci_upper = float(np.percentile(diffs, upper_pct))

    return {
        "mean_diff": mean_diff,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper
    }


class StatisticalTestEngine:
    """
    Evaluates statistical significance of Champion vs Challenger performance differences.
    """

    def analyze_statistical_significance(self, alpha: float = 0.05) -> Dict[str, Any]:
        """
        Runs McNemar's test and bootstrap confidence intervals on all resolved paired shadow observations.
        """
        pairs = shadow_prediction_tracker.get_paired_records(resolved_only=True)
        n = len(pairs)

        if n < 10:
            return {
                "sample_size": n,
                "status": "INSUFFICIENT_DATA",
                "reason": "insufficient_forward_validation_data",
                "p_value": None,
                "statistically_significant": False
            }

        y_true = np.array([1 if p[0].actual_direction == "UP" else 0 for p in pairs])
        y_c = np.array([1 if p[0].predicted_direction == "UP" else 0 for p in pairs])
        y_ch = np.array([1 if p[1].predicted_direction == "UP" else 0 for p in pairs])

        correct_c = (y_c == y_true)
        correct_ch = (y_ch == y_true)

        # McNemar contingency table cells
        a = int(np.sum(correct_c & correct_ch))        # Both right
        b = int(np.sum(correct_c & (~correct_ch)))     # Champion right, Challenger wrong
        c_cell = int(np.sum((~correct_c) & correct_ch))# Champion wrong, Challenger right
        d = int(np.sum((~correct_c) & (~correct_ch)))  # Both wrong

        mc_stat, p_val = run_mcnemar_test(b, c_cell)
        boot_ci = bootstrap_accuracy_difference(y_true, y_c, y_ch, n_bootstraps=1000, alpha=alpha)

        is_sig = bool(p_val < alpha and boot_ci["ci_lower"] > 0)

        return {
            "sample_size": n,
            "status": "EVALUATED",
            "alpha": alpha,
            "contingency_table": {
                "both_correct": a,
                "champion_only_correct": b,
                "challenger_only_correct": c_cell,
                "both_incorrect": d
            },
            "mcnemar": {
                "statistic": mc_stat,
                "p_value": p_val
            },
            "bootstrap_ci": boot_ci,
            "effect_size_accuracy": boot_ci["mean_diff"],
            "statistically_significant": is_sig
        }


statistical_test_engine = StatisticalTestEngine()
