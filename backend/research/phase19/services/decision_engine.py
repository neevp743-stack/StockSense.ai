"""
StockSense AI — Phase 19 Decision Engine
Integrates all Phase 19 services, generates analysis reports, and answers the core question:
'Does Phase 17 genuinely outperform Phase 12 on sufficiently large, unseen, forward market data?'
"""

import os
import json
import logging
from typing import Dict, Any, List

from backend.research.phase19.services.forward_data_service import forward_data_service
from backend.research.phase19.services.rolling_metrics import rolling_metrics_engine
from backend.research.phase19.services.regime_analysis import regime_and_asset_engine
from backend.research.phase19.services.calibration_analysis import calibration_analysis_engine
from backend.research.phase19.services.trade_performance import trade_performance_engine
from backend.research.phase19.services.statistical_validation import statistical_validation_engine
from backend.research.phase19.services.promotion_readiness import promotion_readiness_engine

logger = logging.getLogger(__name__)


class Phase19DecisionEngine:
    """Master orchestration service for Phase 19 forward monitoring and decision support."""

    def run_full_phase19_analysis(self) -> Dict[str, Any]:
        """Runs complete Phase 19 analysis pipeline across all 14 required research domains."""
        # 1. Eligibility Audit & Paired Dataset
        audit_report, eligible_recs = forward_data_service.perform_eligibility_audit()
        paired_records = forward_data_service.get_paired_dataset(resolved_only=True)

        # 2. Cumulative Performance
        cumulative_res = rolling_metrics_engine.compute_cumulative_performance(paired_records)

        # 3. Rolling Performance Windows (N=20, 50, 100, 250)
        rolling_res = rolling_metrics_engine.compute_rolling_windows(paired_records)

        # 4. Per-Symbol Results (all 109+ symbols in ALL_SYMBOLS)
        per_symbol_res = regime_and_asset_engine.compute_per_symbol_results(paired_records)

        # 5. Asset Group Results (INDIA, USA, CRYPTO, ALL-ASSETS)
        asset_group_res = regime_and_asset_engine.compute_asset_group_results(paired_records)

        # 6. Market Regime Results (BULL, BEAR, SIDEWAYS, HIGH_VOLATILITY, LOW_VOLATILITY)
        regime_res = regime_and_asset_engine.compute_regime_results(paired_records)

        # 7. Confidence Band Analysis
        confidence_res = calibration_analysis_engine.compute_confidence_analysis(paired_records)

        # 8. Calibration & Reliability Analysis (10 bins)
        calibration_res = calibration_analysis_engine.compute_calibration_analysis(paired_records)

        # 9. Phase 14 Trade Performance Comparison
        trade_res = trade_performance_engine.compare_trade_setups(paired_records)

        # 10. Statistical Validation (McNemar test, 95% Bootstrap CIs, effect size)
        stat_res = statistical_validation_engine.compute_statistical_tests(paired_records)

        # 11. Performance Stability (Early vs Middle vs Recent)
        ts = cumulative_res.get("time_series", [])
        if len(ts) >= 3:
            early_acc = ts[len(ts)//3].get("challenger_accuracy")
            mid_acc = ts[2*len(ts)//3].get("challenger_accuracy")
            recent_acc = ts[-1].get("challenger_accuracy")
            if early_acc is not None and recent_acc is not None:
                if recent_acc > early_acc + 0.02:
                    stability_status = "IMPROVING"
                elif recent_acc < early_acc - 0.05:
                    stability_status = "DECLINING"
                else:
                    stability_status = "CONSISTENT"
            else:
                stability_status = "INSUFFICIENT_DATA"
        else:
            stability_status = "INSUFFICIENT_DATA"

        stability_res = {
            "sample_size": len(paired_records),
            "stability_status": stability_status,
            "time_series_periods": len(ts)
        }

        # 12. Promotion Readiness & Scorecard
        promotion_res = promotion_readiness_engine.evaluate_promotion_readiness(
            audit_report, cumulative_res, rolling_res, asset_group_res,
            regime_res, calibration_res, trade_res, stat_res
        )

        final_verdict_res = {
            "phase": "PHASE19",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "promotion_policy": "NOT_AUTOMATIC",
            "sample_size": len(paired_records),
            "final_verdict": promotion_res["final_verdict"],
            "explanation": promotion_res["verdict_explanation"]
        }

        dataset_summary_res = {
            "phase": "PHASE19",
            "total_paired_observations": len(paired_records),
            "total_symbols_evaluated": len(per_symbol_res.get("symbols_evaluated", {})),
            "earliest_market_timestamp": paired_records[0]["market_timestamp"] if paired_records else None,
            "latest_market_timestamp": paired_records[-1]["market_timestamp"] if paired_records else None
        }

        return {
            "data_eligibility_report": audit_report,
            "paired_dataset_summary": dataset_summary_res,
            "cumulative_performance": cumulative_res,
            "rolling_performance": rolling_res,
            "per_symbol_results": per_symbol_res,
            "asset_group_results": asset_group_res,
            "regime_results": regime_res,
            "confidence_results": confidence_res,
            "calibration_results": calibration_res,
            "trade_results": trade_res,
            "statistical_results": stat_res,
            "stability_results": stability_res,
            "promotion_readiness": promotion_res,
            "final_verdict": final_verdict_res
        }


phase19_decision_engine = Phase19DecisionEngine()
