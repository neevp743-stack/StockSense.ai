import os
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import PROJECT_ROOT
from backend.features.liquidity_engine import compute_liquidity_metrics
from backend.services.entry_engine import calculate_entry_zone, calculate_atr
from backend.services.risk_engine import compute_risk_targets
from backend.services.trade_signal_service import generate_trade_setup
from backend.backtest.trade_setup_backtester import run_complete_trade_setup_backtest
from backend.tracking.paper_tracker import log_paper_setup, resolve_pending_paper_setups, get_paper_performance
from backend.db.database import SessionLocal
from backend.db.models import PaperPredictionRecord, StockPrice

client = TestClient(app)

def test_liquidity_engine_calculation():
    """Verify liquidity engine computes genuine volume statistics and tiers without fabricating bid/ask."""
    dates = pd.date_range("2023-01-01", periods=30)
    prices = [100.0 + i for i in range(30)]
    volumes = [1000000.0] * 30
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})

    res = compute_liquidity_metrics(df)
    assert res["liquidity_tier"] in ("HIGH", "MEDIUM", "LOW")
    assert res["volume_20d_avg"] == 1000000.0
    assert res["volume_ratio"] == 1.0
    assert res["average_traded_value"] > 0
    assert res["bid_ask_available"] is False
    assert res["bid_ask_spread"] is None

    # Test with quote info containing bid/ask
    quote = {"bid": 129.5, "ask": 130.5, "price": 130.0}
    res_quote = compute_liquidity_metrics(df, quote_info=quote)
    assert res_quote["bid_ask_available"] is True
    assert res_quote["bid_ask_spread"] > 0

def test_entry_engine_calculation():
    """Verify entry engine returns valid deterministic entry zones with entry_low <= entry_high."""
    dates = pd.date_range("2023-01-01", periods=30)
    prices = [100.0 + i*0.5 for i in range(30)]
    df = pd.DataFrame({"date": dates, "high": [p+1 for p in prices], "low": [p-1 for p in prices], "close": prices, "volume": 1000})

    buy_entry = calculate_entry_zone(115.0, "BUY", df)
    assert buy_entry["entry_low"] <= buy_entry["entry_high"]
    assert buy_entry["entry_high"] == 115.0

    sell_entry = calculate_entry_zone(115.0, "SELL", df)
    assert sell_entry["entry_low"] <= sell_entry["entry_high"]
    assert sell_entry["entry_low"] == 115.0

def test_risk_engine_stop_and_targets():
    """Verify risk engine stop loss, targets, risk/reward, and invalid setup rejection logic."""
    dates = pd.date_range("2023-01-01", periods=30)
    prices = [100.0 + i*0.5 for i in range(30)]
    df = pd.DataFrame({"date": dates, "high": [p+1 for p in prices], "low": [p-1 for p in prices], "close": prices, "volume": 1000})

    # BUY setup risk/reward
    res_buy = compute_risk_targets(115.0, 114.0, 115.0, "BUY", df)
    assert res_buy["is_valid"] is True
    assert res_buy["stop_loss"] < 114.0
    assert res_buy["target_1"] > 115.0
    assert res_buy["target_2"] > res_buy["target_1"]
    assert res_buy["risk_reward_target_1"] > 0

    # Invalid setup rejection (e.g. stop loss >= entry)
    res_inv = compute_risk_targets(115.0, 114.0, 115.0, "BUY", df, atr_multiplier_sl=-1.0)
    assert res_inv["is_valid"] is False

def test_trade_signal_service_schema():
    """Verify generate_trade_setup returns complete unified trade setup object matching Phase 14 schema."""
    dates = pd.date_range("2023-01-01", periods=40)
    prices = [100.0 + i*0.5 for i in range(40)]
    df_raw = pd.DataFrame({"date": dates, "open": prices, "high": [p+1 for p in prices], "low": [p-1 for p in prices], "close": prices, "volume": 500000})
    df_feat = df_raw.copy()
    df_feat["rsi"] = 62.0

    setup = generate_trade_setup("RELIANCE", df_raw, df_feat, prob_up=0.72, predicted_dir=1)

    required_keys = [
        "symbol", "signal", "probability_up", "probability_down", "confidence", "confidence_score",
        "confidence_method", "trend_regime", "volatility_regime", "combined_regime", "current_price",
        "entry_low", "entry_high", "entry_method", "stop_loss", "stop_loss_method", "target_1",
        "target_2", "target_method", "risk_reward_target_1", "risk_reward_target_2", "liquidity",
        "volume_20d_avg", "volume_ratio", "average_traded_value", "bid_ask_available",
        "expected_move_percent", "expected_range_low", "expected_range_high", "horizon_days",
        "positive_factors", "negative_factors", "model", "model_version", "generated_at"
    ]
    for key in required_keys:
        assert key in setup, f"Missing key '{key}' in trade setup schema."

    assert setup["signal"] in ("BUY", "SELL", "HOLD")
    assert setup["confidence"] in ("HIGH", "MODERATE", "LOW")
    assert setup["entry_low"] <= setup["entry_high"]

def test_complete_trade_setup_backtest():
    """Verify run_complete_trade_setup_backtest computes setup outcomes, net returns, and ambiguous candle handling."""
    dates = pd.date_range("2023-01-01", periods=60)
    prices = [100.0 + (i%5)*2.0 + i*0.2 for i in range(60)]
    df_raw = pd.DataFrame({"date": dates, "open": prices, "high": [p+2 for p in prices], "low": [p-2 for p in prices], "close": prices, "volume": 100000})
    probs = np.array([0.65]*60)

    res = run_complete_trade_setup_backtest(df_raw, probs)
    assert "number_of_setups" in res
    assert "number_of_trades" in res
    assert "win_rate_pct" in res
    assert "average_net_return_pct" in res
    assert "ambiguous_count" in res
    assert res["estimated_costs_pct"] > 0

def test_transaction_cost_deduction():
    """Verify net return is less than or equal to gross return when costs are applied."""
    dates = pd.date_range("2023-01-01", periods=50)
    prices = [100.0 + i*0.3 for i in range(50)]
    df_raw = pd.DataFrame({"date": dates, "open": prices, "high": [p+1 for p in prices], "low": [p-1 for p in prices], "close": prices, "volume": 100000})
    probs = np.array([0.70]*50)

    res_zero = run_complete_trade_setup_backtest(df_raw, probs, transaction_cost=0.0, slippage=0.0)
    res_cost = run_complete_trade_setup_backtest(df_raw, probs, transaction_cost=0.001, slippage=0.0005)

    if res_cost["number_of_trades"] > 0:
        assert res_cost["average_net_return_pct"] <= res_zero["average_net_return_pct"]

def test_paper_tracker_logging_and_resolution():
    """Verify paper tracker logs predictions, prevents duplicates within 30s, and resolves outcomes."""
    db = SessionLocal()
    try:
        setup_data = {
            "symbol": "TEST_ASSET",
            "signal": "BUY",
            "probability_up": 0.70,
            "probability_down": 0.30,
            "confidence": "HIGH",
            "trend_regime": "BULL",
            "volatility_regime": "LOW_VOLATILITY",
            "combined_regime": "BULL (LOW VOL)",
            "current_price": 100.0,
            "entry_low": 99.5,
            "entry_high": 100.0,
            "stop_loss": 97.0,
            "target_1": 104.0,
            "target_2": 108.0,
            "risk_reward_target_1": 1.5,
            "risk_reward_target_2": 3.0,
            "model_version": "XGBoost v1.0",
            "horizon_days": 1
        }
        
        d1 = date(2025, 1, 1)
        d2 = date(2025, 1, 2)

        rec1 = log_paper_setup(setup_data, as_of_d=d1, pred_d=d2, db=db)
        assert rec1 is not None

        # Duplicate within 30s returns existing record
        rec2 = log_paper_setup(setup_data, as_of_d=d1, pred_d=d2, db=db)
        assert rec2.id == rec1.id

        # Insert stock price to resolve pending paper prediction
        sp1 = StockPrice(symbol="TEST_ASSET", date=d1, open=100.0, high=101.0, low=99.0, close=100.0, volume=1000)
        sp2 = StockPrice(symbol="TEST_ASSET", date=d2, open=100.0, high=105.0, low=99.5, close=104.5, volume=1000)
        db.add(sp1)
        db.add(sp2)
        db.commit()

        resolved = resolve_pending_paper_setups("TEST_ASSET", db=db)
        assert resolved >= 1

        perf = get_paper_performance("TEST_ASSET", db=db)
        assert perf["total_predictions"] >= 1
        assert perf["resolved_predictions"] >= 1

        # Clean up test asset
        db.query(PaperPredictionRecord).filter(PaperPredictionRecord.symbol == "TEST_ASSET").delete()
        db.query(StockPrice).filter(StockPrice.symbol == "TEST_ASSET").delete()
        db.commit()
    finally:
        db.close()

def test_api_trade_setup_endpoints():
    """Verify Phase 14 API endpoints return status 200 and valid schemas."""
    # 1. GET /api/assets/RELIANCE/trade-setup
    res1 = client.get("/api/assets/RELIANCE/trade-setup")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "signal" in data1
    assert "entry_low" in data1
    assert "stop_loss" in data1
    assert "target_1" in data1

    # 2. GET /api/assets/RELIANCE/trade-setup/backtest
    res2 = client.get("/api/assets/RELIANCE/trade-setup/backtest")
    assert res2.status_code == 200
    data2 = res2.json()
    assert "number_of_setups" in data2

    # 3. GET /api/assets/RELIANCE/trade-setup/history
    res3 = client.get("/api/assets/RELIANCE/trade-setup/history")
    assert res3.status_code == 200
    data3 = res3.json()
    assert "history" in data3

    # 4. GET /api/assets/RELIANCE/paper-performance
    res4 = client.get("/api/assets/RELIANCE/paper-performance")
    assert res4.status_code == 200
    data4 = res4.json()
    assert "total_predictions" in data4

def test_symbol_isolation_no_leakage():
    """Verify symbol responses are isolated between RELIANCE and AAPL."""
    from backend.data.data_service import ensure_historical_data_in_db
    db = SessionLocal()
    try:
        ensure_historical_data_in_db("RELIANCE", db=db)
        ensure_historical_data_in_db("AAPL", db=db)
    finally:
        db.close()

    res_rel = client.get("/api/assets/RELIANCE/trade-setup")
    res_aapl = client.get("/api/assets/AAPL/trade-setup")
    assert res_rel.status_code == 200
    assert res_aapl.status_code == 200
    assert res_rel.json()["symbol"] == "RELIANCE"
    assert res_aapl.json()["symbol"] == "AAPL"


def test_research_artifacts_exist():
    """Verify Phase 14 research JSON artifacts exist under backend/research/phase14/."""
    res_dir = os.path.join(PROJECT_ROOT, "backend", "research", "phase14")
    assert os.path.exists(res_dir)
    artifacts = [
        "trade_setup_baseline.json",
        "walk_forward_results.json",
        "backtest_results.json",
        "regime_performance.json",
        "cost_sensitivity.json",
        "paper_performance.json",
        "phase14_summary.json"
    ]
    for art in artifacts:
        p = os.path.join(res_dir, art)
        assert os.path.exists(p), f"Missing research artifact '{art}'."
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        assert d is not None
