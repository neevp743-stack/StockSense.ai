"""
StockSense AI — Phase 19 Promotion Readiness & Scorecard Engine
Evaluates 12 conservative promotion criteria across sample size, accuracy, ROC-AUC, Brier score,
calibration, statistical significance, asset consistency, regime consistency, rolling stability,
Phase 14 trade performance, and data quality audit.

HARD-DISABLES AUTOMATIC PROMOTION.
Returns one of:
1. PHASE19_INSUFFICIENT_FORWARD_DATA
2. PHASE19_CHALLENGER_REJECTED
3. PHASE19_CHALLENGER_INCONCLUSIVE
4. PHASE19_CHALLENGER_READY_FOR_EXPERT_REVIEW
"""

from typing import Dict, Any, List


class PromotionReadinessEngine:
    """Evaluates the 12-point promotion readiness scorecard."""

    MIN_PROMOTION_SAMPLE = 100

    def evaluate_promotion_readiness(
        self,
        audit_report: Dict[str, Any],
        cumulative_res: Dict[str, Any],
        rolling_res: Dict[str, Any],
        asset_group_res: Dict[str, Any],
        regime_res: Dict[str, Any],
        calibration_res: Dict[str, Any],
        trade_res: Dict[str, Any],
        stat_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Runs the 12-point promotion scorecard and determines final verdict."""

        sample_size = cumulative_res.get("total_observations", 0)
        summary = cumulative_res.get("cumulative_summary", {})
        c_m = summary.get("champion", {})
        ch_m = summary.get("challenger", {})
        comp = summary.get("comparison", {})

        # Scorecard item evaluation
        scorecard = {}

        # 1. Forward Sample Size >= 100
        scorecard["forward_sample_size_ge_100"] = {
            "name": "Forward Sample Size (N >= 100)",
            "status": "PASSED" if sample_size >= self.MIN_PROMOTION_SAMPLE else "INSUFFICIENT",
            "details": f"N = {sample_size} (Threshold = {self.MIN_PROMOTION_SAMPLE})"
        }

        # 2. Overall Accuracy Superior
        acc_delta = comp.get("accuracy_delta")
        scorecard["overall_accuracy_superior"] = {
            "name": "Overall Forward Accuracy Superior",
            "status": "PASSED" if (acc_delta is not None and acc_delta > 0) else ("FAILED" if acc_delta is not None and acc_delta < 0 else "INSUFFICIENT"),
            "details": f"Delta = {acc_delta:.4f}" if acc_delta is not None else "Insufficient sample"
        }

        # 3. ROC-AUC Superior
        auc_delta = comp.get("roc_auc_delta")
        scorecard["roc_auc_superior"] = {
            "name": "Overall ROC-AUC Superior",
            "status": "PASSED" if (auc_delta is not None and auc_delta > 0) else ("FAILED" if auc_delta is not None and auc_delta < 0 else "INSUFFICIENT"),
            "details": f"Delta = {auc_delta:.4f}" if auc_delta is not None else "Insufficient sample"
        }

        # 4. Brier Score Superior (Lower is better)
        brier_delta = comp.get("brier_delta")
        scorecard["brier_score_superior"] = {
            "name": "Brier Calibration Loss Superior (Lower)",
            "status": "PASSED" if (brier_delta is not None and brier_delta < 0) else ("FAILED" if brier_delta is not None and brier_delta > 0 else "INSUFFICIENT"),
            "details": f"Delta = {brier_delta:.4f}" if brier_delta is not None else "Insufficient sample"
        }

        # 5. ECE Calibration Superior (Lower is better)
        ece_comp = calibration_res.get("comparison", {})
        ece_delta = ece_comp.get("ece_delta")
        scorecard["calibration_ece_superior"] = {
            "name": "Expected Calibration Error (ECE) Superior",
            "status": "PASSED" if (ece_delta is not None and ece_delta < 0) else ("FAILED" if ece_delta is not None and ece_delta > 0 else "INSUFFICIENT"),
            "details": f"ECE Delta = {ece_delta:.4f}" if ece_delta is not None else "Insufficient sample"
        }

        # 6. Statistical Significance
        stat_sig = stat_res.get("statistically_significant", False)
        p_val = stat_res.get("mcnemar", {}).get("p_value")
        scorecard["statistical_significance"] = {
            "name": "McNemar Statistical Significance (p < 0.05)",
            "status": "PASSED" if stat_sig else ("FAILED" if sample_size >= 50 else "INSUFFICIENT"),
            "details": f"p-value = {p_val:.4f}" if p_val is not None else "Insufficient sample"
        }

        # 7. Asset Group Consistency (India, USA, Crypto)
        group_pass = True
        group_details = []
        for g_key in ["INDIA", "USA", "CRYPTO"]:
            g_info = asset_group_res.get(g_key, {}).get("comparison", {})
            g_delta = g_info.get("accuracy_delta")
            if g_delta is None or g_delta < 0:
                group_pass = False
            group_details.append(f"{g_key}: {g_delta if g_delta is not None else 'null'}")

        scorecard["asset_group_consistency"] = {
            "name": "Asset Group Consistency (India, USA, Crypto)",
            "status": "PASSED" if (group_pass and sample_size >= 30) else ("FAILED" if sample_size >= 30 and not group_pass else "INSUFFICIENT"),
            "details": ", ".join(group_details)
        }

        # 8. Regime Consistency (BULL, BEAR, SIDEWAYS)
        reg_pass = True
        reg_details = []
        for r_key in ["BULL", "BEAR", "SIDEWAYS"]:
            r_info = regime_res.get(r_key, {}).get("comparison", {})
            r_delta = r_info.get("accuracy_delta")
            if r_delta is None or r_delta < 0:
                reg_pass = False
            reg_details.append(f"{r_key}: {r_delta if r_delta is not None else 'null'}")

        scorecard["regime_consistency"] = {
            "name": "Market Regime Consistency (BULL, BEAR, SIDEWAYS)",
            "status": "PASSED" if (reg_pass and sample_size >= 30) else ("FAILED" if sample_size >= 30 and not reg_pass else "INSUFFICIENT"),
            "details": ", ".join(reg_details)
        }

        # 9. Rolling Window Consistency
        roll_pass = True
        for w_key in ["window_20", "window_50", "window_100", "window_250"]:
            w_delta = rolling_res.get(w_key, {}).get("comparison", {}).get("accuracy_delta")
            if w_delta is not None and w_delta < 0:
                roll_pass = False
                break

        scorecard["rolling_window_consistency"] = {
            "name": "Rolling Window Consistency",
            "status": "PASSED" if roll_pass and sample_size >= 20 else "FAILED"
        }

        # 10. Phase 14 Trade Profitability
        trade_comp = trade_res.get("comparison", {})
        pf_delta = trade_comp.get("profit_factor_delta")
        scorecard["phase14_trade_profitability"] = {
            "name": "Phase 14 Trade Setup Profit Factor",
            "status": "PASSED" if (pf_delta is not None and pf_delta > 0) else ("FAILED" if pf_delta is not None and pf_delta < 0 else "INSUFFICIENT"),
            "details": f"PF Delta = {pf_delta:.4f}" if pf_delta is not None else "Insufficient trades"
        }

        # 11. Recent Performance Stability
        ts = cumulative_res.get("time_series", [])
        if len(ts) >= 10:
            early_acc = ts[len(ts)//2].get("challenger_accuracy") or 0.0
            recent_acc = ts[-1].get("challenger_accuracy") or 0.0
            recent_pass = recent_acc >= (early_acc - 0.05)
        else:
            recent_pass = True

        scorecard["recent_performance_stability"] = {
            "name": "Recent Performance Stability",
            "status": "PASSED" if recent_pass else "FAILED"
        }

        # 12. Data Quality Audit
        audit_pass = audit_report.get("audit_status") == "PASSED" and audit_report.get("synthetic_records_excluded", 0) >= 0
        scorecard["data_quality_audit"] = {
            "name": "17-Point Data Eligibility Audit",
            "status": "PASSED" if audit_pass else "FAILED",
            "details": f"Eligible = {audit_report.get('eligible_records', 0)}, Synthetic Excluded = {audit_report.get('synthetic_records_excluded', 0)}"
        }

        # Determine Final Verdict
        if sample_size < self.MIN_PROMOTION_SAMPLE:
            verdict = "PHASE19_INSUFFICIENT_FORWARD_DATA"
            explanation = f"Insufficient genuine forward observations (N = {sample_size} < {self.MIN_PROMOTION_SAMPLE}). Phase 12 remains production."
        else:
            passed_count = sum(1 for item in scorecard.values() if item["status"] == "PASSED")
            failed_count = sum(1 for item in scorecard.values() if item["status"] == "FAILED")

            if failed_count >= 5 or (acc_delta is not None and acc_delta < -0.05):
                verdict = "PHASE19_CHALLENGER_REJECTED"
                explanation = "Phase 17 challenger failed forward validation criteria. Phase 12 remains production."
            elif not stat_sig or not group_pass or not reg_pass:
                verdict = "PHASE19_CHALLENGER_INCONCLUSIVE"
                explanation = "Forward evidence is mixed across assets or market regimes. Phase 12 remains production."
            elif passed_count >= 10 and stat_sig:
                verdict = "PHASE19_CHALLENGER_READY_FOR_EXPERT_REVIEW"
                explanation = "Phase 17 demonstrates sufficient forward evidence for HUMAN EXPERT REVIEW. Phase 12 remains production until an explicit human-approved migration."
            else:
                verdict = "PHASE19_CHALLENGER_INCONCLUSIVE"
                explanation = "Forward evidence is inconclusive. Phase 12 remains production."

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "promotion_policy": "NOT_AUTOMATIC",
            "sample_size": sample_size,
            "min_required_sample": self.MIN_PROMOTION_SAMPLE,
            "scorecard": scorecard,
            "final_verdict": verdict,
            "verdict_explanation": explanation
        }


promotion_readiness_engine = PromotionReadinessEngine()
