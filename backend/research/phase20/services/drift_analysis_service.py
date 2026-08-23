"""
StockSense AI — Phase 20 Concept Drift Analysis Service
Calculates Population Stability Index (PSI), Kolmogorov-Smirnov (KS) test,
Wasserstein distance, mean shift, and variance shift across historical train,
historical holdout, and Phase 18/19 forward datasets.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy.stats import ks_2samp, wasserstein_distance


def calculate_psi(reference: np.ndarray, current: np.ndarray, num_bins: int = 10) -> float:
    """Calculates Population Stability Index (PSI) between reference and current distribution."""
    ref_clean = reference[~np.isnan(reference)]
    cur_clean = current[~np.isnan(current)]

    if len(ref_clean) < 10 or len(cur_clean) < 10:
        return 0.0

    percentiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(ref_clean, percentiles)
    bins[0] = -np.inf
    bins[-1] = np.inf
    bins = np.unique(bins)

    ref_counts, _ = np.histogram(ref_clean, bins=bins)
    cur_counts, _ = np.histogram(cur_clean, bins=bins)

    ref_pct = ref_counts / len(ref_clean)
    cur_pct = cur_counts / len(cur_clean)

    # Avoid division by zero
    ref_pct = np.where(ref_pct == 0, 1e-4, ref_pct)
    cur_pct = np.where(cur_pct == 0, 1e-4, cur_pct)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return float(psi)


class DriftAnalysisService:
    """Measures feature, target, probability, and regime drift across datasets."""

    def analyze_distribution_drift(
        self,
        ref_df: pd.DataFrame,
        cur_df: pd.DataFrame,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Computes PSI, KS statistic, and Wasserstein distance for feature set between ref and cur.
        """
        feature_drift = {}
        high_drift_count = 0

        for col in feature_columns:
            if col not in ref_df.columns or col not in cur_df.columns:
                continue

            ref_vals = ref_df[col].dropna().values
            cur_vals = cur_df[col].dropna().values

            if len(ref_vals) < 10 or len(cur_vals) < 10:
                continue

            psi_val = calculate_psi(ref_vals, cur_vals)
            ks_stat, ks_pvalue = ks_2samp(ref_vals, cur_vals)
            w_dist = float(wasserstein_distance(ref_vals, cur_vals))

            mean_shift = float(abs(np.mean(cur_vals) - np.mean(ref_vals)))
            var_shift = float(abs(np.var(cur_vals) - np.var(ref_vals)))

            if psi_val >= 0.25 or ks_pvalue < 0.01:
                status = "HIGH_DRIFT"
                high_drift_count += 1
            elif psi_val >= 0.10:
                status = "MODERATE_DRIFT"
            else:
                status = "STABLE"

            feature_drift[col] = {
                "psi": round(psi_val, 4),
                "ks_statistic": round(float(ks_stat), 4),
                "ks_pvalue": round(float(ks_pvalue), 4),
                "wasserstein_distance": round(w_dist, 4),
                "mean_shift": round(mean_shift, 4),
                "variance_shift": round(var_shift, 4),
                "status": status
            }

        overall_status = "DRIFT_DETECTED" if high_drift_count > (len(feature_columns) * 0.2) else "NORMAL"

        return {
            "overall_drift_status": overall_status,
            "total_features_analyzed": len(feature_drift),
            "high_drift_features": high_drift_count,
            "feature_drift_details": feature_drift
        }
