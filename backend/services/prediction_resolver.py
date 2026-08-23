"""
StockSense AI — Live Prediction Resolver (Phase 16)
Evaluates unresolved historical predictions against subsequent market data outcomes.
Adds resolution metrics without altering original prediction parameters.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord, StockPrice
from backend.data.data_service import get_historical_data_from_db

logger = logging.getLogger(__name__)


class PredictionResolver:
    """
    Evaluates unresolved live prediction records against actual forward market outcomes.
    """

    def resolve_unresolved_predictions(self, symbol: str = None) -> Dict[str, Any]:
        """
        Resolves pending live predictions using historical close prices.
        Returns resolution summary dictionary.
        """
        resolved_count = 0
        error_count = 0

        try:
            with get_db_context() as db:
                query = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.resolved == False
                )
                if symbol:
                    query = query.filter(LivePredictionRecord.symbol == symbol.upper().strip())

                unresolved = query.all()
                if not unresolved:
                    return {"resolved_count": 0, "error_count": 0}

                # Group unresolved records by symbol
                records_by_symbol = {}
                for rec in unresolved:
                    records_by_symbol.setdefault(rec.symbol, []).append(rec)

                now = datetime.now(timezone.utc)

                for sym, rec_list in records_by_symbol.items():
                    df_hist = get_historical_data_from_db(sym)
                    if df_hist.empty or len(df_hist) < 2:
                        continue

                    # Sort by date
                    df_sorted = df_hist.sort_values("date").reset_index(drop=True)
                    date_to_close = {row["date"]: float(row["close"]) for _, row in df_sorted.iterrows()}
                    dates = list(df_sorted["date"])

                    for rec in rec_list:
                        # Determine base price and target price
                        base_price = rec.current_price
                        market_date = rec.market_timestamp.date() if rec.market_timestamp else None

                        if not base_price and market_date and market_date in date_to_close:
                            base_price = date_to_close[market_date]

                        # Find actual price after horizon
                        actual_price = None
                        if market_date and market_date in dates:
                            idx = dates.index(market_date)
                            if idx + rec.prediction_horizon < len(dates):
                                target_date = dates[idx + rec.prediction_horizon]
                                actual_price = date_to_close.get(target_date)

                        # Fallback for recent live ticks: use latest close if at least 1 day has passed
                        if actual_price is None and base_price is not None:
                            last_date = dates[-1]
                            last_close = date_to_close[last_date]
                            if market_date and (last_date - market_date).days >= rec.prediction_horizon:
                                actual_price = last_close

                        if base_price and actual_price and base_price > 0:
                            act_return = (actual_price - base_price) / base_price
                            act_dir = "UP" if act_return > 0 else "DOWN"
                            is_corr = (rec.predicted_direction == act_dir)

                            y_true = 1.0 if act_dir == "UP" else 0.0
                            brier = (rec.probability_up - y_true) ** 2

                            # Resolution fields
                            rec.resolved = True
                            rec.resolution_timestamp = now
                            rec.resolved_at = now
                            rec.actual_price = round(actual_price, 2)
                            rec.actual_direction = act_dir
                            rec.resolved_direction = act_dir
                            rec.actual_return = round(act_return, 6)
                            rec.correct = is_corr
                            rec.is_correct = is_corr
                            rec.brier_score = round(brier, 6)
                            rec.error_reason = None

                            resolved_count += 1

                db.commit()

        except Exception as e:
            logger.error(f"Error in PredictionResolver: {e}")
            error_count += 1

        return {
            "resolved_count": resolved_count,
            "error_count": error_count
        }


# Global Singleton Service
prediction_resolver = PredictionResolver()
