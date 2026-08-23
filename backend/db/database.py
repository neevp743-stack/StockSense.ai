from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from contextlib import contextmanager

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text

def init_db():
    from backend.models.phase18_shadow_prediction_record import Phase18ShadowPredictionRecord  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Ensure SQLite column migrations for existing databases
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE model_metadata ADD COLUMN asset_class VARCHAR(50)",
            "ALTER TABLE predictions ADD COLUMN asset_class VARCHAR(50)",
            "ALTER TABLE predictions ADD COLUMN data_status VARCHAR(20)",
            "ALTER TABLE live_prediction_records ADD COLUMN market_timestamp DATETIME",
            "ALTER TABLE live_prediction_records ADD COLUMN confidence VARCHAR(20)",
            "ALTER TABLE live_prediction_records ADD COLUMN trend_regime VARCHAR(20)",
            "ALTER TABLE live_prediction_records ADD COLUMN volatility_regime VARCHAR(20)",
            "ALTER TABLE live_prediction_records ADD COLUMN combined_regime VARCHAR(50)",
            "ALTER TABLE live_prediction_records ADD COLUMN current_price FLOAT",
            "ALTER TABLE live_prediction_records ADD COLUMN prediction_horizon INTEGER DEFAULT 1",
            "ALTER TABLE live_prediction_records ADD COLUMN feature_version VARCHAR(20) DEFAULT 'v12'",
            "ALTER TABLE live_prediction_records ADD COLUMN resolved BOOLEAN DEFAULT 0",
            "ALTER TABLE live_prediction_records ADD COLUMN resolution_timestamp DATETIME",
            "ALTER TABLE live_prediction_records ADD COLUMN actual_price FLOAT",
            "ALTER TABLE live_prediction_records ADD COLUMN actual_direction VARCHAR(10)",
            "ALTER TABLE live_prediction_records ADD COLUMN actual_return FLOAT",
            "ALTER TABLE live_prediction_records ADD COLUMN correct BOOLEAN",
            "ALTER TABLE live_prediction_records ADD COLUMN brier_score FLOAT",
            "ALTER TABLE live_prediction_records ADD COLUMN error_reason VARCHAR(255)"
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass

# Run schema migrations on database module import
try:
    init_db()
except Exception:
    pass


