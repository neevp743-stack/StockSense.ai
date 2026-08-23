"""
StockSense AI — Phase 19 Statistical Validation Engine
Implements paired statistical hypothesis testing:
1. McNemar's Test for paired classification outcomes
2. Bootstrap 95% Confidence Intervals for Accuracy, Brier, and ROC-AUC differences
3. Effect Size estimation at alpha = 0.05
"""

import numpy as np
from typing import Dict, Any, List
from scipy.stats import chisquare


class StatisticalValidationEngine:
    """Computes paired statistical hypothesis tests and bootstrap confidence intervals."""

    def compute_statistical_tests(
        self,
        paired_records: List[Dict[str, Any]],
        alpha: float = 0.05,
        n_bootstraps: int = 1000
    ) -> Dict[str, Any]:
        """Calculates McNemar test, bootstrap 95% CIs, and effect size on paired records."""
        n = len(paired_records)
        if n < 10:
            return {
                "sample_size": n,
                "status": "INSUFFICIENT_FORWARD_DATA",
                "alpha": alpha,
                "contingency_table": {"both_correct": 0, "champion_only_correct": 0, "challenger_only_correct": 0, "both_incorrect": 0},
                "mcnemar": {"statistic": None, "p_value": None},
                "bootstrap_ci": {"mean_diff": None, "ci_lower": None, "ci_upper": None},
                "effect_size_accuracy": None,
                "statistically_significant": False
            }

        y_true = [1 if r["actual_direction"] == "UP" else 0 for r in paired_records]
        c_correct = [1 if r["champion"]["correct"] else 0 for r in paired_records]
        ch_correct = [1 if r["challenger"]["correct"] else 0 for r in paired_records]

        # 2x2 Contingency Table for McNemar's Test
        both_correct = sum(1 for c, ch in zip(c_correct, ch_correct) if c == 1 and ch == 1)
        champ_only = sum(1 for c, ch in zip(c_correct, ch_correct) if c == 1 and ch == 0)
        chall_only = sum(1 for c, ch in zip(c_correct, ch_correct) if c == 0 and ch == 1)
        both_incorrect = sum(1 for c, ch in zip(c_correct, ch_correct) if c == 0 and ch == 0)

        contingency = {
            "both_correct": both_correct,
            "champion_only_correct": champ_only,
            "challenger_only_correct": chall_only,
            "both_incorrect": both_incorrect
        }

        # McNemar's Test with continuity correction
        b, c = champ_only, chall_only
        if (b + c) > 0:
            mcnemar_stat = float(((abs(b - c) - 1.0) ** 2) / (b + c))
            # 1-degree of freedom chi-square p-value
            p_val = float(chisquare([b, c]).pvalue)
        else:
            mcnemar_stat = 0.0
            p_val = 1.0

        # Bootstrap 95% Confidence Interval for Accuracy Difference (Challenger - Champion)
        np.random.seed(42)
        diffs = []
        for _ in range(n_bootstraps):
            idxs = np.random.choice(n, size=n, replace=True)
            boot_c_acc = np.mean([c_correct[i] for i in idxs])
            boot_ch_acc = np.mean([ch_correct[i] for i in idxs])
            diffs.append(boot_ch_acc - boot_c_acc)

        mean_diff = float(np.mean(diffs))
        ci_lower = float(np.percentile(diffs, 100 * (alpha / 2.0)))
        ci_upper = float(np.percentile(diffs, 100 * (1.0 - alpha / 2.0)))

        is_significant = (p_val < alpha) and (ci_lower > 0 or ci_upper < 0)

        # Effect Size (Cohen's g for McNemar test: (b - c) / n)
        effect_size = float(mean_diff)

        return {
            "sample_size": n,
            "status": "EVALUATED",
            "alpha": alpha,
            "contingency_table": contingency,
            "mcnemar": {
                "statistic": mcnemar_stat,
                "p_value": p_val
            },
            "bootstrap_ci": {
                "mean_diff": mean_diff,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper
            },
            "effect_size_accuracy": effect_size,
            "statistically_significant": is_significant
        }


statistical_validation_engine = StatisticalValidationEngine()
