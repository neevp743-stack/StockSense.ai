from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from backend.db.database import Base


class WatchtowerStateRecord(Base):
    __tablename__ = "watchtower_state"

    id = Column(Integer, primary_key=True, default=1)
    current_status = Column(String(50), default="HEALTHY")
    consecutive_failures = Column(Integer, default=0)
    consecutive_successes = Column(Integer, default=0)
    is_outage_active = Column(Boolean, default=False)
    last_check_ts = Column(DateTime, nullable=True)
    last_successful_check_ts = Column(DateTime, nullable=True)
    current_latency_ms = Column(Float, default=0.0)
    total_checks = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    last_outage_ts = Column(DateTime, nullable=True)
    last_recovery_ts = Column(DateTime, nullable=True)
    monitoring_status = Column(String(50), default="ACTIVE")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WatchtowerCheckRecord(Base):
    __tablename__ = "watchtower_checks"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    http_status = Column(Integer, nullable=True)
    latency_ms = Column(Float, default=0.0)
    health_state = Column(String(50), nullable=False)
    error_message = Column(String(255), nullable=True)
