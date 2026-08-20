import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from backend.config import DEFAULT_TRANSACTION_COST, DEFAULT_SLIPPAGE

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252) -> float:
    """Calculates annualized Sharpe Ratio."""
    if returns.empty or returns.std() == 0:
        return 0.0
    rf_daily = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
    excess_returns = returns - rf_daily
    mean = excess_returns.mean()
    std = excess_returns.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return float((mean / std) * np.sqrt(periods_per_year))

def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """Calculates maximum drawdown percentage."""
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_dd = float(drawdown.min())
    return abs(max_dd)

def calculate_cagr(start_val: float, end_val: float, num_days: int) -> float:
    """Calculates Compound Annual Growth Rate."""
    if start_val <= 0 or num_days <= 0:
        return 0.0
    years = num_days / 365.25
    if years <= 0:
        return 0.0
    return float(((end_val / start_val) ** (1.0 / years)) - 1.0)

def run_backtest(
    df_features: pd.DataFrame,
    predictions_prob: np.ndarray,
    initial_capital: float = 100000.0,
    prob_threshold: float = 0.55,
    allow_short: bool = False,
    transaction_cost: float = DEFAULT_TRANSACTION_COST,
    slippage: float = DEFAULT_SLIPPAGE
) -> Dict[str, Any]:
    """
    Executes backtest comparing:
    1. Buy & Hold Baseline
    2. Simple Prediction Strategy (Long on UP, Cash on DOWN)
    3. AI Threshold Strategy (Long when prob > threshold, Cash/Short otherwise)
    
    Includes trade logs, transaction costs, slippage, Max DD, CAGR, and Sharpe ratio.
    """
    if df_features.empty or len(df_features) < 10:
        return {"error": "Insufficient feature rows for backtesting."}

    df = df_features.copy().sort_values("date").reset_index(drop=True)
    n = len(df)
    dates = df["date"].tolist()
    closes = df["close"].values

    # Daily asset returns
    asset_returns = pd.Series(closes).pct_change().fillna(0.0)

    # 1. Buy & Hold Strategy
    bh_equity = [initial_capital]
    for r in asset_returns[1:]:
        bh_equity.append(bh_equity[-1] * (1.0 + r))
    bh_equity_series = pd.Series(bh_equity, index=df.index)
    bh_returns = bh_equity_series.pct_change().fillna(0.0)

    # 2. AI Strategy (Long / Cash default)
    ai_capital = initial_capital
    ai_equity = [initial_capital]
    position = 0  # 0 = Cash, 1 = Long, -1 = Short (if allowed)
    trades_count = 0
    winning_trades = 0
    active_days = 0

    trade_log = []

    for i in range(1, n):
        prob_up = predictions_prob[i - 1]  # Signal from yesterday (t-1) for today (t)
        prev_close = closes[i - 1]
        curr_close = closes[i]

        # Determine target position for today
        if prob_up >= prob_threshold:
            new_position = 1
        elif allow_short and prob_up <= (1.0 - prob_threshold):
            new_position = -1
        else:
            new_position = 0  # Cash

        # Position change -> incur transaction cost and slippage
        if new_position != position:
            trades_count += 1
            cost_pct = transaction_cost + slippage
            ai_capital *= (1.0 - cost_pct)
            
            trade_log.append({
                "date": dates[i].strftime("%Y-%m-%d") if hasattr(dates[i], "strftime") else str(dates[i]),
                "action": "ENTER_LONG" if new_position == 1 else ("ENTER_SHORT" if new_position == -1 else "EXIT_TO_CASH"),
                "price": curr_close,
                "capital": ai_capital
            })

        position = new_position

        # Apply daily return based on position
        daily_ret = asset_returns[i]
        if position != 0:
            active_days += 1
            trade_pnl = daily_ret if position == 1 else -daily_ret
            if trade_pnl > 0:
                winning_trades += 1
            ai_capital *= (1.0 + trade_pnl)

        ai_equity.append(ai_capital)

    ai_equity_series = pd.Series(ai_equity, index=df.index)
    ai_returns = ai_equity_series.pct_change().fillna(0.0)

    num_days = (dates[-1] - dates[0]).days if hasattr(dates[0], "days") or isinstance(dates[0], pd.Timestamp) or hasattr(dates[0], "year") else len(dates)
    if isinstance(dates[0], (pd.Timestamp, str)):
        num_days = (pd.to_datetime(dates[-1]) - pd.to_datetime(dates[0])).days

    # Metrics calculation
    bh_total_return = float((bh_equity[-1] - initial_capital) / initial_capital)
    ai_total_return = float((ai_equity[-1] - initial_capital) / initial_capital)

    bh_cagr = calculate_cagr(initial_capital, bh_equity[-1], num_days)
    ai_cagr = calculate_cagr(initial_capital, ai_equity[-1], num_days)

    bh_max_dd = calculate_max_drawdown(bh_equity_series)
    ai_max_dd = calculate_max_drawdown(ai_equity_series)

    bh_sharpe = calculate_sharpe_ratio(bh_returns)
    ai_sharpe = calculate_sharpe_ratio(ai_returns)

    win_rate = float(winning_trades / active_days) if active_days > 0 else 0.0

    return {
        "initial_capital": initial_capital,
        "final_buy_and_hold_capital": bh_equity[-1],
        "final_ai_strategy_capital": ai_equity[-1],
        "buy_and_hold": {
            "total_return_pct": bh_total_return * 100.0,
            "cagr_pct": bh_cagr * 100.0,
            "max_drawdown_pct": bh_max_dd * 100.0,
            "sharpe_ratio": bh_sharpe
        },
        "ai_strategy": {
            "total_return_pct": ai_total_return * 100.0,
            "cagr_pct": ai_cagr * 100.0,
            "max_drawdown_pct": ai_max_dd * 100.0,
            "sharpe_ratio": ai_sharpe,
            "trade_count": trades_count,
            "win_rate_pct": win_rate * 100.0,
            "allow_short": allow_short,
            "prob_threshold": prob_threshold
        },
        "equity_curve": [
            {
                "date": d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d),
                "buy_and_hold": round(bh_v, 2),
                "ai_strategy": round(ai_v, 2)
            }
            for d, bh_v, ai_v in zip(dates, bh_equity, ai_equity)
        ],
        "trade_log": trade_log[:30],  # Limit top 30 trades for API response
        "disclaimer": "Backtesting results reflect historical simulation and do NOT guarantee future trading performance."
    }

def run_monte_carlo_baseline(df_features: pd.DataFrame, runs: int = 100, initial_capital: float = 100000.0) -> Dict[str, Any]:
    """Runs a Monte Carlo random guess prediction baseline across N random runs."""
    if df_features.empty or len(df_features) < 10:
        return {"mean_return_pct": 0.0, "runs": 0}

    n = len(df_features)
    returns = []
    
    np.random.seed(42)
    for _ in range(runs):
        random_probs = np.random.uniform(0.0, 1.0, size=n)
        bt_res = run_backtest(df_features, random_probs, initial_capital=initial_capital, prob_threshold=0.50)
        returns.append(bt_res["ai_strategy"]["total_return_pct"])

    return {
        "mean_return_pct": float(np.mean(returns)),
        "std_return_pct": float(np.std(returns)),
        "min_return_pct": float(np.min(returns)),
        "max_return_pct": float(np.max(returns)),
        "runs": runs
    }
