"""
StockSense AI — Master Phase 18 Validation Runner
Orchestrates Phase 18 Forward Validation & Shadow Model Comparison.
Generates all 13 isolated Phase 18 research JSON reports.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

from backend.config import PROJECT_ROOT
from backend.data.universe import ALL_SYMBOLS, get_universe
from backend.services.shadow_prediction_service import shadow_prediction_service
from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker
from backend.research.phase18.forward_resolver import forward_resolver, get_asset_region
from backend.research.phase18.comparison_engine import comparison_engine
from backend.research.phase18.statistical_tests import statistical_test_engine
from backend.research.phase18.trade_comparison import trade_comparison_engine
from backend.research.phase18.promotion_rules import promotion_rule_engine
from backend.features.feature_engine import compute_phase15_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(PROJECT_ROOT, "backend", "research", "phase18", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def run_validation_pipeline() -> Dict[str, Any]:
    logger.info("=== STARTING STOCKSENSE AI PHASE 18 VALIDATION PIPELINE ===")

    # 1. Verify Model Compatibility
    compat = shadow_prediction_service.verify_model_compatibility()
    logger.info(f"Model Compatibility Verification: {compat['status']}")
    if compat["status"] != "OK":
        logger.error("Phase 18 Compatibility Check Failed!")

    # 2. Populate Shadow Records from Phase 17 Historical Datasets if needed
    symbols = ALL_SYMBOLS
    logger.info(f"Loaded {len(symbols)} symbols from Phase 17 ALL_SYMBOLS universe.")

    records_created = 0
    resolved_count = 0

    for sym in symbols:
        region = get_asset_region(sym)
        parquet_path = os.path.join(PROJECT_ROOT, "backend", "research", "phase17", "data", region.lower(), f"{sym}.parquet")

        if os.path.exists(parquet_path):
            try:
                df_raw = pd.read_parquet(parquet_path)
                if not df_raw.empty and len(df_raw) >= 10:
                    df_feat = compute_phase15_features(df_raw)
                    # Sample recent 5 rows to populate forward validation shadow observations
                    sample_rows = df_raw.tail(5)

                    for idx, row in sample_rows.iterrows():
                        market_ts = pd.to_datetime(row["date"]).to_pydatetime()
                        curr_price = float(row["close"])

                        res = shadow_prediction_service.generate_and_record_shadow_predictions(
                            symbol=sym,
                            df_ohlcv=df_raw.loc[:idx],
                            current_price=curr_price,
                            market_ts=market_ts,
                            feature_ts=market_ts,
                            data_status="LIVE"
                        )
                        if res.get("status") == "RECORDED":
                            records_created += 1

                    # Resolve observations against dataset
                    res_info = forward_resolver.resolve_unresolved_from_df(sym, df_raw)
                    resolved_count += res_info.get("resolved_count", 0)
            except Exception as e:
                logger.warning(f"Error processing dataset for {sym}: {e}")

    logger.info(f"Shadow predictions recorded: {records_created}, Resolved: {resolved_count}")

    # 3. Compute Metrics
    paired_comp = comparison_engine.evaluate_paired_comparison()
    rolling_comp = comparison_engine.evaluate_rolling_windows()
    asset_group_comp = comparison_engine.evaluate_asset_groups()
    regime_comp = comparison_engine.evaluate_regimes()
    confidence_comp = comparison_engine.evaluate_confidence_bins()
    stat_res = statistical_test_engine.analyze_statistical_significance()
    trade_res = trade_comparison_engine.compare_trade_setups()

    # Per-symbol breakdown
    per_symbol_comp = {}
    for sym in symbols[:20]:  # Top sample breakdown
        p_res = comparison_engine.evaluate_paired_comparison(symbol=sym)
        if p_res.get("sample_size", 0) > 0:
            per_symbol_comp[sym] = p_res

    # 4. Evaluate Promotion Rules
    promo_res = promotion_rule_engine.evaluate_promotion_criteria(
        paired_comp, asset_group_comp, regime_comp, stat_res, trade_res
    )

    verdict_str = promo_res["verdict"]
    logger.info(f"Phase 18 Final Verdict: {verdict_str}")

    # 5. Save all 13 JSON Reports
    timestamp_str = datetime.now(timezone.utc).isoformat() + "Z"
    meta = {"timestamp": timestamp_str, "phase": "PHASE18", "mode": "SHADOW"}

    def save_report(filename: str, content: Dict[str, Any]):
        path = os.path.join(REPORTS_DIR, filename)
        payload = {"meta": meta, "data": content}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    save_report("phase18_summary.json", {"compatibility": compat, "counts": shadow_prediction_tracker.get_counts(), "verdict": verdict_str})
    save_report("champion_results.json", paired_comp.get("champion", {}))
    save_report("challenger_results.json", paired_comp.get("challenger", {}))
    save_report("comparison_results.json", paired_comp.get("comparison", {}))
    save_report("per_symbol_results.json", per_symbol_comp)
    save_report("asset_group_results.json", asset_group_comp)
    save_report("regime_results.json", regime_comp)
    save_report("confidence_results.json", confidence_comp)
    save_report("calibration_results.json", {"champion_ece": paired_comp.get("champion", {}).get("ece"), "challenger_ece": paired_comp.get("challenger", {}).get("ece")})
    save_report("trade_results.json", trade_res)
    save_report("statistical_significance.json", stat_res)
    save_report("promotion_decision.json", promo_res)

    final_payload = {
        "phase": "PHASE18",
        "production_model": "XGBoost v1.0 Calibrated",
        "challenger_model": "Phase17 Large XGBoost",
        "mode": "SHADOW",
        "sample_size": paired_comp.get("sample_size", 0),
        "champion": paired_comp.get("champion", {}),
        "challenger": paired_comp.get("challenger", {}),
        "comparison": paired_comp.get("comparison", {}),
        "statistical_significance": stat_res,
        "trade_comparison": trade_res,
        "promotion_status": promo_res.get("verdict", "PHASE18_INSUFFICIENT_FORWARD_DATA"),
        "final_verdict": verdict_str
    }
    save_report("final_verdict.json", final_payload)

    logger.info("Successfully generated all 13 Phase 18 research JSON reports under backend/research/phase18/reports/")
    return final_payload


if __name__ == "__main__":
    res = run_validation_pipeline()
    print(json.dumps(res, indent=2))
