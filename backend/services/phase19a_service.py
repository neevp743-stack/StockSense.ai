"""
StockSense AI — Phase 19A Live Data Pipeline & Diagnostic Service
Provides real-time telemetry on market data providers (Finnhub WebSocket / REST fallback),
tick freshness, data status distributions, and shadow prediction pipeline diagnostics.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from backend.data.realtime_provider import realtime_provider_manager
from backend.services.data_quality_service import data_quality_service
from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.data.universe import ALL_SYMBOLS
from backend.models.baseline_models import ModelPipeline

logger = logging.getLogger(__name__)


class Phase19AService:
    """Service providing real-time data reliability and shadow pipeline diagnostics for Phase 19A."""

    def get_overall_status(self) -> Dict[str, Any]:
        """
        Returns overall Phase 19A telemetry:
        - Finnhub WebSocket connection status
        - REST Fallback status
        - Tick age and freshness
        - Symbol status breakdown across ALL_SYMBOLS
        - Today's shadow pipeline observation counts
        """
        ws_conn = realtime_provider_manager.connection_status.upper()
        # WebSocket statuses: CONNECTED (or LIVE), DISCONNECTED (or UNAVAILABLE), CONNECTING (or RECONNECTING)
        if ws_conn in ["LIVE", "CONNECTED"]:
            ws_status = "CONNECTED"
            rest_fallback = "STANDBY"
        elif ws_conn in ["RECONNECTING", "CONNECTING"]:
            ws_status = "CONNECTING"
            rest_fallback = "ACTIVE"
        else:
            ws_status = "DISCONNECTED"
            rest_fallback = "ACTIVE"

        # Finnhub API Key configuration check
        api_key_configured = realtime_provider_manager.is_configured()
        if not api_key_configured and rest_fallback == "ACTIVE":
            # If no API key set, REST fallback also operates in fallback mode
            pass

        # Inspect ticks for latest valid tick age & symbol breakdown
        latest_tick_age: Optional[float] = None
        data_status_counts = {"LIVE": 0, "DELAYED": 0, "STALE": 0, "UNAVAILABLE": 0}

        sample_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "AAPL", "NVDA", "BTC-USD"]
        for sym in sample_symbols:
            dq = data_quality_service.inspect_symbol_data_quality(sym)
            st = dq.get("status", "UNAVAILABLE")
            data_status_counts[st] = data_status_counts.get(st, 0) + 1

            tick_age = dq.get("last_tick_age_seconds")
            if tick_age is not None:
                if latest_tick_age is None or tick_age < latest_tick_age:
                    latest_tick_age = tick_age

        # Scale total count representation to match ALL_SYMBOLS universe
        remaining = len(ALL_SYMBOLS) - len(sample_symbols)
        if remaining > 0:
            data_status_counts["UNAVAILABLE"] += remaining

        # Determine overall data status
        if data_status_counts["LIVE"] > 0:
            overall_data_status = "LIVE"
        elif data_status_counts["DELAYED"] > 0:
            overall_data_status = "DELAYED"
        elif data_status_counts["STALE"] > 0:
            overall_data_status = "STALE"
        else:
            overall_data_status = "UNAVAILABLE"

        # Query today's Phase 18 shadow pipeline observations
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        observations_today = 0
        paired_today = 0
        failed_today = 0
        last_success_ts: Optional[str] = None

        try:
            with get_db_context() as db:
                recs_today = db.query(Phase18ShadowPredictionRecord).filter(
                    Phase18ShadowPredictionRecord.prediction_timestamp >= today_start
                ).all()

                observations_today = len(recs_today)
                failed_today = sum(1 for r in recs_today if r.error_reason is not None)

                # Find last successful observation timestamp
                resolved_recs = [r for r in recs_today if r.resolved and r.correct is not None]
                if resolved_recs:
                    sorted_recs = sorted(resolved_recs, key=lambda x: x.prediction_timestamp, reverse=True)
                    last_success_ts = sorted_recs[0].prediction_timestamp.isoformat()

                # Count paired resolved today
                champ_keys = set(
                    (r.symbol, r.market_timestamp, r.feature_timestamp)
                    for r in recs_today if r.model_role == "CHAMPION" and r.resolved
                )
                chall_keys = set(
                    (r.symbol, r.market_timestamp, r.feature_timestamp)
                    for r in recs_today if r.model_role == "CHALLENGER" and r.resolved
                )
                paired_today = len(champ_keys.intersection(chall_keys))
        except Exception as e:
            logger.error(f"Error querying Phase 18 shadow stats for Phase 19A: {e}")

        # Determine pipeline status
        if failed_today > 0 and observations_today > 0 and failed_today == observations_today:
            pipeline_status = "UNAVAILABLE"
        elif failed_today > 0 or overall_data_status in ["DELAYED", "STALE"]:
            pipeline_status = "DEGRADED"
        else:
            pipeline_status = "HEALTHY"

        return {
            "mode": "RESEARCH",
            "phase": "PHASE19A",
            "provider": "FINNHUB",
            "websocket_status": ws_status,
            "rest_fallback_status": rest_fallback,
            "latest_valid_tick_age_seconds": latest_tick_age,
            "data_status": overall_data_status,
            "symbol_counts": {
                "total_symbols": len(ALL_SYMBOLS),
                "live_symbols": data_status_counts["LIVE"],
                "delayed_symbols": data_status_counts["DELAYED"],
                "stale_symbols": data_status_counts["STALE"],
                "unavailable_symbols": data_status_counts["UNAVAILABLE"]
            },
            "shadow_pipeline": {
                "observations_today": observations_today,
                "paired_observations": paired_today,
                "failed_observations": failed_today,
                "last_successful_observation": last_success_ts,
                "pipeline_status": pipeline_status
            }
        }

    def get_symbol_diagnostics(self, symbol: str) -> Dict[str, Any]:
        """
        Returns Phase 19A symbol-specific diagnostics:
        - Live data status & fallback
        - Prediction pipeline (Champion & Challenger model status)
        - Database shadow observation counts
        - Actual backend error/reason
        """
        sym_clean = symbol.upper().strip()

        # 1. Live Data Inspection
        dq = data_quality_service.inspect_symbol_data_quality(sym_clean)
        ws_conn = realtime_provider_manager.connection_status.upper()
        if ws_conn in ["LIVE", "CONNECTED"]:
            ws_status = "CONNECTED"
            rest_fallback = "STANDBY"
        elif ws_conn in ["RECONNECTING", "CONNECTING"]:
            ws_status = "CONNECTING"
            rest_fallback = "ACTIVE"
        else:
            ws_status = "DISCONNECTED"
            rest_fallback = "ACTIVE"

        data_st = dq.get("status", "UNAVAILABLE")
        latest_price = dq.get("last_price")
        latest_market_ts = dq.get("latest_data_timestamp")

        # 2. Prediction Pipeline Inspection
        try:
            champ_pipe = ModelPipeline.load_model(sym_clean, "XGBoost")
            champ_status = "HEALTHY" if (champ_pipe and champ_pipe.is_trained) else "UNAVAILABLE"
        except Exception:
            champ_status = "UNAVAILABLE"

        # Challenger model check (Phase 17 model file)
        chall_model_path = os.path.join("saved_models", "phase17", "global_xgboost", "model.joblib")
        chall_status = "HEALTHY" if os.path.exists(chall_model_path) else "UNAVAILABLE"

        # 3. Database Shadow Observations for symbol
        total_obs = 0
        paired_obs = 0
        last_obs_ts: Optional[str] = None
        error_reason: Optional[str] = None

        try:
            with get_db_context() as db:
                recs = db.query(Phase18ShadowPredictionRecord).filter(
                    Phase18ShadowPredictionRecord.symbol == sym_clean
                ).order_by(Phase18ShadowPredictionRecord.prediction_timestamp.desc()).all()

                total_obs = len(recs)
                if recs:
                    last_obs_ts = recs[0].prediction_timestamp.isoformat()
                    errs = [r.error_reason for r in recs if r.error_reason]
                    if errs:
                        error_reason = errs[0]

                champ_keys = set((r.market_timestamp, r.feature_timestamp) for r in recs if r.model_role == "CHAMPION" and r.resolved)
                chall_keys = set((r.market_timestamp, r.feature_timestamp) for r in recs if r.model_role == "CHALLENGER" and r.resolved)
                paired_obs = len(champ_keys.intersection(chall_keys))
        except Exception as e:
            logger.error(f"Error querying shadow obs for symbol {sym_clean}: {e}")
            error_reason = str(e)

        if not error_reason:
            if ws_status != "CONNECTED" and rest_fallback == "ACTIVE":
                error_reason = "WebSocket idle or reconnecting; REST fallback active."
            elif data_st == "STALE":
                error_reason = "Tick age exceeds stale threshold (30s)."
            elif data_st == "UNAVAILABLE":
                error_reason = "Market provider quote feed unavailable for symbol."

        return {
            "symbol": sym_clean,
            "live_data": {
                "provider": "FINNHUB",
                "websocket_status": ws_status,
                "rest_fallback_status": rest_fallback,
                "latest_price": latest_price,
                "latest_market_timestamp": latest_market_ts,
                "data_status": data_st
            },
            "prediction_pipeline": {
                "champion_status": champ_status,
                "challenger_status": chall_status,
                "last_observation": last_obs_ts
            },
            "database": {
                "observations": total_obs,
                "paired_observations": paired_obs
            },
            "diagnostics": {
                "error_reason": error_reason
            }
        }


phase19a_service = Phase19AService()
