"""
StockSense AI — Shadow Prediction Service (Phase 18)
Generates parallel Champion (Phase 12 Calibrated XGBoost v1.0) and Challenger (Phase 17 Large XGBoost)
shadow predictions on live market observations without altering production endpoints or behavior.
"""

import os
import hashlib
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List

from backend.config import PROJECT_ROOT
from backend.db.database import get_db_context
from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord
from backend.models.baseline_models import ModelPipeline
from backend.data.universe import ALL_SYMBOLS
from backend.features.feature_engine import compute_phase15_features, FEATURE_COLUMNS

logger = logging.getLogger(__name__)

PHASE17_MODEL_PATH = os.path.join(PROJECT_ROOT, "saved_models", "phase17", "global_xgboost", "model.joblib")


def get_file_sha256(filepath: str) -> Optional[str]:
    if not os.path.exists(filepath):
        return None
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ShadowPredictionService:
    """
    Manages dual Champion/Challenger shadow inference and record persistence.
    """

    def __init__(self):
        self._challenger_model = None
        self._challenger_hash = None
        self._load_challenger()

    def _load_challenger(self):
        """Loads Phase 17 Large XGBoost Challenger model from isolated path."""
        if os.path.exists(PHASE17_MODEL_PATH):
            try:
                self._challenger_model = joblib.load(PHASE17_MODEL_PATH)
                self._challenger_hash = get_file_sha256(PHASE17_MODEL_PATH)[:16]
                logger.info(f"Loaded Phase 17 Challenger model (SHA256: {self._challenger_hash})")
            except Exception as e:
                logger.error(f"Failed to load Phase 17 Challenger model: {e}")

    def verify_model_compatibility(self) -> Dict[str, Any]:
        """
        Verifies Champion and Challenger model availability, versioning, feature ordering, and hashes.
        """
        champion_sample = ModelPipeline.load_model("RELIANCE", "XGBoost")
        champ_ok = champion_sample is not None and champion_sample.is_trained
        chall_ok = self._challenger_model is not None and hasattr(self._challenger_model, "predict_proba")

        if not champ_ok or not chall_ok:
            return {
                "status": "PHASE18_MODEL_COMPATIBILITY_ERROR",
                "champion_available": champ_ok,
                "challenger_available": chall_ok,
                "reason": "One or both model artifacts missing or invalid"
            }

        return {
            "status": "OK",
            "champion_available": True,
            "challenger_available": True,
            "champion_model_name": "XGBoost v1.0 Calibrated",
            "challenger_model_name": "Phase17 Large XGBoost",
            "challenger_hash": self._challenger_hash,
            "feature_count_champ": len(FEATURE_COLUMNS),
            "feature_count_challenger": len(getattr(self._challenger_model, "feature_names_in_", []))
        }

    def validate_eligibility(
        self,
        symbol: str,
        current_price: Optional[float],
        market_ts: Optional[datetime],
        feature_ts: Optional[datetime],
        data_status: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforces 8-point data eligibility criteria for live forward-validation observations.
        """
        if data_status != "LIVE":
            return False, f"Ineligible data_status: {data_status}"

        if current_price is None or current_price <= 0 or not np.isfinite(current_price):
            return False, "Invalid current_price"

        if market_ts is None or feature_ts is None:
            return False, "Missing market or feature timestamp"

        clean_symbol = symbol.upper().strip()
        if clean_symbol not in ALL_SYMBOLS:
            return False, f"Symbol {clean_symbol} not in Phase 17 ALL_SYMBOLS universe"

        if feature_ts > market_ts + timedelta(seconds=5):
            return False, "feature_timestamp > market_timestamp (Lookahead anomaly)"

        return True, None

    def generate_and_record_shadow_predictions(
        self,
        symbol: str,
        df_ohlcv: pd.DataFrame,
        current_price: float,
        market_ts: datetime,
        feature_ts: datetime,
        data_status: str = "LIVE",
        regime_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generates paired Champion and Challenger predictions for eligible observations.
        Records both into phase18_shadow_predictions with strict duplicate protection.
        """
        clean_symbol = symbol.upper().strip()
        prediction_ts = datetime.now(timezone.utc)

        # 1. Eligibility Check
        eligible, reason = self.validate_eligibility(clean_symbol, current_price, market_ts, feature_ts, data_status)
        if not eligible:
            return {"status": "SKIPPED", "reason": reason}

        # 2. Compute Features
        try:
            df_feat = compute_phase15_features(df_ohlcv)
            if df_feat.empty:
                return {"status": "SKIPPED", "reason": "Empty feature DataFrame"}
            latest_row = df_feat.iloc[[-1]]
        except Exception as e:
            return {"status": "ERROR", "reason": f"Feature extraction failed: {e}"}

        # Regimes
        regime_info = regime_info or {}
        trend_reg = regime_info.get("trend_regime", "SIDEWAYS")
        vol_reg = regime_info.get("volatility_regime", "LOW_VOLATILITY")
        comb_reg = f"{trend_reg}_{vol_reg}"

        results = {}

        # 3. Champion Prediction (Phase 12)
        try:
            champ_pipe = ModelPipeline.load_model(clean_symbol, "XGBoost")
            if champ_pipe and champ_pipe.is_trained:
                preds_c, probas_c = champ_pipe.predict(latest_row)
                p_up_c = float(probas_c[0])
                p_down_c = float(1.0 - p_up_c)
                dir_c = "UP" if p_up_c >= 0.5 else "DOWN"
                conf_c = "HIGH" if abs(p_up_c - 0.5) >= 0.15 else ("MODERATE" if abs(p_up_c - 0.5) >= 0.05 else "LOW")

                rec_c = self._save_shadow_record(
                    symbol=clean_symbol,
                    prediction_ts=prediction_ts,
                    market_ts=market_ts,
                    feature_ts=feature_ts,
                    model_role="CHAMPION",
                    model_version="XGBoost v1.0 Calibrated",
                    predicted_direction=dir_c,
                    prob_up=p_up_c,
                    prob_down=p_down_c,
                    confidence=conf_c,
                    trend_reg=trend_reg,
                    vol_reg=vol_reg,
                    comb_reg=comb_reg,
                    current_price=current_price,
                    data_status=data_status,
                    feature_version="v12"
                )
                results["champion"] = rec_c
        except Exception as e:
            logger.error(f"Champion inference error for {clean_symbol}: {e}")
            results["champion_error"] = str(e)

        # 4. Challenger Prediction (Phase 17 Shadow)
        if self._challenger_model is not None:
            try:
                # Match feature names required by Phase 17 XGBoost
                f_names = getattr(self._challenger_model, "feature_names_in_", FEATURE_COLUMNS)
                # Fill missing columns with 0.0 if not in latest_row
                X_chall = []
                for fn in f_names:
                    if fn in latest_row.columns:
                        val = latest_row[fn].values[0]
                    else:
                        val = 0.0
                    X_chall.append(0.0 if np.isnan(val) else float(val))

                X_chall_arr = np.array(X_chall, dtype=np.float32).reshape(1, -1)
                probas_ch = self._challenger_model.predict_proba(X_chall_arr)[0]
                p_up_ch = float(probas_ch[1])
                p_down_ch = float(1.0 - p_up_ch)
                dir_ch = "UP" if p_up_ch >= 0.5 else "DOWN"
                conf_ch = "HIGH" if abs(p_up_ch - 0.5) >= 0.15 else ("MODERATE" if abs(p_up_ch - 0.5) >= 0.05 else "LOW")

                rec_ch = self._save_shadow_record(
                    symbol=clean_symbol,
                    prediction_ts=prediction_ts,
                    market_ts=market_ts,
                    feature_ts=feature_ts,
                    model_role="CHALLENGER",
                    model_version="Phase17 Large XGBoost",
                    predicted_direction=dir_ch,
                    prob_up=p_up_ch,
                    prob_down=p_down_ch,
                    confidence=conf_ch,
                    trend_reg=trend_reg,
                    vol_reg=vol_reg,
                    comb_reg=comb_reg,
                    current_price=current_price,
                    data_status=data_status,
                    feature_version="v17",
                    artifact_hash=self._challenger_hash
                )
                results["challenger"] = rec_ch
            except Exception as e:
                logger.error(f"Challenger shadow inference error for {clean_symbol}: {e}")
                results["challenger_error"] = str(e)

        return {"status": "RECORDED", "results": results}

    def _save_shadow_record(
        self,
        symbol: str,
        prediction_ts: datetime,
        market_ts: datetime,
        feature_ts: datetime,
        model_role: str,
        model_version: str,
        predicted_direction: str,
        prob_up: float,
        prob_down: float,
        confidence: str,
        trend_reg: str,
        vol_reg: str,
        comb_reg: str,
        current_price: float,
        data_status: str,
        feature_version: str,
        artifact_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves a shadow record with application-level duplicate protection."""
        with get_db_context() as db:
            # Check duplicate (symbol, market_timestamp, feature_timestamp, model_version, prediction_horizon)
            dup = db.query(Phase18ShadowPredictionRecord).filter_by(
                symbol=symbol,
                market_timestamp=market_ts,
                feature_timestamp=feature_ts,
                model_version=model_version,
                prediction_horizon=1
            ).first()

            if dup is not None:
                return {"id": dup.id, "status": "DUPLICATE_SKIPPED"}

            rec = Phase18ShadowPredictionRecord(
                symbol=symbol,
                prediction_timestamp=prediction_ts,
                market_timestamp=market_ts,
                feature_timestamp=feature_ts,
                model_role=model_role,
                model_version=model_version,
                predicted_direction=predicted_direction,
                probability_up=prob_up,
                probability_down=prob_down,
                confidence=confidence,
                trend_regime=trend_reg,
                volatility_regime=vol_reg,
                combined_regime=comb_reg,
                current_price=current_price,
                prediction_horizon=1,
                feature_version=feature_version,
                data_status=data_status,
                resolved=False,
                model_artifact_hash=artifact_hash
            )
            try:
                db.add(rec)
                db.commit()
                db.refresh(rec)
                return {"id": rec.id, "status": "CREATED", "model_role": model_role, "predicted_direction": predicted_direction}
            except Exception as e:
                db.rollback()
                logger.warning(f"DB duplicate/integrity skip for {symbol} {model_role}: {e}")
                return {"status": "DB_INTEGRITY_SKIP", "error": str(e)}


shadow_prediction_service = ShadowPredictionService()
