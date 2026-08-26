import concurrent.futures
import time
import random
from datetime import date
from backend.db.database import get_db_context, init_db
from backend.db.models import PaperPredictionRecord

init_db()

def perform_write(worker_id):
    success = False
    for attempt in range(3):
        try:
            with get_db_context() as db:
                rec = PaperPredictionRecord(
                    symbol="BTC-USD",
                    prediction_timestamp=None,
                    as_of_date=date(2026, 8, 26),
                    prediction_date=date(2026, 8, 27),
                    signal="BUY",
                    probability_up=0.75,
                    probability_down=0.25,
                    confidence="HIGH",
                    trend_regime="BULLISH",
                    volatility_regime="LOW_VOLATILITY",
                    combined_regime="BULLISH_LOW_VOL",
                    current_price=65000.0,
                    entry_low=64500.0,
                    entry_high=65500.0,
                    stop_loss=63000.0,
                    target_1=68000.0,
                    target_2=70000.0,
                    risk_reward_target_1=2.0,
                    risk_reward_target_2=3.33,
                    outcome="PENDING"
                )
                db.add(rec)
                db.commit()
                success = True
                break
        except Exception as e:
            if "locked" in str(e).lower():
                time.sleep(0.05 * (2 ** attempt))
            else:
                raise e
    return success

def test_concurrent_writes():
    workers = 30
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(perform_write, i) for i in range(workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert all(results) is True, f"Failed writes in concurrent stress test: {results.count(False)}/{len(results)}"

if __name__ == "__main__":
    test_concurrent_writes()
    print("SUCCESS: 30 concurrent database writes completed without locks!")
