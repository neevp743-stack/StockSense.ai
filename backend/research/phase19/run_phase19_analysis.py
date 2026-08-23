"""
StockSense AI — Master Phase 19 CLI Orchestrator Script
Executes full forward monitoring, validation, and decision analysis.
Generates all 14 required JSON research reports under backend/research/phase19/reports/
"""

import os
import json
import logging
from typing import Dict, Any

from backend.research.phase19.services.decision_engine import phase19_decision_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join("backend", "research", "phase19", "reports")


def run_phase19_pipeline() -> Dict[str, Any]:
    """Executes Phase 19 decision analysis pipeline and writes 14 JSON research reports."""
    logger.info("=== STARTING STOCKSENSE AI PHASE 19 FORWARD MONITORING & DECISION PIPELINE ===")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    full_results = phase19_decision_engine.run_full_phase19_analysis()

    # Mapping of domain key to output report filename
    file_mapping = {
        "data_eligibility_report": "data_eligibility_report.json",
        "paired_dataset_summary": "paired_dataset_summary.json",
        "cumulative_performance": "cumulative_performance.json",
        "rolling_performance": "rolling_performance.json",
        "per_symbol_results": "per_symbol_results.json",
        "asset_group_results": "asset_group_results.json",
        "regime_results": "regime_results.json",
        "confidence_results": "confidence_results.json",
        "calibration_results": "calibration_results.json",
        "trade_results": "trade_results.json",
        "statistical_results": "statistical_results.json",
        "stability_results": "stability_results.json",
        "promotion_readiness": "promotion_readiness.json",
        "final_verdict": "final_verdict.json"
    }

    for key, filename in file_mapping.items():
        filepath = os.path.join(REPORTS_DIR, filename)
        content = full_results.get(key, {})
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, default=str)
        logger.info(f"Saved report: {filepath}")

    final_verdict = full_results["final_verdict"]["final_verdict"]
    logger.info(f"Phase 19 Final Verdict: {final_verdict}")
    logger.info(f"Successfully generated all 14 Phase 19 research JSON reports under {REPORTS_DIR}")

    print(json.dumps(full_results["final_verdict"], indent=2))
    return full_results


if __name__ == "__main__":
    run_phase19_pipeline()
