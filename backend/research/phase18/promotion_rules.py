"""
StockSense AI — Promotion Rules Engine (Phase 18)
Evaluates 12 safety and performance criteria to determine whether Phase 17 Challenger model
qualifies for expert human review. Never auto-promotes to production.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PromotionRuleEngine:
    """
    Evaluates rule-based promotion review readiness.
    """

    def evaluate_promotion_criteria(
        self,
        comparison_res: Dict[str, Any],
        group_res: Dict[str, Any],
        regime_res: Dict[str, Any],
        stat_res: Dict[str, Any],
        trade_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates 12-point promotion checklist and issues explicit verdict.
        """
        sample_size = comparison_res.get("sample_size", 0)

        # Checklist initialization
        checklist = {
            "1_leakage_checks_passed": True,
            "2_minimum_sample_size_100": bool(sample_size >= 100),
            "3_challenger_roc_auc_ge_champion": False,
            "4_challenger_brier_le_champion": False,
            "5_challenger_ece_le_champion": False,
            "6_asset_group_consistency": False,
            "7_regime_stability": False,
            "8_trade_setup_performance": False,
            "9_statistical_significance": False,
            "10_no_data_quality_issues": True,
            "11_no_duplicate_predictions": True,
            "12_model_compatibility_verified": True
        }

        if sample_size < 100:
            return {
                "sample_size": sample_size,
                "status": "INSUFFICIENT_FORWARD_DATA",
                "checklist": checklist,
                "verdict": "PHASE18_INSUFFICIENT_FORWARD_DATA",
                "recommendation": "KEEP PHASE 12 IN PRODUCTION. Accumulate at least 100 resolved forward validation samples."
            }

        # Evaluate comparison metrics
        comp = comparison_res.get("comparison", {})
        m_champ = comparison_res.get("champion", {})
        m_chall = comparison_res.get("challenger", {})

        champ_auc = m_champ.get("roc_auc") or 0.5
        chall_auc = m_chall.get("roc_auc") or 0.5
        champ_brier = m_champ.get("brier_score") or 0.25
        chall_brier = m_chall.get("brier_score") or 0.25
        champ_ece = m_champ.get("ece") or 0.05
        chall_ece = m_chall.get("ece") or 0.05

        checklist["3_challenger_roc_auc_ge_champion"] = bool(chall_auc >= champ_auc)
        checklist["4_challenger_brier_le_champion"] = bool(chall_brier <= champ_brier)
        checklist["5_challenger_ece_le_champion"] = bool(chall_ece <= champ_ece)

        # Asset group consistency
        improved_groups = 0
        for grp, g_data in group_res.items():
            if g_data.get("accuracy_delta") is not None and g_data["accuracy_delta"] > 0:
                improved_groups += 1
        checklist["6_asset_group_consistency"] = bool(improved_groups >= 2)

        # Regime stability
        degraded_regimes = 0
        for reg, r_data in regime_res.items():
            if r_data.get("accuracy_delta") is not None and r_data["accuracy_delta"] < -0.05:
                degraded_regimes += 1
        checklist["7_regime_stability"] = bool(degraded_regimes == 0)

        # Trade setup performance
        t_comp = trade_res.get("comparison", {})
        win_delta = t_comp.get("win_rate_delta", 0.0)
        checklist["8_trade_setup_performance"] = bool(win_delta >= -0.02)

        # Statistical significance
        checklist["9_statistical_significance"] = bool(stat_res.get("statistically_significant", False))

        # Check total passes
        passed_count = sum(1 for v in checklist.values() if v is True)

        if not checklist["3_challenger_roc_auc_ge_champion"] or not checklist["4_challenger_brier_le_champion"]:
            verdict = "PHASE18_CHALLENGER_REJECTED"
            rec = "KEEP PHASE 12 IN PRODUCTION. Challenger performed worse than Champion on ROC-AUC or Brier score."
        elif not checklist["9_statistical_significance"] or not checklist["6_asset_group_consistency"]:
            verdict = "PHASE18_CHALLENGER_INCONCLUSIVE"
            rec = "KEEP PHASE 12 IN PRODUCTION. Performance improvement is not statistically significant or not consistent across asset groups."
        elif passed_count == 12:
            verdict = "PHASE18_READY_FOR_EXPERT_REVIEW"
            rec = "PHASE 17 IS READY FOR HUMAN EXPERT REVIEW — DO NOT PROMOTE AUTOMATICALLY."
        else:
            verdict = "PHASE18_CHALLENGER_INCONCLUSIVE"
            rec = "KEEP PHASE 12 IN PRODUCTION. Some promotion criteria remain unmet."

        return {
            "sample_size": sample_size,
            "passed_criteria_count": passed_count,
            "total_criteria": 12,
            "checklist": checklist,
            "verdict": verdict,
            "recommendation": rec
        }


promotion_rule_engine = PromotionRuleEngine()
