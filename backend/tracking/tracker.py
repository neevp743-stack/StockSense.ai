from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.database import SessionLocal
from backend.db.models import PredictionRecord, StockPrice

def log_prediction(
    symbol: str,
    as_of_date: date,
    prediction_date: date,
    predicted_direction: int,
    prob_up: float,
    prob_down: float,
    risk_category: str,
    model_version: str,
    explanation_json: Optional[str] = None,
    db: Optional[Session] = None
) -> PredictionRecord:
    """Logs a new prediction record without overwriting past predictions."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Check if identical prediction already exists for symbol, prediction_date, model_version
        existing = db.query(PredictionRecord).filter(
            and_(
                PredictionRecord.stock_symbol == symbol.upper().strip(),
                PredictionRecord.prediction_date == prediction_date,
                PredictionRecord.model_version == model_version
            )
        ).first()

        if existing:
            return existing

        rec = PredictionRecord(
            stock_symbol=symbol.upper().strip(),
            as_of_date=as_of_date,
            prediction_date=prediction_date,
            predicted_direction=predicted_direction,
            probability_up=prob_up,
            probability_down=prob_down,
            risk_category=risk_category,
            model_version=model_version,
            explanation_json=explanation_json,
            prediction_timestamp=datetime.utcnow()
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
    finally:
        if close_db:
            db.close()

def resolve_pending_predictions(symbol: Optional[str] = None, db: Optional[Session] = None) -> int:
    """
    Checks for pending predictions (actual_direction is NULL) where actual market close price
    for prediction_date is now available in stock_prices table.
    Updates actual_direction, is_correct, resolved_at. Never alters initial predictions.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        query = db.query(PredictionRecord).filter(PredictionRecord.actual_direction == None)
        if symbol:
            query = query.filter(PredictionRecord.stock_symbol == symbol.upper().strip())

        pending = query.all()
        resolved_count = 0

        for pred in pending:
            # Get stock price on as_of_date (Close_t) and prediction_date (Close_{t+1})
            price_t = db.query(StockPrice).filter(
                and_(StockPrice.symbol == pred.stock_symbol, StockPrice.date == pred.as_of_date)
            ).first()

            price_t_next = db.query(StockPrice).filter(
                and_(StockPrice.symbol == pred.stock_symbol, StockPrice.date == pred.prediction_date)
            ).first()

            if price_t and price_t_next:
                actual_dir = 1 if price_t_next.close > price_t.close else 0
                is_correct = (pred.predicted_direction == actual_dir)

                pred.actual_direction = actual_dir
                pred.is_correct = is_correct
                pred.resolved_at = datetime.utcnow()
                resolved_count += 1

        if resolved_count > 0:
            db.commit()

        return resolved_count
    finally:
        if close_db:
            db.close()

def get_prediction_history(symbol: Optional[str] = None, limit: int = 50, db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """Returns historical prediction records with resolution status."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        query = db.query(PredictionRecord)
        if symbol:
            query = query.filter(PredictionRecord.stock_symbol == symbol.upper().strip())

        records = query.order_by(PredictionRecord.prediction_date.desc()).limit(limit).all()

        results = []
        for r in records:
            results.append({
                "id": r.id,
                "stock_symbol": r.stock_symbol,
                "as_of_date": r.as_of_date.strftime("%Y-%m-%d"),
                "prediction_date": r.prediction_date.strftime("%Y-%m-%d"),
                "predicted_direction": "UP" if r.predicted_direction == 1 else "DOWN",
                "probability_up": r.probability_up,
                "probability_down": r.probability_down,
                "risk_category": r.risk_category,
                "model_version": r.model_version,
                "explanation_json": r.explanation_json,
                "prediction_timestamp": r.prediction_timestamp.isoformat() if r.prediction_timestamp else None,
                "actual_direction": "UP" if r.actual_direction == 1 else ("DOWN" if r.actual_direction == 0 else "PENDING"),
                "is_correct": r.is_correct,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None
            })
        return results
    finally:
        if close_db:
            db.close()
