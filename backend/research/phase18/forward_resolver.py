"""
StockSense AI — Forward Resolver (Phase 18)
Resolves unresolved Champion and Challenger shadow prediction records against T+1 settlement market outcomes.
Respects regional asset trading calendars (NSE, NASDAQ/NYSE, Crypto 24/7) and avoids weekend/holiday leakage.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.data.universe import INDIA_SYMBOLS, US_SYMBOLS, CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)


def get_asset_region(symbol: str) -> str:
    """Returns region classification: INDIA, USA, or CRYPTO."""
    sym = symbol.upper().strip()
    if sym in INDIA_SYMBOLS:
        return "INDIA"
    elif sym in US_SYMBOLS:
        return "USA"
    elif sym in CRYPTO_SYMBOLS or "-USD" in sym:
        return "CRYPTO"
    return "UNKNOWN"


def is_market_day(dt: datetime, region: str) -> bool:
    """Returns True if dt is a valid trading day for given region."""
    if region == "CRYPTO":
        return True  # 24/7 calendar
    # Saturday = 5, Sunday = 6
    if dt.weekday() in [5, 6]:
        return False
    return True


class ForwardResolver:
    """
    Evaluates unresolved Phase 18 shadow prediction records against future settlement prices.
    """

    def resolve_prediction_record(
        self,
        record_id: int,
        future_price: float,
        settlement_ts: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Resolves a single prediction record given an actual future settlement price.
        Calculates return, direction, correctness, and Brier score.
        """
        with get_db_context() as db:
            rec = db.query(Phase18ShadowPredictionRecord).filter_by(id=record_id).first()
            if rec is None:
                return {"status": "NOT_FOUND", "record_id": record_id}

            if rec.resolved:
                return {"status": "ALREADY_RESOLVED", "record_id": record_id}

            if rec.current_price is None or rec.current_price <= 0:
                rec.resolved = True
                rec.error_reason = "missing_baseline_current_price"
                db.commit()
                return {"status": "RESOLVED_WITH_ERROR", "reason": "missing_baseline_current_price"}

            if future_price is None or future_price <= 0 or not np.isfinite(future_price):
                rec.resolved = True
                rec.error_reason = "missing_future_settlement_price"
                db.commit()
                return {"status": "RESOLVED_WITH_ERROR", "reason": "missing_future_settlement_price"}

            # Calculate settlement metrics
            p_curr = float(rec.current_price)
            p_fut = float(future_price)
            ret = (p_fut - p_curr) / p_curr
            actual_dir = "UP" if ret > 0 else "DOWN"
            y_binary = 1.0 if actual_dir == "UP" else 0.0

            is_correct = (rec.predicted_direction == actual_dir)
            brier = (rec.probability_up - y_binary) ** 2

            now_utc = datetime.now(timezone.utc)
            rec.resolved = True
            rec.resolution_timestamp = settlement_ts or now_utc
            rec.resolved_at = now_utc
            rec.actual_price = p_fut
            rec.actual_direction = actual_dir
            rec.actual_return = float(ret)
            rec.correct = bool(is_correct)
            rec.brier_score = float(brier)

            db.commit()
            return {
                "status": "RESOLVED",
                "record_id": rec.id,
                "model_role": rec.model_role,
                "actual_direction": actual_dir,
                "actual_return": ret,
                "correct": is_correct,
                "brier_score": brier
            }

    def resolve_unresolved_from_df(self, symbol: str, df_ohlcv: pd.DataFrame) -> Dict[str, Any]:
        """
        Scans unresolved predictions for a symbol and resolves them if settlement data exists in df_ohlcv.
        """
        clean_sym = symbol.upper().strip()
        region = get_asset_region(clean_sym)

        if df_ohlcv.empty or "close" not in df_ohlcv.columns:
            return {"symbol": clean_sym, "resolved_count": 0}

        df = df_ohlcv.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

        resolved_count = 0

        with get_db_context() as db:
            unresolved = db.query(Phase18ShadowPredictionRecord).filter(
                Phase18ShadowPredictionRecord.symbol == clean_sym,
                Phase18ShadowPredictionRecord.resolved == False
            ).all()

            for rec in unresolved:
                ref_ts = rec.market_timestamp or rec.feature_timestamp or rec.prediction_timestamp
                if ref_ts is None:
                    continue

                if "date" in df.columns:
                    # Find future date > ref_ts respecting calendar
                    future_df = df[df["date"] > pd.to_datetime(ref_ts)]
                    if not future_df.empty:
                        target_row = future_df.iloc[0]
                        fut_price = float(target_row["close"])
                        fut_ts = target_row["date"].to_pydatetime() if hasattr(target_row["date"], "to_pydatetime") else None

                        if is_market_day(pd.to_datetime(ref_ts).to_pydatetime(), region):
                            p_curr = float(rec.current_price) if rec.current_price else float(df[df["date"] <= pd.to_datetime(ref_ts)].iloc[-1]["close"])
                            ret = (fut_price - p_curr) / p_curr
                            actual_dir = "UP" if ret > 0 else "DOWN"
                            y_bin = 1.0 if actual_dir == "UP" else 0.0

                            rec.resolved = True
                            rec.resolution_timestamp = fut_ts or datetime.now(timezone.utc)
                            rec.resolved_at = datetime.now(timezone.utc)
                            rec.actual_price = fut_price
                            rec.actual_direction = actual_dir
                            rec.actual_return = float(ret)
                            rec.correct = (rec.predicted_direction == actual_dir)
                            rec.brier_score = float((rec.probability_up - y_bin) ** 2)
                            resolved_count += 1

            db.commit()

        return {"symbol": clean_sym, "resolved_count": resolved_count}


forward_resolver = ForwardResolver()
