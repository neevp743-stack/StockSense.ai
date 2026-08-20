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
    Base.metadata.create_all(bind=engine)
    # Ensure SQLite column migrations for existing databases
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE model_metadata ADD COLUMN asset_class VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE predictions ADD COLUMN asset_class VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE predictions ADD COLUMN data_status VARCHAR(20)"))
            conn.commit()
        except Exception:
            pass
