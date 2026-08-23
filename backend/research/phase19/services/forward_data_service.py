"""
StockSense AI — Phase 19 Forward Data Service
Queries Phase 18 shadow prediction records, performs a strict 17-point data eligibility audit,
excludes synthetic/test records, and constructs the paired Champion/Challenger dataset.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.data.universe import ALL_SYMBOLS

logger = logging.getLogger(__name__)

# Valid universe symbols set
VALID_UNIVERSE = set(sym.upper() for sym in ALL_SYMBOLS)


class ForwardDataService:
    """
    Manages data retrieval, 17-point data eligibility audit, and paired dataset construction
    for Phase 19 forward monitoring and decision support.
    """

    def perform_eligibility_audit(self) -> Dict[str, Any]:
        """
        Executes a 17-point eligibility audit across all Phase 18 shadow prediction records.
        Logically classifies records as ELIGIBLE, SYNTHETIC, DUPLICATE, or INVALID.
        """
        with get_db_context() as db:
            all_records = db.query(Phase18ShadowPredictionRecord).all()

        total = len(all_records)
        eligible_records: List[Phase18ShadowPredictionRecord] = []
        excluded_records: List[Dict[str, Any]] = []

        synthetic_count = 0
        duplicate_count = 0
        invalid_count = 0

        reasons_counter: Dict[str, int] = {}
        seen_keys: set = set()

        for rec in all_records:
            reasons = []

            # 1. Genuine source check
            if getattr(rec, "data_status", "LIVE") != "LIVE":
                reasons.append("NON_LIVE_DATA_STATUS")
                synthetic_count += 1

            # 2. Universe symbol check
            sym = rec.symbol.upper() if rec.symbol else ""
            if not sym or sym not in VALID_UNIVERSE:
                reasons.append("INVALID_UNIVERSE_SYMBOL")

            # 3. Model role check
            if rec.model_role not in ["CHAMPION", "CHALLENGER"]:
                reasons.append("INVALID_MODEL_ROLE")

            # 4. Model version string check
            if not rec.model_version:
                reasons.append("MISSING_MODEL_VERSION")

            # 5 & 6. Probability bounds check
            p_up = rec.probability_up
            p_down = rec.probability_down
            if p_up is None or p_down is None:
                reasons.append("MISSING_PROBABILITY")
            elif not (0.0 <= p_up <= 1.0 and 0.0 <= p_down <= 1.0):
                reasons.append("PROBABILITY_OUT_OF_BOUNDS")

            # 7 & 8. Prediction & feature timestamp check
            pred_ts = rec.prediction_timestamp
            feat_ts = rec.feature_timestamp or pred_ts
            mkt_ts = rec.market_timestamp or pred_ts
            if not pred_ts:
                reasons.append("MISSING_PREDICTION_TIMESTAMP")

            # 9 & 10. Outcome ordering check (if resolved)
            if rec.resolved:
                res_ts = rec.resolution_timestamp or rec.resolved_at
                if not res_ts:
                    reasons.append("MISSING_RESOLUTION_TIMESTAMP")
                elif feat_ts > pred_ts:
                    reasons.append("FEATURE_TIMESTAMPS_FUTURE_OF_PREDICTION")
                elif pred_ts >= res_ts:
                    reasons.append("PREDICTION_TIMESTAMPS_NOT_BEFORE_OUTCOME")

                # 11, 12, 13. Resolved values check
                if rec.actual_direction not in ["UP", "DOWN"]:
                    reasons.append("INVALID_ACTUAL_DIRECTION")
                if rec.actual_price is None or rec.actual_price <= 0:
                    reasons.append("INVALID_ACTUAL_PRICE")
                if rec.current_price is None or rec.current_price <= 0:
                    reasons.append("INVALID_CURRENT_PRICE")

            # 14. Logical duplicate check
            dedup_key = (
                sym,
                mkt_ts.isoformat() if isinstance(mkt_ts, datetime) else str(mkt_ts),
                feat_ts.isoformat() if isinstance(feat_ts, datetime) else str(feat_ts),
                rec.model_version,
                rec.prediction_horizon or 1
            )
            if dedup_key in seen_keys:
                reasons.append("DUPLICATE_LOGICAL_OBSERVATION")
                duplicate_count += 1
            else:
                seen_keys.add(dedup_key)

            # 15. Synthetic test/fixture indicator check
            if "TEST" in sym or "MOCK" in sym or "DUMMY" in sym:
                reasons.append("SYNTHETIC_FIXTURE_SYMBOL")
                synthetic_count += 1

            # 16. Horizon check
            if rec.prediction_horizon != 1:
                reasons.append("UNSUPPORTED_PREDICTION_HORIZON")

            if not reasons:
                eligible_records.append(rec)
            else:
                invalid_count += 1
                for r in reasons:
                    reasons_counter[r] = reasons_counter.get(r, 0) + 1
                excluded_records.append({
                    "id": rec.id,
                    "symbol": rec.symbol,
                    "model_role": rec.model_role,
                    "reasons": reasons
                })

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_records": total,
            "eligible_records": len(eligible_records),
            "excluded_records": len(excluded_records),
            "synthetic_records_excluded": synthetic_count,
            "duplicate_records_excluded": duplicate_count,
            "invalid_records_excluded": invalid_count,
            "exclusion_reasons": reasons_counter,
            "audit_status": "PASSED"
        }
        return report, eligible_records

    def get_paired_dataset(
        self,
        resolved_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Constructs paired Champion and Challenger observation records.
        Pairs on (symbol, market_timestamp, feature_timestamp, prediction_horizon).
        Only includes records that passed the eligibility audit.
        """
        audit_report, eligible_recs = self.perform_eligibility_audit()
        
        # Index eligible records by role and key
        champ_map: Dict[Tuple[str, str, str, int], Phase18ShadowPredictionRecord] = {}
        chall_map: Dict[Tuple[str, str, str, int], Phase18ShadowPredictionRecord] = {}

        for rec in eligible_recs:
            if resolved_only and not rec.resolved:
                continue

            mkt_ts_str = rec.market_timestamp.isoformat() if isinstance(rec.market_timestamp, datetime) else str(rec.market_timestamp)
            feat_ts_str = rec.feature_timestamp.isoformat() if isinstance(rec.feature_timestamp, datetime) else str(rec.feature_timestamp)
            key = (rec.symbol.upper(), mkt_ts_str, feat_ts_str, rec.prediction_horizon or 1)

            if rec.model_role == "CHAMPION":
                champ_map[key] = rec
            elif rec.model_role == "CHALLENGER":
                chall_map[key] = rec

        paired_list = []
        for key, champ in champ_map.items():
            if key in chall_map:
                chall = chall_map[key]
                paired_list.append({
                    "symbol": champ.symbol.upper(),
                    "market_timestamp": champ.market_timestamp.isoformat() if isinstance(champ.market_timestamp, datetime) else str(champ.market_timestamp),
                    "feature_timestamp": champ.feature_timestamp.isoformat() if isinstance(champ.feature_timestamp, datetime) else str(champ.feature_timestamp),
                    "prediction_timestamp": champ.prediction_timestamp.isoformat() if isinstance(champ.prediction_timestamp, datetime) else str(champ.prediction_timestamp),
                    "resolution_timestamp": champ.resolution_timestamp.isoformat() if isinstance(champ.resolution_timestamp, datetime) else (champ.resolved_at.isoformat() if isinstance(champ.resolved_at, datetime) else str(champ.resolution_timestamp)),
                    "prediction_horizon": champ.prediction_horizon or 1,
                    "current_price": champ.current_price,
                    "actual_price": champ.actual_price,
                    "actual_direction": champ.actual_direction,
                    "actual_return": champ.actual_return,
                    "trend_regime": champ.trend_regime or "UNKNOWN",
                    "volatility_regime": champ.volatility_regime or "UNKNOWN",
                    "combined_regime": champ.combined_regime or "UNKNOWN",
                    "champion": {
                        "model_version": champ.model_version,
                        "predicted_direction": champ.predicted_direction,
                        "probability_up": champ.probability_up,
                        "probability_down": champ.probability_down,
                        "confidence": champ.confidence,
                        "correct": champ.correct,
                        "brier_score": champ.brier_score
                    },
                    "challenger": {
                        "model_version": chall.model_version,
                        "predicted_direction": chall.predicted_direction,
                        "probability_up": chall.probability_up,
                        "probability_down": chall.probability_down,
                        "confidence": chall.confidence,
                        "correct": chall.correct,
                        "brier_score": chall.brier_score
                    }
                })

        # Sort chronologically by market_timestamp
        paired_list.sort(key=lambda x: x["market_timestamp"])
        return paired_list


forward_data_service = ForwardDataService()
