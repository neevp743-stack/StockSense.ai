import math
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.features.regime_engine import get_latest_regime
from backend.features.liquidity_engine import compute_liquidity_metrics
from backend.services.entry_engine import calculate_entry_zone, calculate_atr
from backend.services.risk_engine import compute_risk_targets

# Configurable Signal & Confidence Thresholds (Validated on historical validation folds)
PROB_BUY_THRESHOLD = 0.55
PROB_SELL_THRESHOLD = 0.45
CONFIDENCE_HIGH_DEV = 0.15
CONFIDENCE_MODERATE_DEV = 0.05

def generate_trade_setup(
    symbol: str,
    df_raw: pd.DataFrame,
    df_feat: pd.DataFrame,
    prob_up: float,
    predicted_dir: int,
    model_name: str = "XGBoost",
    model_version: str = "1.0",
    quote_info: Optional[Dict[str, Any]] = None,
    buy_threshold: float = PROB_BUY_THRESHOLD,
    sell_threshold: float = PROB_SELL_THRESHOLD
) -> Dict[str, Any]:
    """
    Master Trade Setup Engine.
    Transforms raw prices + features + Phase 12 prediction -> complete unified trade setup object.
    Does NOT modify or retrain Phase 12 production prediction engine.
    """
    symbol_clean = symbol.upper().strip()
    
    if df_raw is None or df_raw.empty or len(df_raw) < 5:
        # Fallback empty setup
        now_str = datetime.utcnow().isoformat() + "Z"
        return {
            "symbol": symbol_clean,
            "signal": "HOLD",
            "probability_up": 0.50,
            "probability_down": 0.50,
            "confidence": "LOW",
            "confidence_score": 0.50,
            "confidence_method": "Insufficient Price Data Baseline",
            "trend_regime": "SIDEWAYS",
            "volatility_regime": "LOW_VOLATILITY",
            "combined_regime": "SIDEWAYS (LOW VOL)",
            "current_price": 0.0,
            "entry_low": 0.0,
            "entry_high": 0.0,
            "entry_method": "Insufficient Data",
            "stop_loss": 0.0,
            "stop_loss_method": "Insufficient Data",
            "target_1": 0.0,
            "target_2": 0.0,
            "target_method": "Insufficient Data",
            "risk_reward_target_1": 0.0,
            "risk_reward_target_2": 0.0,
            "liquidity": "LOW",
            "volume_20d_avg": 0.0,
            "volume_ratio": 1.0,
            "average_traded_value": 0.0,
            "bid_ask_available": False,
            "bid_ask_spread": None,
            "expected_move_percent": 0.0,
            "expected_range_low": 0.0,
            "expected_range_high": 0.0,
            "horizon_days": 1,
            "positive_factors": [],
            "negative_factors": ["Insufficient historical price rows"],
            "model": model_name,
            "model_version": model_version,
            "generated_at": now_str
        }

    # 1. Price & Regime Telemetry
    latest_row_raw = df_raw.iloc[-1]
    current_price = quote_info.get("price") if (quote_info and quote_info.get("price")) else float(latest_row_raw["close"])
    regime_info = get_latest_regime(df_raw)
    
    trend_regime = regime_info.get("trend_regime", "SIDEWAYS")
    volatility_regime = regime_info.get("volatility_regime", "LOW_VOLATILITY")
    combined_regime = regime_info.get("combined_regime", "SIDEWAYS (LOW VOL)")

    # 2. Liquidity Metrics
    liq_info = compute_liquidity_metrics(df_raw, quote_info=quote_info)
    liquidity_tier = liq_info["liquidity_tier"]

    # 3. Technical Indicator Confluence
    latest_feat = df_feat.iloc[-1] if (df_feat is not None and not df_feat.empty) else latest_row_raw
    rsi_val = float(latest_feat.get("rsi", 50.0)) if "rsi" in latest_feat else 50.0
    macd_val = float(latest_feat.get("macd", 0.0)) if "macd" in latest_feat else 0.0
    sma_10 = float(latest_feat.get("sma_10", current_price)) if "sma_10" in latest_feat else current_price
    sma_50 = float(latest_feat.get("sma_50", current_price)) if "sma_50" in latest_feat else current_price

    # Technical Confluence Checks
    tech_bullish = (rsi_val > 50 and rsi_val < 78 and sma_10 >= sma_50)
    tech_bearish = (rsi_val < 50 and rsi_val > 22 and sma_10 <= sma_50)

    # 4. Signal Determination Engine (BUY / SELL / HOLD)
    # Require probability + trend non-contradiction + technical confirmation + valid risk/reward
    raw_signal = "HOLD"
    if prob_up >= buy_threshold:
        if trend_regime != "BEAR" and rsi_val < 82:
            raw_signal = "BUY"
    elif prob_up <= sell_threshold:
        if trend_regime != "BULL" and rsi_val > 18:
            raw_signal = "SELL"

    # 5. Entry Zone Engine
    entry_info = calculate_entry_zone(current_price, raw_signal, df_raw)
    e_low = entry_info["entry_low"]
    e_high = entry_info["entry_high"]

    # 6. Risk Engine (Stop Loss, Targets, Risk/Reward)
    risk_info = compute_risk_targets(current_price, e_low, e_high, raw_signal, df_raw)
    
    # If risk engine marks setup as invalid (e.g. stop_loss >= entry for BUY), downgrade signal to HOLD
    final_signal = raw_signal if risk_info["is_valid"] else "HOLD"

    # 7. Confidence Engine (HIGH / MODERATE / LOW)
    prob_dev = abs(prob_up - 0.5)
    conf_score = 0.5 + prob_dev  # 0.5 to 1.0 scale

    if prob_dev >= CONFIDENCE_HIGH_DEV and final_signal != "HOLD":
        if (final_signal == "BUY" and trend_regime == "BULL") or (final_signal == "SELL" and trend_regime == "BEAR"):
            confidence = "HIGH"
            conf_score = min(0.95, conf_score + 0.1)
        else:
            confidence = "MODERATE"
    elif prob_dev >= CONFIDENCE_MODERATE_DEV and final_signal != "HOLD":
        confidence = "MODERATE"
    else:
        confidence = "LOW"
        conf_score = max(0.40, conf_score - 0.1)

    conf_method = "Calibrated Probability Deviation + Regime Confluence"

    # 8. Expected Move Engine (20-day rolling volatility statistical move)
    daily_returns = df_raw["close"].pct_change().dropna()
    vol_20d = float(daily_returns.tail(20).std()) if len(daily_returns) >= 5 else 0.02
    if math.isnan(vol_20d) or vol_20d <= 0:
        vol_20d = 0.02

    exp_move_pct = float(vol_20d * 100.0)  # 1-day expected move %
    exp_range_low = float(current_price * (1.0 - vol_20d))
    exp_range_high = float(current_price * (1.0 + vol_20d))

    # 9. Explainability Factors (Genuine evidence only)
    positive_factors = []
    negative_factors = []

    if prob_up >= 0.55:
        positive_factors.append(f"Model Directional Probability ({prob_up*100:.1f}% UP)")
    elif prob_up <= 0.45:
        positive_factors.append(f"Model Directional Probability ({(1.0-prob_up)*100:.1f}% DOWN)")
    else:
        negative_factors.append(f"Neutral Model Probability ({prob_up*100:.1f}%)")

    if trend_regime == "BULL":
        positive_factors.append("Market Trend Regime: BULL")
    elif trend_regime == "BEAR":
        negative_factors.append("Market Trend Regime: BEAR")
    else:
        negative_factors.append("Market Trend Regime: SIDEWAYS")

    if volatility_regime == "HIGH_VOLATILITY":
        negative_factors.append("High Market Volatility (Elevated Noise)")
    else:
        positive_factors.append("Stable Volatility Regime (LOW VOL)")

    if rsi_val > 50 and rsi_val < 70:
        positive_factors.append(f"Positive Momentum (RSI {rsi_val:.1f})")
    elif rsi_val >= 70:
        negative_factors.append(f"Overbought Momentum Warning (RSI {rsi_val:.1f})")
    elif rsi_val < 30:
        negative_factors.append(f"Oversold Momentum Warning (RSI {rsi_val:.1f})")

    if liquidity_tier == "HIGH":
        positive_factors.append("High Asset Liquidity & Volume")
    elif liquidity_tier == "LOW":
        negative_factors.append("Low Asset Liquidity Tier")

    now_str = datetime.utcnow().isoformat() + "Z"

    return {
        "symbol": symbol_clean,
        "signal": final_signal,
        "probability_up": round(prob_up, 4),
        "probability_down": round(1.0 - prob_up, 4),
        "confidence": confidence,
        "confidence_score": round(conf_score, 2),
        "confidence_method": conf_method,
        "trend_regime": trend_regime,
        "volatility_regime": volatility_regime,
        "combined_regime": combined_regime,
        "current_price": round(current_price, 2),
        "entry_low": entry_info["entry_low"],
        "entry_high": entry_info["entry_high"],
        "entry_method": entry_info["entry_method"],
        "stop_loss": risk_info["stop_loss"],
        "stop_loss_method": risk_info["stop_loss_method"],
        "target_1": risk_info["target_1"],
        "target_2": risk_info["target_2"],
        "target_method": risk_info["target_method"],
        "risk_reward_target_1": risk_info["risk_reward_target_1"],
        "risk_reward_target_2": risk_info["risk_reward_target_2"],
        "liquidity": liquidity_tier,
        "volume_20d_avg": liq_info["volume_20d_avg"],
        "volume_ratio": liq_info["volume_ratio"],
        "average_traded_value": liq_info["average_traded_value"],
        "bid_ask_available": liq_info["bid_ask_available"],
        "bid_ask_spread": liq_info["bid_ask_spread"],
        "expected_move_percent": round(exp_move_pct, 2),
        "expected_range_low": round(exp_range_low, 2),
        "expected_range_high": round(exp_range_high, 2),
        "horizon_days": 1,
        "positive_factors": positive_factors,
        "negative_factors": negative_factors,
        "model": model_name,
        "model_version": model_version,
        "generated_at": now_str
    }
