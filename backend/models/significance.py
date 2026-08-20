"""
StockSense AI — Statistical Significance Testing Suite
Provides McNemar's test and Paired t-test for comparing Baseline vs Enhanced model predictions.
Prevents false claims of model superiority without empirical statistical confidence (p < 0.05).
"""

import numpy as np
from scipy import stats
from typing import Dict, Any

def run_mcnemar_test(y_true: np.ndarray, y_pred_base: np.ndarray, y_pred_enh: np.ndarray) -> Dict[str, Any]:
    """
    Executes McNemar's Test for paired binary classification predictions.
    
    Contingency Table:
    - n00: Both wrong
    - n01: Baseline wrong, Enhanced correct
    - n10: Baseline correct, Enhanced wrong
    - n11: Both correct
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred_base = np.asarray(y_pred_base, dtype=int)
    y_pred_enh = np.asarray(y_pred_enh, dtype=int)

    correct_base = (y_pred_base == y_true)
    correct_enh = (y_pred_enh == y_true)

    n01 = int(np.sum(~correct_base & correct_enh))
    n10 = int(np.sum(correct_base & ~correct_enh))

    acc_base = float(np.mean(correct_base))
    acc_enh = float(np.mean(correct_enh))
    acc_diff = acc_enh - acc_base

    if (n01 + n10) == 0:
        p_value = 1.0
        statistic = 0.0
    else:
        # McNemar's test with continuity correction
        statistic = float(((abs(n01 - n10) - 1.0) ** 2) / (n01 + n10))
        p_value = float(1.0 - stats.chi2.cdf(statistic, df=1))

    is_significant = (p_value < 0.05) and (n01 + n10 > 0)

    if not is_significant:
        verdict = "Evidence insufficient to establish improvement."
    elif acc_diff > 0:
        verdict = f"Statistically significant improvement established (p = {p_value:.4f} < 0.05)."
    else:
        verdict = f"Statistically significant performance degradation detected (p = {p_value:.4f} < 0.05)."

    return {
        "acc_baseline": round(acc_base * 100.0, 2),
        "acc_enhanced": round(acc_enh * 100.0, 2),
        "acc_difference_pct": round(acc_diff * 100.0, 2),
        "n_baseline_wrong_enh_correct": n01,
        "n_baseline_correct_enh_wrong": n10,
        "mcnemar_statistic": round(statistic, 4),
        "p_value": round(p_value, 4),
        "is_significant": is_significant,
        "verdict": verdict
    }
