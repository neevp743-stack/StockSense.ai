import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from backend.features.feature_engine import compute_features_and_target
from backend.services.trade_signal_service import generate_trade_setup
from backend.config import DEFAULT_TRANSACTION_COST, DEFAULT_SLIPPAGE

def run_complete_trade_setup_backtest(
    df_raw: pd.DataFrame,
    predictions_prob: np.ndarray,
    initial_capital: float = 100000.0,
    max_holding_days: int = 5,
    transaction_cost: float = DEFAULT_TRANSACTION_COST,
    slippage: float = DEFAULT_SLIPPAGE,
    buy_threshold: float = 0.55,
    sell_threshold: float = 0.45
) -> Dict[str, Any]:
    """
    Simulates complete trade setup execution over out-of-sample historical OHLC data.
    Enforces conservative intrabar candle ambiguity rule: if stop & target are hit in the same candle,
    it is marked AMBIGUOUS and counted conservatively as a stop loss.
    Calculates gross returns, estimated transaction costs, net returns, MFE, MAE, and regime breakdowns.
    """
    if df_raw is None or df_raw.empty or len(df_raw) < 30 or len(predictions_prob) < 30:
        return {"error": "Insufficient dataset rows for complete trade setup backtesting."}

    df_feat = compute_features_and_target(df_raw)
    df_clean = df_raw.sort_values("date").reset_index(drop=True)
    n = min(len(df_clean), len(predictions_prob))

    setups_log = []
    regime_outcomes = {
        "BULL": {"trades": 0, "wins": 0, "net_return": 0.0},
        "BEAR": {"trades": 0, "wins": 0, "net_return": 0.0},
        "SIDEWAYS": {"trades": 0, "wins": 0, "net_return": 0.0},
        "HIGH_VOLATILITY": {"trades": 0, "wins": 0, "net_return": 0.0},
        "LOW_VOLATILITY": {"trades": 0, "wins": 0, "net_return": 0.0}
    }

    signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
    total_setups = 0
    trade_returns_net = []
    trade_returns_gross = []
    holding_periods = []
    mfes = []
    maes = []

    target1_hits = 0
    target2_hits = 0
    stop_hits = 0
    ambiguous_count = 0
    expired_holds = 0

    capital = initial_capital
    cost_per_trade_pct = transaction_cost + slippage

    step_size = 2 if n > 250 else 1
    # Evaluate each day t (signal generated at close of day t for trade execution from t+1)
    for i in range(20, n - max_holding_days - 1, step_size):
        total_setups += 1
        df_sub_raw = df_clean.iloc[: i + 1]
        df_sub_feat = df_feat.iloc[: i + 1] if len(df_feat) >= i + 1 else df_sub_raw

        prob_up = float(predictions_prob[i])
        pred_dir = 1 if prob_up >= 0.50 else 0
        symbol_name = df_clean.get("symbol", pd.Series(["ASSET"])).iloc[0]

        setup = generate_trade_setup(
            symbol=str(symbol_name),
            df_raw=df_sub_raw,
            df_feat=df_sub_feat,
            prob_up=prob_up,
            predicted_dir=pred_dir,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold
        )


        sig = setup["signal"]
        signal_counts[sig] = signal_counts.get(sig, 0) + 1

        if sig == "HOLD":
            continue

        entry_price = setup["entry_high"] if sig == "BUY" else setup["entry_low"]
        stop_loss = setup["stop_loss"]
        target_1 = setup["target_1"]
        target_2 = setup["target_2"]
        trend_reg = setup["trend_regime"]
        vol_reg = setup["volatility_regime"]

        # Track outcome over next max_holding_days candles
        future_candles = df_clean.iloc[i + 1 : i + 1 + max_holding_days]
        outcome = "EXPIRED_HOLD"
        exit_price = entry_price
        days_held = 0
        mfe_pct = 0.0
        mae_pct = 0.0

        for f_idx, (_, candle) in enumerate(future_candles.iterrows(), 1):
            c_high = float(candle["high"])
            c_low = float(candle["low"])
            c_close = float(candle["close"])
            days_held = f_idx

            if sig == "BUY":
                curr_mfe = ((c_high - entry_price) / entry_price) * 100.0
                curr_mae = ((entry_price - c_low) / entry_price) * 100.0
                mfe_pct = max(mfe_pct, curr_mfe)
                mae_pct = max(mae_pct, curr_mae)

                hit_stop = c_low <= stop_loss
                hit_t1 = c_high >= target_1
                hit_t2 = c_high >= target_2

                if hit_stop and (hit_t1 or hit_t2):
                    outcome = "AMBIGUOUS"
                    exit_price = stop_loss
                    ambiguous_count += 1
                    break
                elif hit_t2:
                    outcome = "TARGET_2_HIT"
                    exit_price = target_2
                    target2_hits += 1
                    break
                elif hit_t1:
                    outcome = "TARGET_1_HIT"
                    exit_price = target_1
                    target1_hits += 1
                    break
                elif hit_stop:
                    outcome = "STOP_HIT"
                    exit_price = stop_loss
                    stop_hits += 1
                    break
            else: # SELL
                curr_mfe = ((entry_price - c_low) / entry_price) * 100.0
                curr_mae = ((c_high - entry_price) / entry_price) * 100.0
                mfe_pct = max(mfe_pct, curr_mfe)
                mae_pct = max(mae_pct, curr_mae)

                hit_stop = c_high >= stop_loss
                hit_t1 = c_low <= target_1
                hit_t2 = c_low <= target_2

                if hit_stop and (hit_t1 or hit_t2):
                    outcome = "AMBIGUOUS"
                    exit_price = stop_loss
                    ambiguous_count += 1
                    break
                elif hit_t2:
                    outcome = "TARGET_2_HIT"
                    exit_price = target_2
                    target2_hits += 1
                    break
                elif hit_t1:
                    outcome = "TARGET_1_HIT"
                    exit_price = target_1
                    target1_hits += 1
                    break
                elif hit_stop:
                    outcome = "STOP_HIT"
                    exit_price = stop_loss
                    stop_hits += 1
                    break

        if outcome == "EXPIRED_HOLD":
            exit_price = float(future_candles.iloc[-1]["close"])
            expired_holds += 1

        # Calculate gross & net return
        if sig == "BUY":
            raw_ret = (exit_price - entry_price) / entry_price
        else:
            raw_ret = (entry_price - exit_price) / entry_price

        gross_ret_pct = raw_ret * 100.0
        net_ret_pct = (raw_ret - cost_per_trade_pct) * 100.0

        trade_returns_gross.append(gross_ret_pct)
        trade_returns_net.append(net_ret_pct)
        holding_periods.append(days_held)
        mfes.append(mfe_pct)
        maes.append(mae_pct)

        # Update regime outcomes
        is_win = (net_ret_pct > 0)
        for r_k in [trend_reg, vol_reg]:
            if r_k in regime_outcomes:
                regime_outcomes[r_k]["trades"] += 1
                if is_win:
                    regime_outcomes[r_k]["wins"] += 1
                regime_outcomes[r_k]["net_return"] += net_ret_pct

        setups_log.append({
            "date": str(df_clean["date"].iloc[i]),
            "signal": sig,
            "probability": prob_up,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "outcome": outcome,
            "days_held": days_held,
            "gross_return_pct": round(gross_ret_pct, 2),
            "net_return_pct": round(net_ret_pct, 2)
        })

    # Summary Metrics
    total_trades = len(trade_returns_net)
    if total_trades > 0:
        winning_trades = sum(1 for r in trade_returns_net if r > 0)
        losing_trades = sum(1 for r in trade_returns_net if r <= 0)
        win_rate = float(winning_trades / total_trades) * 100.0
        loss_rate = float(losing_trades / total_trades) * 100.0
        avg_ret_net = float(np.mean(trade_returns_net))
        median_ret_net = float(np.median(trade_returns_net))
        avg_ret_gross = float(np.mean(trade_returns_gross))
        avg_hold = float(np.mean(holding_periods))
        avg_mfe = float(np.mean(mfes))
        avg_mae = float(np.mean(maes))

        gross_gains = sum(r for r in trade_returns_net if r > 0)
        gross_losses = abs(sum(r for r in trade_returns_net if r < 0))
        profit_factor = float(gross_gains / gross_losses) if gross_losses > 0 else (99.0 if gross_gains > 0 else 0.0)

        # Equity Curve and Max Drawdown calculation
        cum_equity = np.cumprod(1.0 + (np.array(trade_returns_net) / 100.0))
        peak = np.maximum.accumulate(cum_equity)
        drawdown = (cum_equity - peak) / peak
        max_dd = float(abs(np.min(drawdown))) * 100.0 if len(drawdown) > 0 else 0.0
    else:
        win_rate = 0.0
        loss_rate = 0.0
        avg_ret_net = 0.0
        median_ret_net = 0.0
        avg_ret_gross = 0.0
        avg_hold = 0.0
        avg_mfe = 0.0
        avg_mae = 0.0
        profit_factor = 0.0
        max_dd = 0.0

    return {
        "number_of_setups": total_setups,
        "number_of_trades": total_trades,
        "signal_distribution": signal_counts,
        "win_rate_pct": round(win_rate, 2),
        "loss_rate_pct": round(loss_rate, 2),
        "target_1_hit_rate_pct": round(float(target1_hits / total_trades * 100.0), 2) if total_trades > 0 else 0.0,
        "target_2_hit_rate_pct": round(float(target2_hits / total_trades * 100.0), 2) if total_trades > 0 else 0.0,
        "stop_loss_rate_pct": round(float(stop_hits / total_trades * 100.0), 2) if total_trades > 0 else 0.0,
        "ambiguous_rate_pct": round(float(ambiguous_count / total_trades * 100.0), 2) if total_trades > 0 else 0.0,
        "ambiguous_count": ambiguous_count,
        "average_gross_return_pct": round(avg_ret_gross, 2),
        "estimated_costs_pct": round(cost_per_trade_pct * 100.0, 2),
        "average_net_return_pct": round(avg_ret_net, 2),
        "median_net_return_pct": round(median_ret_net, 2),
        "profit_factor": round(profit_factor, 2),
        "maximum_drawdown_pct": round(max_dd, 2),
        "average_holding_period_days": round(avg_hold, 1),
        "maximum_favorable_excursion_pct": round(avg_mfe, 2),
        "maximum_adverse_excursion_pct": round(avg_mae, 2),
        "regime_performance": regime_outcomes,
        "trade_log": setups_log[-20:],  # Recent 20 setups log
        "ambiguous_candle_rule": "CONSERVATIVE: Intrabar candle ambiguity counts as stop loss",
        "disclaimer": "Research backtest results simulate historical trade setups and do NOT guarantee future profitability."
    }
