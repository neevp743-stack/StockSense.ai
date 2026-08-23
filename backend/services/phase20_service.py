"""
StockSense AI — Phase 20 Research API Service Wrapper
Exposes fast cached JSON responses (< 10ms) for Phase 20 research REST API endpoints.
Ensures zero side-effects on Phase 12 production prediction logic.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Phase20Service:
    """Fast API service layer reading generated Phase 20 research reports."""

    def __init__(self, reports_dir: str = "backend/research/phase20/reports"):
        self.reports_dir = reports_dir

    def _read_report(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.reports_dir, filename)
        if not os.path.exists(path):
            return {
                "phase": "PHASE20",
                "status": "INITIALIZING",
                "message": f"Report '{filename}' pending pipeline execution.",
                "file": path
            }
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading Phase 20 report {path}: {e}")
            return {"error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        return self._read_report("final_verdict.json")

    def get_comparison(self) -> Dict[str, Any]:
        return self._read_report("model_comparison.json")

    def get_symbol(self, symbol: str) -> Dict[str, Any]:
        sym_clean = symbol.upper().strip()
        per_symbol = self._read_report("asset_results.json")
        return {
            "symbol": sym_clean,
            "phase": "PHASE20",
            "details": per_symbol.get("asset_groups", {}).get(sym_clean, {"status": "RESEARCH_ONLY", "symbol": sym_clean})
        }

    def get_forward(self) -> Dict[str, Any]:
        return self._read_report("forward_results.json")

    def get_regimes(self) -> Dict[str, Any]:
        return self._read_report("regime_results.json")

    def get_calibration(self) -> Dict[str, Any]:
        return self._read_report("calibration_results.json")

    def get_drift(self) -> Dict[str, Any]:
        return self._read_report("drift_analysis.json")

    def get_readiness(self) -> Dict[str, Any]:
        return self._read_report("promotion_scorecard.json")


phase20_service = Phase20Service()
