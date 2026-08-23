from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.database import SessionLocal, init_db
from backend.db.models import PaperPredictionRecord, StockPrice

def log_paper_setup(
    setup_data: Dict[str, Any],
    as_of_d: date,
    pred_d: date,
    db: Optional[Session] = None
) -> Optional[PaperPredictionRecord]:
    """Logs a live trade setup to PaperPredictionRecord permanently without modifying past records."""
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True


    symbol_clean = setup_data.get("symbol", "").upper().strip()
    if not symbol_clean:
        if close_db: db.close()
        return None

    try:
        # Check duplicate prediction within 30 seconds
        cutoff = datetime.utcnow() - timedelta(seconds=30)
        existing = db.query(PaperPredictionRecord).filter(
            and_(
                PaperPredictionRecord.symbol == symbol_clean,
                PaperPredictionRecord.prediction_timestamp >= cutoff
            )
        ).first()

        if existing:
            return existing

        rec = PaperPredictionRecord(
            symbol=symbol_clean,
            prediction_timestamp=datetime.utcnow(),
            as_of_date=as_of_d,
            prediction_date=pred_d,
            signal=setup_data.get("signal", "HOLD"),
            probability_up=float(setup_data.get("probability_up", 0.5)),
            probability_down=float(setup_data.get("probability_down", 0.5)),
            confidence=setup_data.get("confidence", "LOW"),
            trend_regime=setup_data.get("trend_regime", "SIDEWAYS"),
            volatility_regime=setup_data.get("volatility_regime", "LOW_VOLATILITY"),
            combined_regime=setup_data.get("combined_regime", "SIDEWAYS (LOW VOL)"),
            current_price=float(setup_data.get("current_price", 0.0)),
            entry_low=float(setup_data.get("entry_low", 0.0)),
            entry_high=float(setup_data.get("entry_high", 0.0)),
            stop_loss=float(setup_data.get("stop_loss", 0.0)),
            target_1=float(setup_data.get("target_1", 0.0)),
            target_2=float(setup_data.get("target_2", 0.0)),
            risk_reward_target_1=float(setup_data.get("risk_reward_target_1", 1.0)),
            risk_reward_target_2=float(setup_data.get("risk_reward_target_2", 2.0)),
            model_version=setup_data.get("model_version", "XGBoost v1.0"),
            horizon_days=int(setup_data.get("horizon_days", 1)),
            outcome="PENDING"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
    except Exception as e:
        db.rollback()
        return None
    finally:
        if close_db:
            db.close()

def resolve_pending_paper_setups(symbol: Optional[str] = None, db: Optional[Session] = None) -> int:
    """
    Checks for unresolved paper predictions (outcome is PENDING or None)
    where actual market OHLC price on prediction_date is available.
    """
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True


    try:
        query = db.query(PaperPredictionRecord).filter(
            (PaperPredictionRecord.outcome == "PENDING") | (PaperPredictionRecord.outcome.is_(None))
        )
        if symbol:
            query = query.filter(PaperPredictionRecord.symbol == symbol.upper().strip())

        pending = query.all()
        resolved_count = 0

        for pred in pending:
            # Look up price on as_of_date and prediction_date
            p_t = db.query(StockPrice).filter(
                and_(StockPrice.symbol == pred.symbol, StockPrice.date == pred.as_of_date)
            ).first()
            p_next = db.query(StockPrice).filter(
                and_(StockPrice.symbol == pred.symbol, StockPrice.date == pred.prediction_date)
            ).first()

            if p_t and p_next:
                act_dir = "UP" if p_next.close > p_t.close else "DOWN"
                is_correct = (pred.signal == "BUY" and act_dir == "UP") or (pred.signal == "SELL" and act_dir == "DOWN")
                
                # Check hit targets/stop
                target_hit = False
                stop_hit = False
                outcome = "EXPIRED_HOLD"

                c_high = float(p_next.high)
                c_low = float(p_next.low)

                if pred.signal == "BUY":
                    hit_stop = c_low <= pred.stop_loss
                    hit_t1 = c_high >= pred.target_1
                    hit_t2 = c_high >= pred.target_2
                    if hit_stop and (hit_t1 or hit_t2):
                        outcome = "AMBIGUOUS"
                        stop_hit = True
                    elif hit_t2:
                        outcome = "TARGET_2_HIT"
                        target_hit = True
                    elif hit_t1:
                        outcome = "TARGET_1_HIT"
                        target_hit = True
                    elif hit_stop:
                        outcome = "STOP_HIT"
                        stop_hit = True

                    ret_pct = ((p_next.close - pred.current_price) / pred.current_price) * 100.0
                elif pred.signal == "SELL":
                    hit_stop = c_high >= pred.stop_loss
                    hit_t1 = c_low <= pred.target_1
                    hit_t2 = c_low <= pred.target_2
                    if hit_stop and (hit_t1 or hit_t2):
                        outcome = "AMBIGUOUS"
                        stop_hit = True
                    elif hit_t2:
                        outcome = "TARGET_2_HIT"
                        target_hit = True
                    elif hit_t1:
                        outcome = "TARGET_1_HIT"
                        target_hit = True
                    elif hit_stop:
                        outcome = "STOP_HIT"
                        stop_hit = True

                    ret_pct = ((pred.current_price - p_next.close) / pred.current_price) * 100.0
                else: # HOLD
                    ret_pct = 0.0

                pred.actual_direction = act_dir
                pred.actual_close_price = float(p_next.close)
                pred.target_hit = target_hit
                pred.stop_hit = stop_hit
                pred.outcome = outcome
                pred.realized_return_pct = round(ret_pct, 2)
                pred.resolved_at = datetime.utcnow()
                pred.is_correct = is_correct
                resolved_count += 1

        if resolved_count > 0:
            db.commit()

        return resolved_count
    finally:
        if close_db:
            db.close()

def get_paper_performance(symbol: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Returns live paper trading performance metrics for a given asset symbol."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    symbol_clean = symbol.upper().strip()

    try:
        # First attempt auto-resolving pending predictions
        resolve_pending_paper_setups(symbol_clean, db=db)

        all_records = db.query(PaperPredictionRecord).filter(
            PaperPredictionRecord.symbol == symbol_clean
        ).all()

        total_preds = len(all_records)
        resolved_recs = [r for r in all_records if r.outcome and r.outcome != "PENDING"]
        resolved_count = len(resolved_recs)
        pending_count = total_preds - resolved_count

        if resolved_count == 0:
            return {
                "symbol": symbol_clean,
                "data_source": "LIVE_PAPER_TRACKER",
                "total_predictions": total_preds,
                "resolved_predictions": 0,
                "pending_predictions": pending_count,
                "win_rate_pct": 0.0,
                "accuracy_pct": 0.0,
                "target_1_hit_rate_pct": 0.0,
                "target_2_hit_rate_pct": 0.0,
                "stop_hit_rate_pct": 0.0,
                "average_return_pct": 0.0,
                "median_return_pct": 0.0,
                "average_holding_period_days": 1.0,
                "sample_size_status": "INSUFFICIENT_SAMPLE"
            }

        returns = [r.realized_return_pct for r in resolved_recs if r.realized_return_pct is not None]
        correct_count = sum(1 for r in resolved_recs if r.is_correct)
        t1_count = sum(1 for r in resolved_recs if r.outcome == "TARGET_1_HIT")
        t2_count = sum(1 for r in resolved_recs if r.outcome == "TARGET_2_HIT")
        stop_count = sum(1 for r in resolved_recs if r.outcome in ("STOP_HIT", "AMBIGUOUS"))

        win_count = sum(1 for r in returns if r > 0)
        win_rate = (win_count / resolved_count) * 100.0
        acc_pct = (correct_count / resolved_count) * 100.0

        avg_ret = float(sum(returns) / len(returns)) if returns else 0.0
        med_ret = float(sorted(returns)[len(returns)//2]) if returns else 0.0

        return {
            "symbol": symbol_clean,
            "data_source": "LIVE_PAPER_TRACKER",
            "total_predictions": total_preds,
            "resolved_predictions": resolved_count,
            "pending_predictions": pending_count,
            "win_rate_pct": round(win_rate, 2),
            "accuracy_pct": round(acc_pct, 2),
            "target_1_hit_rate_pct": round((t1_count / resolved_count) * 100.0, 2),
            "target_2_hit_rate_pct": round((t2_count / resolved_count) * 100.0, 2),
            "stop_hit_rate_pct": round((stop_count / resolved_count) * 100.0, 2),
            "average_return_pct": round(avg_ret, 2),
            "median_return_pct": round(med_ret, 2),
            "average_holding_period_days": 1.0,
            "sample_size_status": "VALID_SAMPLE" if resolved_count >= 10 else "SMALL_SAMPLE"
        }
    finally:
        if close_db:
            db.close()
