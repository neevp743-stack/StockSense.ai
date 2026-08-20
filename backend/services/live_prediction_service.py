"""
StockSense AI — Live AI Prediction Engine Service
Provides 30-second throttled real-time model inference, probability normalization,
LivePredictionRecord persistence, and prediction auto-resolution.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from backend.db.database import get_db_context
from backend.db.models import LivePredictionRecord, StockPrice
from backend.data.realtime_provider import realtime_provider_manager
from backend.data.provider import YFinanceProvider
from backend.models.baseline_models import ModelPipeline
from backend.features.feature_engine import compute_features_and_target
from backend.data.data_service import get_historical_data_from_db


logger = logging.getLogger(__name__)

class LivePredictionService:
    """
    Service responsible for real-time inference, prediction throttling,
    probability calculation, and prediction resolution tracking.
    """

    def __init__(self, throttle_seconds: int = 30):
        self.throttle_seconds = throttle_seconds
        self.prediction_cache: Dict[str, Dict[str, Any]] = {}
        self.quote_provider = YFinanceProvider()

    def get_live_prediction(self, symbol: str, model_name: str = "XGBoost") -> Dict[str, Any]:
        """
        Computes live direction prediction for a given symbol.
        Returns throttled prediction if computed within throttle_seconds.
        """
        symbol_clean = symbol.upper().strip()
        now = datetime.utcnow()

        # Check inference throttle cache
        cache_key = f"{symbol_clean}_{model_name}"
        if cache_key in self.prediction_cache:
            cached_pred = self.prediction_cache[cache_key]
            try:
                cached_ts = datetime.fromisoformat(cached_pred["prediction_timestamp"])
                if (now - cached_ts).total_seconds() < self.throttle_seconds:
                    # Update current live tick price in cached prediction payload
                    latest_tick = realtime_provider_manager.cache.get_latest_tick(symbol_clean)
                    if latest_tick:
                        cached_pred["live_price"] = latest_tick["price"]
                        cached_pred["data_status"] = latest_tick["data_status"]
                    return cached_pred
            except Exception:
                pass

        # 1. Verify Model Existence
        pipe = ModelPipeline.load_model(symbol_clean, model_name)
        if not pipe or not pipe.is_trained:
            # Fallback check for LogisticRegression or any trained model
            pipe = ModelPipeline.load_model(symbol_clean, "LogisticRegression")

        if not pipe or not pipe.is_trained:
            return {
                "symbol": symbol_clean,
                "status": "MODEL NOT TRAINED FOR THIS ASSET",
                "message": f"No trained model found for asset symbol '{symbol_clean}'.",
                "predicted_direction": "NEUTRAL",
                "probability_up": 0.50,
                "probability_down": 0.50,
                "model_version": "N/A",
                "prediction_timestamp": now.isoformat(),
                "feature_timestamp": now.isoformat(),
                "data_status": "UNAVAILABLE"
            }

        # 2. Fetch Latest Live Tick or Quote
        latest_tick = realtime_provider_manager.cache.get_latest_tick(symbol_clean)
        if latest_tick:
            current_price = latest_tick["price"]
            data_status = latest_tick["data_status"]
            provider_name = latest_tick["provider"]
            input_ts = latest_tick["timestamp"]
        else:
            quote = self.quote_provider.get_latest_quote(symbol_clean)
            if not quote or quote.get("price") is None:
                return {
                    "symbol": symbol_clean,
                    "status": "REAL-TIME DATA UNAVAILABLE",
                    "message": f"Market data unavailable for asset '{symbol_clean}'.",
                    "predicted_direction": "NEUTRAL",
                    "probability_up": 0.50,
                    "probability_down": 0.50,
                    "model_version": f"{model_name} v1.0",
                    "prediction_timestamp": now.isoformat(),
                    "feature_timestamp": now.isoformat(),
                    "data_status": "UNAVAILABLE"
                }
            current_price = quote["price"]
            data_status = quote.get("data_status", "DELAYED")
            provider_name = quote.get("provider", "yfinance")
            input_ts = quote.get("timestamp", now.isoformat())

        # 3. Construct Live Features Without Modifying Historical DB Data
        df_hist = get_historical_data_from_db(symbol_clean)
        if df_hist.empty or len(df_hist) < 30:
            return {
                "symbol": symbol_clean,
                "status": "INSUFFICIENT HISTORICAL DATA",
                "predicted_direction": "NEUTRAL",
                "probability_up": 0.50,
                "probability_down": 0.50,
                "model_version": f"{model_name} v1.0",
                "prediction_timestamp": now.isoformat(),
                "feature_timestamp": now.isoformat(),
                "data_status": data_status
            }

        df_feat = compute_features_and_target(df_hist)
        if df_feat.empty:
            return {
                "symbol": symbol_clean,
                "status": "FEATURE COMPUTATION ERROR",
                "predicted_direction": "NEUTRAL",
                "probability_up": 0.50,
                "probability_down": 0.50,
                "model_version": f"{model_name} v1.0",
                "prediction_timestamp": now.isoformat(),
                "feature_timestamp": now.isoformat(),
                "data_status": data_status
            }

        latest_row = df_feat.iloc[[-1]]
        preds, probs = pipe.predict(latest_row)

        # 4. Strict Probability Formatting & Validation
        prob_up = float(probs[0])
        prob_up = max(0.0, min(1.0, prob_up))
        prob_down = round(1.0 - prob_up, 4)
        direction = "UP" if prob_up >= 0.50 else "DOWN"

        feat_d = latest_row["date"].iloc[0]
        feature_ts_str = feat_d.isoformat() if hasattr(feat_d, "isoformat") else str(feat_d)

        prediction_payload = {
            "symbol": symbol_clean,
            "status": "SUCCESS",
            "live_price": current_price,
            "predicted_direction": direction,
            "probability_up": round(prob_up, 4),
            "probability_down": prob_down,
            "model_version": f"{pipe.model_name} v1.0",
            "prediction_timestamp": now.isoformat(),
            "feature_timestamp": feature_ts_str,
            "data_status": data_status,
            "provider": provider_name,
            "risk_category": "LOW" if abs(prob_up - 0.50) > 0.15 else ("HIGH" if abs(prob_up - 0.50) < 0.05 else "MEDIUM")
        }

        # Update cache
        self.prediction_cache[cache_key] = prediction_payload

        # 5. Persist Prediction Record to DB (Prevent Duplicate Predictions Within 30 Seconds)
        try:
            with get_db_context() as db:
                cutoff = now - timedelta(seconds=self.throttle_seconds)
                recent_dup = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.symbol == symbol_clean,
                    LivePredictionRecord.prediction_timestamp >= cutoff
                ).first()

                if not recent_dup:
                    rec = LivePredictionRecord(
                        symbol=symbol_clean,
                        prediction_timestamp=now,
                        feature_timestamp=feat_d if isinstance(feat_d, datetime) else datetime.utcnow(),
                        probability_up=round(prob_up, 4),
                        probability_down=prob_down,
                        predicted_direction=direction,
                        model_version=f"{pipe.model_name} v1.0",
                        data_status=data_status
                    )
                    db.add(rec)
                    db.commit()
        except Exception as e:
            logger.error(f"Error persisting LivePredictionRecord: {e}")

        return prediction_payload

    def resolve_pending_predictions(self) -> Dict[str, Any]:
        """Resolves past unresolved prediction records against actual market data."""
        resolved_count = 0
        try:
            with get_db_context() as db:
                unresolved = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.resolved_direction.is_(None)
                ).all()

                for rec in unresolved:
                    df = get_historical_data_from_db(rec.symbol)
                    if not df.empty and len(df) > 1:
                        latest_bar = df.iloc[-1]
                        prev_bar = df.iloc[-2]

                        ret = (latest_bar["close"] - prev_bar["close"]) / prev_bar["close"]
                        actual_dir = "UP" if ret > 0 else "DOWN"
                        rec.resolved_direction = actual_dir
                        rec.resolved_at = datetime.utcnow()
                        rec.is_correct = (rec.predicted_direction == actual_dir)
                        resolved_count += 1
                db.commit()
        except Exception as e:
            logger.error(f"Error resolving predictions: {e}")

        return {"resolved_count": resolved_count}

    def get_prediction_tracker_stats(self, symbol: str) -> Dict[str, Any]:
        """Calculates prediction tracking statistics directly from database records enforcing N>=30 threshold rule."""
        symbol_clean = symbol.upper().strip()
        try:
            with get_db_context() as db:
                records = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.symbol == symbol_clean
                ).all()

                total_predictions = len(records)
                resolved_records = [r for r in records if r.resolved_direction is not None]
                resolved_count = len(resolved_records)
                unresolved_count = total_predictions - resolved_count

                correct_count = sum(1 for r in resolved_records if r.is_correct is True)
                wrong_count = sum(1 for r in resolved_records if r.is_correct is False)

                accuracy = (correct_count / resolved_count) if resolved_count > 0 else None

                latest_resolved = resolved_records[-1] if resolved_records else None

                # Enforce >= 30 sample size threshold rule
                if resolved_count >= 30:
                    accuracy_display = f"{(accuracy * 100):.1f}% (N={resolved_count})"
                else:
                    accuracy_display = f"INSUFFICIENT LIVE SAMPLE SIZE (N={resolved_count}/30)"

                return {
                    "symbol": symbol_clean,
                    "total_predictions": total_predictions,
                    "resolved_count": resolved_count,
                    "unresolved_count": unresolved_count,
                    "correct_count": correct_count,
                    "wrong_count": wrong_count,
                    "accuracy": round(accuracy, 4) if (accuracy is not None and resolved_count >= 30) else None,
                    "accuracy_display": accuracy_display,
                    "sample_size": resolved_count,
                    "sample_size_threshold_met": resolved_count >= 30,
                    "resolved_display": f"{latest_resolved.resolved_direction} {'✅' if latest_resolved.is_correct else '❌'}" if latest_resolved else "No resolved predictions yet"
                }
        except Exception as e:
            logger.error(f"Error fetching prediction tracker stats: {e}")
            return {
                "symbol": symbol_clean,
                "total_predictions": 0,
                "resolved_count": 0,
                "unresolved_count": 0,
                "correct_count": 0,
                "wrong_count": 0,
                "accuracy": None,
                "accuracy_display": "INSUFFICIENT LIVE SAMPLE SIZE (N=0/30)",
                "sample_size": 0,
                "sample_size_threshold_met": False,
                "resolved_display": "No resolved predictions yet"
            }

    def get_live_collection_status(self) -> Dict[str, Any]:
        """Returns global live research collection status and metrics."""
        is_configured = realtime_provider_manager.is_configured()
        status_str = "COLLECTION ACTIVE" if is_configured else "PROVIDER UNAVAILABLE"
        if is_configured and realtime_provider_manager.connection_status == "RECONNECTING":
            status_str = "COLLECTION PAUSED"

        try:
            with get_db_context() as db:
                total_preds = db.query(LivePredictionRecord).count()
                resolved_preds = db.query(LivePredictionRecord).filter(
                    LivePredictionRecord.resolved_direction.isnot(None)
                ).count()
                unresolved_preds = total_preds - resolved_preds

                last_rec = db.query(LivePredictionRecord).order_by(
                    LivePredictionRecord.prediction_timestamp.desc()
                ).first()
                last_pred_ts = last_rec.prediction_timestamp.isoformat() if last_rec else None

                # Get latest tick timestamp across cache
                latest_tick_ts = None
                for sym, tick in realtime_provider_manager.cache._ticks.items():
                    if tick.get("timestamp"):
                        latest_tick_ts = tick.get("timestamp")
                        break

                return {
                    "collection_status": status_str,
                    "provider": realtime_provider_manager.provider_name,
                    "symbols_being_collected": list(realtime_provider_manager.subscribed_symbols),
                    "predictions_created": total_preds,
                    "predictions_resolved": resolved_preds,
                    "unresolved_predictions": unresolved_preds,
                    "last_prediction_timestamp": last_pred_ts,
                    "last_tick_timestamp": latest_tick_ts
                }
        except Exception as e:
            logger.error(f"Error fetching live collection status: {e}")
            return {
                "collection_status": status_str,
                "provider": realtime_provider_manager.provider_name,
                "symbols_being_collected": [],
                "predictions_created": 0,
                "predictions_resolved": 0,
                "unresolved_predictions": 0,
                "last_prediction_timestamp": None,
                "last_tick_timestamp": None
            }

# Global Singleton Service
live_prediction_service = LivePredictionService(throttle_seconds=30)


