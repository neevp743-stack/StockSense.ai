"""
StockSense AI — Forward Validation Service (Phase 18)
High-level service interface connecting DB shadow prediction records, resolution, comparison engines,
and REST API endpoints.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from backend.config import PROJECT_ROOT
from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker
from backend.research.phase18.forward_resolver import forward_resolver
from backend.research.phase18.comparison_engine import comparison_engine
from backend.research.phase18.statistical_tests import statistical_test_engine
from backend.research.phase18.trade_comparison import trade_comparison_engine
from backend.research.phase18.promotion_rules import promotion_rule_engine

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(PROJECT_ROOT, "backend", "research", "phase18", "phase18_config.json")


def load_phase18_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "champion_model": "XGBoost v1.0 Calibrated",
        "challenger_model": "Phase17 Large XGBoost",
        "mode": "SHADOW",
        "minimum_metric_sample": 10,
        "minimum_promotion_sample": 100,
        "alpha": 0.05
    }


class ForwardValidationService:
    """
    High-level forward validation interface.
    """

    def __init__(self):
        self.config = load_phase18_config()

    def get_status(self) -> Dict[str, Any]:
        """Returns current Phase 18 validation status."""
        counts = shadow_prediction_tracker.get_counts()
        paired_resolved = counts.get("paired_resolved", 0)

        # Quick promotion status check
        comp_res = comparison_engine.evaluate_paired_comparison()
        grp_res = comparison_engine.evaluate_asset_groups()
        reg_res = comparison_engine.evaluate_regimes()
        stat_res = statistical_test_engine.analyze_statistical_significance()
        trade_res = trade_comparison_engine.compare_trade_setups()

        promo_res = promotion_rule_engine.evaluate_promotion_criteria(comp_res, grp_res, reg_res, stat_res, trade_res)

        return {
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase17 Large XGBoost",
            "mode": "SHADOW",
            "promotion_status": promo_res.get("verdict", "PHASE18_INSUFFICIENT_FORWARD_DATA"),
            "recommendation": promo_res.get("recommendation", "KEEP PHASE 12 IN PRODUCTION."),
            "total_observations": counts.get("total_observations", 0),
            "champion_resolved": counts.get("champion", {}).get("resolved", 0),
            "challenger_resolved": counts.get("challenger", {}).get("resolved", 0),
            "paired_resolved_samples": paired_resolved
        }

    def get_comparison(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Returns paired Champion vs Challenger comparison metrics and rolling windows."""
        comp_res = comparison_engine.evaluate_paired_comparison(symbol=symbol)
        rolling_res = comparison_engine.evaluate_rolling_windows(symbol=symbol)
        return {
            "symbol": symbol or "ALL_SYMBOLS",
            "summary": comp_res,
            "rolling_windows": rolling_res
        }

    def get_trades(self) -> Dict[str, Any]:
        """Returns Phase 14 trade setup comparison metrics."""
        return trade_comparison_engine.compare_trade_setups()

    def get_statistics(self) -> Dict[str, Any]:
        """Returns statistical hypothesis test results (McNemar, bootstrap CIs)."""
        return statistical_test_engine.analyze_statistical_significance()


forward_validation_service = ForwardValidationService()
