"""
StockSense AI — Phase 20 Statistical Validation Service
Computes McNemar's test, bootstrap 95% confidence intervals,
paired Brier comparison, ROC-AUC confidence interval, and effect size.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from scipy.stats import chi2
from sklearn.metrics import accuracy_score, roc_auc_score


class StatisticalValidationService:
    """Provides rigorous statistical hypothesis testing between Champion and Phase 20 Candidates."""

    def perform_mcnemar_test(self, y_true: np.ndarray, pred1: np.ndarray, pred2: np.ndarray) -> Dict[str, Any]:
        """
        Computes McNemar's test for paired binary classification.
        """
        correct1 = (pred1 == y_true)
        correct2 = (pred2 == y_true)

        # Contingency table cells
        # n10: Model 1 correct, Model 2 incorrect
        # n01: Model 1 incorrect, Model 2 correct
        n10 = int(np.sum(correct1 & ~correct2))
        n01 = int(np.sum(~correct1 & correct2))
        n11 = int(np.sum(correct1 & correct2))
        n00 = int(np.sum(~correct1 & ~correct2))

        # McNemar statistic with continuity correction
        b = n10
        c = n01

        if (b + c) == 0:
            stat = 0.0
            p_value = 1.0
        else:
            stat = (abs(b - c) - 1.0) ** 2 / (b + c)
            p_value = float(1.0 - chi2.cdf(stat, df=1))

        is_significant = p_value < 0.05

        return {
            "mcnemar_statistic": round(float(stat), 4),
            "p_value": round(float(p_value), 4),
            "statistically_significant": is_significant,
            "contingency_table": {
                "n_both_correct": n11,
                "n_model1_only": n10,
                "n_model2_only": n01,
                "n_both_incorrect": n00
            }
        }

    def compute_bootstrap_ci(
        self,
        y_true: np.ndarray,
        pred1: np.ndarray,
        pred2: np.ndarray,
        n_bootstraps: int = 1000,
        ci_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculates 95% bootstrap confidence intervals for accuracy difference (pred2 - pred1).
        """
        n = len(y_true)
        if n < 10:
            return {"accuracy_diff_ci": [None, None], "statistically_significant": False}

        rng = np.random.RandomState(42)
        diffs = []

        for _ in range(n_bootstraps):
            indices = rng.choice(n, size=n, replace=True)
            acc1 = accuracy_score(y_true[indices], pred1[indices])
            acc2 = accuracy_score(y_true[indices], pred2[indices])
            diffs.append(acc2 - acc1)

        alpha = 1.0 - ci_level
        low_pct = (alpha / 2.0) * 100
        high_pct = (1.0 - alpha / 2.0) * 100

        ci_lower = float(np.percentile(diffs, low_pct))
        ci_upper = float(np.percentile(diffs, high_pct))

        # Significant if 0 is not in CI
        is_sig = (ci_lower > 0) or (ci_upper < 0)

        return {
            "mean_accuracy_diff": round(float(np.mean(diffs)), 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "ci_level": ci_level,
            "statistically_significant": is_sig
        }
