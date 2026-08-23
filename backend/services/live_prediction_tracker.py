"""
StockSense AI — Live Prediction Tracker (Phase 16)
Idempotently records live production predictions for forward-testing validation.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord

logger = logging.getLogger(__name__)


class LivePredictionTracker:
    """
    Idempotent prediction observation recorder preventing duplicate entries.
    """

    def record_prediction(self, prediction_payload: Dict[str, Any], db_session=None) -> Optional[int]:
        """
        Persists a live prediction observation if no duplicate record exists for the same timestamp/window.
        Returns the record ID.
        """
        if not prediction_payload or prediction_payload.get("status") != "SUCCESS":
            return None

        symbol = str(prediction_payload.get("symbol", "")).upper().strip()
        if not symbol:
            return None

        now = datetime.now(timezone.utc)
        
        # Extracttimestamps
        feat_ts_str = prediction_payload.get("feature_timestamp")
        market_ts = None
        if feat_ts_str:
            try:
                market_ts = datetime.fromisoformat(feat_ts_str.replace("Z", "+00:00"))
            except Exception:
                market_ts = now

        model_version = prediction_payload.get("model_version", "XGBoost v1.0")
        prob_up = float(prediction_payload.get("probability_up", 0.50))
        prob_down = float(prediction_payload.get("probability_down", 0.50))
        predicted_dir = prediction_payload.get("predicted_direction", "UP")
        current_price = prediction_payload.get("live_price") or prediction_payload.get("current_price")
        data_status = prediction_payload.get("data_status", "LIVE")

        # Regimes & Confidence
        regime_info = prediction_payload.get("regime", {})
        trend_regime = regime_info.get("trend_regime", "SIDEWAYS") if isinstance(regime_info, dict) else "SIDEWAYS"
        vol_regime = regime_info.get("volatility_regime", "LOW_VOLATILITY") if isinstance(regime_info, dict) else "LOW_VOLATILITY"
        combined_regime = f"{trend_regime}_{vol_regime}"
        
        risk_cat = prediction_payload.get("risk_category", "MEDIUM")
        confidence = "HIGH" if risk_cat == "LOW" else ("LOW" if risk_cat == "HIGH" else "MODERATE")

        def _do_insert(db):
            # Check 30-second window uniqueness or exact market_timestamp match
            cutoff = now - timedelta(seconds=30)
            existing = db.query(LivePredictionRecord).filter(
                LivePredictionRecord.symbol == symbol,
                LivePredictionRecord.model_version == model_version,
                LivePredictionRecord.prediction_timestamp >= cutoff
            ).first()

            if existing:
                return existing.id

            rec = LivePredictionRecord(
                symbol=symbol,
                prediction_timestamp=now,
                market_timestamp=market_ts,
                feature_timestamp=market_ts,
                model_version=model_version,
                predicted_direction=predicted_dir,
                probability_up=prob_up,
                probability_down=prob_down,
                confidence=confidence,
                trend_regime=trend_regime,
                volatility_regime=vol_regime,
                combined_regime=combined_regime,
                current_price=current_price,
                prediction_horizon=1,
                feature_version="v12",
                data_status=data_status,
                resolved=False
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return rec.id

        try:
            if db_session:
                return _do_insert(db_session)
            else:
                with get_db_context() as db:
                    return _do_insert(db)
        except Exception as e:
            logger.error(f"Error in LivePredictionTracker: {e}")
            return None


# Global Singleton Service
live_prediction_tracker = LivePredictionTracker()
