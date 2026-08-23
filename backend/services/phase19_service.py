"""
StockSense AI — Phase 19 Service Interface for API Endpoints
Provides fast, cached access to Phase 19 research reports and decision support calculations.
Guarantees warm API response latency < 10ms.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from backend.research.phase19.services.decision_engine import phase19_decision_engine

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join("backend", "research", "phase19", "reports")


class Phase19Service:
    """Caching service wrapper for Phase 19 API endpoints."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[float] = None

    def _read_report_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(REPORTS_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading Phase 19 report {filename}: {e}")
        return {}

    def get_full_analysis(self, force_refresh: bool = False) -> Dict[str, Any]:
        if not self._cache or force_refresh:
            self._cache = phase19_decision_engine.run_full_phase19_analysis()
        return self._cache

    def get_status(self) -> Dict[str, Any]:
        verdict_res = self._read_report_json("final_verdict.json")
        if not verdict_res:
            res = self.get_full_analysis()
            verdict_res = res.get("final_verdict", {})

        return {
            "mode": "RESEARCH",
            "phase": "PHASE19",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "promotion_policy": "NOT_AUTOMATIC",
            "final_verdict": verdict_res.get("final_verdict", "PHASE19_INSUFFICIENT_FORWARD_DATA"),
            "explanation": verdict_res.get("explanation", "Insufficient forward observations.")
        }

    def get_summary(self) -> Dict[str, Any]:
        summary_res = self._read_report_json("cumulative_performance.json")
        if not summary_res:
            res = self.get_full_analysis()
            summary_res = res.get("cumulative_performance", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "summary": summary_res
        }

    def get_rolling(self) -> Dict[str, Any]:
        rolling_res = self._read_report_json("rolling_performance.json")
        if not rolling_res:
            res = self.get_full_analysis()
            rolling_res = res.get("rolling_performance", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "rolling_windows": rolling_res
        }

    def get_symbols(self) -> Dict[str, Any]:
        symbols_res = self._read_report_json("per_symbol_results.json")
        if not symbols_res:
            res = self.get_full_analysis()
            symbols_res = res.get("per_symbol_results", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "per_symbol": symbols_res
        }

    def get_regimes(self) -> Dict[str, Any]:
        regimes_res = self._read_report_json("regime_results.json")
        if not regimes_res:
            res = self.get_full_analysis()
            regimes_res = res.get("regime_results", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "regimes": regimes_res
        }

    def get_calibration(self) -> Dict[str, Any]:
        calib_res = self._read_report_json("calibration_results.json")
        conf_res = self._read_report_json("confidence_results.json")
        if not calib_res:
            res = self.get_full_analysis()
            calib_res = res.get("calibration_results", {})
            conf_res = res.get("confidence_results", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "calibration": calib_res,
            "confidence_bands": conf_res
        }

    def get_trades(self) -> Dict[str, Any]:
        trade_res = self._read_report_json("trade_results.json")
        if not trade_res:
            res = self.get_full_analysis()
            trade_res = res.get("trade_results", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "trades": trade_res
        }

    def get_statistics(self) -> Dict[str, Any]:
        stat_res = self._read_report_json("statistical_results.json")
        if not stat_res:
            res = self.get_full_analysis()
            stat_res = res.get("statistical_results", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "statistics": stat_res
        }

    def get_promotion_readiness(self) -> Dict[str, Any]:
        prom_res = self._read_report_json("promotion_readiness.json")
        if not prom_res:
            res = self.get_full_analysis()
            prom_res = res.get("promotion_readiness", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "promotion_readiness": prom_res
        }

    def get_data_quality(self) -> Dict[str, Any]:
        audit_res = self._read_report_json("data_eligibility_report.json")
        if not audit_res:
            res = self.get_full_analysis()
            audit_res = res.get("data_eligibility_report", {})

        return {
            "mode": "RESEARCH",
            "production_model": "XGBoost v1.0 Calibrated",
            "challenger_model": "Phase 17 Large XGBoost",
            "data_quality_audit": audit_res
        }


phase19_service = Phase19Service()
