"""
StockSense AI — Phase 20 Forward Dataset Builder
Queries Phase 18 shadow prediction records, audits for genuine LIVE observations,
excludes synthetic/fixture/test records, pairs Champion/Challenger predictions,
and compiles phase20_forward_dataset.parquet.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.data.universe import ALL_SYMBOLS, INDIA_SYMBOLS, US_SYMBOLS, CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)

VALID_UNIVERSE = set(sym.upper() for sym in ALL_SYMBOLS)
INDIA_SET = set(INDIA_SYMBOLS)
US_SET = set(US_SYMBOLS)
CRYPTO_SET = set(CRYPTO_SYMBOLS)


class ForwardDatasetBuilder:
    """Builds and audits phase20_forward_dataset.parquet from genuine Phase 18/19 observations."""

    def __init__(self, output_path: str = "backend/research/phase20/data/phase20_forward_dataset.parquet"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def build_forward_dataset(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Queries DB, filters for clean LIVE resolved Phase 18 shadow records,
        pairs Champion and Challenger observations, and exports to Parquet.
        """
        with get_db_context() as db:
            records = db.query(Phase18ShadowPredictionRecord).all()

        total_raw = len(records)
        synthetic_count = 0
        unresolved_count = 0
        invalid_universe_count = 0

        eligible_recs = []
        for rec in records:
            # Audit checks
            if getattr(rec, "data_status", "LIVE") != "LIVE":
                synthetic_count += 1
                continue

            sym = rec.symbol.upper() if rec.symbol else ""
            if not sym or sym in ["TEST_MOCK_XYZ", "MOCK_BTC", "MOCK_AAPL"] or sym not in VALID_UNIVERSE:
                invalid_universe_count += 1
                continue

            if not rec.resolved or rec.correct is None or rec.actual_direction is None:
                unresolved_count += 1
                continue

            eligible_recs.append(rec)

        # Pair Champion and Challenger
        champ_map = {}
        chall_map = {}

        for rec in eligible_recs:
            key = (rec.symbol.upper(), rec.market_timestamp, rec.feature_timestamp, rec.prediction_horizon)
            if rec.model_role == "CHAMPION":
                champ_map[key] = rec
            elif rec.model_role == "CHALLENGER":
                chall_map[key] = rec

        common_keys = set(champ_map.keys()).intersection(set(chall_map.keys()))

        rows = []
        for key in common_keys:
            c = champ_map[key]
            ch = chall_map[key]

            symbol = c.symbol.upper()
            if symbol in INDIA_SET:
                asset_grp = "INDIA"
            elif symbol in US_SET:
                asset_grp = "USA"
            elif symbol in CRYPTO_SET:
                asset_grp = "CRYPTO"
            else:
                asset_grp = "ALL-ASSETS"

            rows.append({
                "symbol": symbol,
                "market_timestamp": c.market_timestamp.isoformat() if c.market_timestamp else None,
                "feature_timestamp": c.feature_timestamp.isoformat() if c.feature_timestamp else None,
                "prediction_timestamp": c.prediction_timestamp.isoformat() if c.prediction_timestamp else None,
                "outcome_timestamp": c.resolution_timestamp.isoformat() if c.resolution_timestamp else None,
                "actual_direction": c.actual_direction,
                "actual_return": c.actual_return,
                "champion_probability": c.probability_up,
                "champion_prediction": c.predicted_direction,
                "challenger_probability": ch.probability_up,
                "challenger_prediction": ch.predicted_direction,
                "regime": getattr(c, "regime", "SIDEWAYS") or "SIDEWAYS",
                "volatility_regime": getattr(c, "volatility_regime", "LOW_VOLATILITY") or "LOW_VOLATILITY",
                "confidence": max(c.probability_up, 1.0 - c.probability_up),
                "asset_group": asset_grp
            })

        df_forward = pd.DataFrame(rows)
        if not df_forward.empty:
            df_forward.to_parquet(self.output_path, index=False)

        audit_report = {
            "total_raw_db_records": total_raw,
            "synthetic_records_excluded": synthetic_count,
            "unresolved_records_excluded": unresolved_count,
            "invalid_universe_excluded": invalid_universe_count,
            "eligible_records": len(eligible_recs),
            "total_paired_observations": len(rows),
            "output_parquet_path": self.output_path,
            "symbols_covered": df_forward["symbol"].nunique() if not df_forward.empty else 0
        }

        return df_forward, audit_report
