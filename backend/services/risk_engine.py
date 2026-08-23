import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from backend.services.entry_engine import calculate_atr

def compute_risk_targets(
    current_price: float,
    entry_low: float,
    entry_high: float,
    signal: str,
    df_history: pd.DataFrame,
    atr_multiplier_sl: float = 1.5,
    rr_target1: float = 1.5,
    rr_target2: float = 3.0,
    stop_method_choice: str = "ATR"
) -> Dict[str, Any]:
    """
    Computes stop loss, target 1, target 2, and risk/reward metrics.
    Rejects setups where risk <= 0 or invalid price/stop relationships.
    """
    entry_mid = (entry_low + entry_high) / 2.0 if (entry_low > 0 and entry_high > 0) else current_price

    if signal == "HOLD" or current_price <= 0 or entry_mid <= 0:
        return {
            "stop_loss": round(current_price * 0.95, 2),
            "stop_loss_method": "Neutral Baseline",
            "target_1": round(current_price * 1.05, 2),
            "target_2": round(current_price * 1.10, 2),
            "target_method": "Neutral Baseline",
            "risk_reward_target_1": 1.0,
            "risk_reward_target_2": 2.0,
            "is_valid": False,
            "rejection_reason": "HOLD signal or invalid baseline price"
        }

    atr = calculate_atr(df_history, period=14)
    
    # 1. Recent Structure High/Low
    if df_history is not None and not df_history.empty and len(df_history) >= 10:
        recent = df_history.iloc[-20:]
        recent_low = float(recent["low"].min())
        recent_high = float(recent["high"].max())
    else:
        recent_low = current_price * 0.95
        recent_high = current_price * 1.05

    # 2. Stop Loss Calculation
    if stop_method_choice == "Structure" and len(df_history) >= 10:
        if signal == "BUY":
            sl_cand = min(recent_low, entry_low - 0.5 * atr)
            stop_loss = min(sl_cand, entry_low - 0.001 * entry_low)
            stop_loss_method = "Structure/Support Level + ATR Buffer"
        else: # SELL
            sl_cand = max(recent_high, entry_high + 0.5 * atr)
            stop_loss = max(sl_cand, entry_high + 0.001 * entry_high)
            stop_loss_method = "Structure/Resistance Level + ATR Buffer"
    else:
        # Default ATR-based stop loss
        if signal == "BUY":
            stop_loss = entry_low - (atr * atr_multiplier_sl)
            stop_loss_method = f"ATR Volatility ({atr_multiplier_sl}x ATR)"
        else: # SELL
            stop_loss = entry_high + (atr * atr_multiplier_sl)
            stop_loss_method = f"ATR Volatility ({atr_multiplier_sl}x ATR)"

    # 3. Validation Rules
    if signal == "BUY":
        risk = entry_mid - stop_loss
        if stop_loss >= entry_low or risk <= 0:
            return {
                "stop_loss": round(entry_low * 0.95, 2),
                "stop_loss_method": "Rejected Invalid Risk",
                "target_1": round(entry_mid * 1.05, 2),
                "target_2": round(entry_mid * 1.10, 2),
                "target_method": "Rejected Invalid Risk",
                "risk_reward_target_1": 0.0,
                "risk_reward_target_2": 0.0,
                "is_valid": False,
                "rejection_reason": "BUY stop_loss must be strictly less than entry"
            }
        
        # Targets for BUY
        target_1 = entry_mid + (risk * rr_target1)
        target_2 = entry_mid + (risk * rr_target2)
        if len(df_history) >= 10 and recent_high > entry_mid and recent_high < target_2:
            # Align target_1 or target_2 with key resistance if reasonable
            target_1 = max(recent_high, entry_mid + risk * 1.2)
            target_2 = target_1 + (risk * 1.5)
            target_method = "Resistance Confluence + Risk Multiple"
        else:
            target_method = f"Risk Multiple ({rr_target1}x / {rr_target2}x R)"

        reward_1 = target_1 - entry_mid
        reward_2 = target_2 - entry_mid

    else: # SELL
        risk = stop_loss - entry_mid
        if stop_loss <= entry_high or risk <= 0:
            return {
                "stop_loss": round(entry_high * 1.05, 2),
                "stop_loss_method": "Rejected Invalid Risk",
                "target_1": round(entry_mid * 0.95, 2),
                "target_2": round(entry_mid * 0.90, 2),
                "target_method": "Rejected Invalid Risk",
                "risk_reward_target_1": 0.0,
                "risk_reward_target_2": 0.0,
                "is_valid": False,
                "rejection_reason": "SELL stop_loss must be strictly greater than entry"
            }

        # Targets for SELL
        target_1 = entry_mid - (risk * rr_target1)
        target_2 = entry_mid - (risk * rr_target2)
        if len(df_history) >= 10 and recent_low < entry_mid and recent_low > target_2:
            target_1 = min(recent_low, entry_mid - risk * 1.2)
            target_2 = target_1 - (risk * 1.5)
            target_method = "Support Confluence + Risk Multiple"
        else:
            target_method = f"Risk Multiple ({rr_target1}x / {rr_target2}x R)"

        reward_1 = entry_mid - target_1
        reward_2 = entry_mid - target_2

    rr_1 = float(reward_1 / risk) if risk > 0 else 0.0
    rr_2 = float(reward_2 / risk) if risk > 0 else 0.0

    return {
        "stop_loss": round(float(stop_loss), 2),
        "stop_loss_method": stop_loss_method,
        "target_1": round(float(target_1), 2),
        "target_2": round(float(target_2), 2),
        "target_method": target_method,
        "risk_reward_target_1": round(rr_1, 2),
        "risk_reward_target_2": round(rr_2, 2),
        "is_valid": True,
        "rejection_reason": None
    }
