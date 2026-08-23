"""
StockSense AI — Phase 18 Shadow Prediction Record Database Model
Stores isolated Champion (Phase 12) and Challenger (Phase 17) shadow prediction observations.
Includes composite unique index protection for deterministic duplicate prevention.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, UniqueConstraint, Index
from backend.db.database import Base


class Phase18ShadowPredictionRecord(Base):
    __tablename__ = "phase18_shadow_predictions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)

    prediction_timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    market_timestamp = Column(DateTime, nullable=True)
    feature_timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)

    model_role = Column(String(20), nullable=False, default="SHADOW")  # CHAMPION or CHALLENGER
    model_version = Column(String(50), nullable=False)                 # "XGBoost v1.0 Calibrated" or "Phase17 Large XGBoost"

    predicted_direction = Column(String(10), nullable=False)            # UP, DOWN
    probability_up = Column(Float, nullable=False)
    probability_down = Column(Float, nullable=False)

    confidence = Column(String(20), nullable=True)                     # HIGH, MODERATE, LOW
    trend_regime = Column(String(20), nullable=True)                   # BULL, BEAR, SIDEWAYS
    volatility_regime = Column(String(20), nullable=True)              # HIGH_VOLATILITY, LOW_VOLATILITY
    combined_regime = Column(String(50), nullable=True)               # e.g., BULL_LOW_VOLATILITY

    current_price = Column(Float, nullable=True)
    prediction_horizon = Column(Integer, default=1)

    feature_version = Column(String(20), default="v17")
    data_status = Column(String(20), nullable=False, default="LIVE")    # LIVE, DELAYED, STALE

    # Resolution fields
    resolved = Column(Boolean, default=False, index=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    actual_price = Column(Float, nullable=True)
    actual_direction = Column(String(10), nullable=True)            # UP, DOWN
    actual_return = Column(Float, nullable=True)
    correct = Column(Boolean, nullable=True)
    brier_score = Column(Float, nullable=True)
    error_reason = Column(String(255), nullable=True)

    # Provenance fields
    model_artifact_hash = Column(String(64), nullable=True)
    calibration_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "symbol", "market_timestamp", "feature_timestamp", "model_version", "prediction_horizon",
            name="uix_phase18_shadow_observation"
        ),
        Index("idx_p18_shadow_sym_role_ts", "symbol", "model_role", "prediction_timestamp"),
    )
