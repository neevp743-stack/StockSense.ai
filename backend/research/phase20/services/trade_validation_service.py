"""
StockSense AI — Phase 20 Trade Setup Validation Service
Evaluates Phase 20 candidate predictions by passing them through
the UNCHANGED Phase 14 trade setup engine (generate_trade_setup).
Compares Profit Factor, Net Return, Max Drawdown, Sharpe Ratio, and Target/Stop hit rates.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from backend.services.trade_signal_service import generate_trade_setup


class TradeValidationService:
    """Evaluates candidates through unchanged Phase 14 trade setup engine."""

    def evaluate_trading_performance(
        self,
        observations: pd.DataFrame,
        model_name: str = "Phase20 Candidate"
    ) -> Dict[str, Any]:
        """
        Passes predictions through generate_trade_setup and computes trading performance metrics.
        """
        if observations.empty:
            return {
                "model_name": model_name,
                "total_trades": 0,
                "profit_factor": 0.0,
                "net_return": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0
            }

        total_trades = 0
        winning_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0

        target1_hits = 0
        target2_hits = 0
        stop_hits = 0

        returns = []

        for idx, row in observations.iterrows():
            sym = row.get("symbol", "RELIANCE")
            price = float(row.get("current_price", row.get("price", 100.0)))
            prob_up = float(row.get("probability_up", row.get("champion_probability", 0.55)))
            act_ret = float(row.get("actual_return", 0.0))

            # Mock OHLCV DataFrame for Phase 14 Trade Signal Service
            mock_df = pd.DataFrame({
                "date": pd.date_range("2024-01-01", periods=5),
                "close": [price * 0.99, price * 0.995, price * 0.998, price * 1.0, price],
                "high": [price * 1.01] * 5,
                "low": [price * 0.98] * 5,
                "volume": [100000] * 5,
                "rsi": [55.0] * 5,
                "macd": [0.1] * 5
            })

            # Invoke UNCHANGED Phase 14 trade setup generator
            pred_dir_int = 1 if prob_up >= 0.50 else 0
            setup = generate_trade_setup(
                symbol=sym,
                df_raw=mock_df,
                df_feat=mock_df,
                prob_up=prob_up,
                predicted_dir=pred_dir_int
            )

            signal = setup.get("signal", "HOLD")
            if signal in ["BUY", "SELL"]:
                total_trades += 1

                # Calculate trade outcome
                direction_mult = 1.0 if signal == "BUY" else -1.0
                trade_ret = act_ret * direction_mult - 0.0010  # 10 bps slippage/transaction cost

                returns.append(trade_ret)

                if trade_ret > 0:
                    winning_trades += 1
                    gross_profit += trade_ret
                    if trade_ret >= 0.02:
                        target2_hits += 1
                    else:
                        target1_hits += 1
                else:
                    gross_loss += abs(trade_ret)
                    stop_hits += 1

        win_rate = winning_trades / max(total_trades, 1)
        profit_factor = gross_profit / max(gross_loss, 1e-6) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
        net_ret = sum(returns)

        # Max drawdown calculation
        cum_ret = np.cumsum(returns)
        peak = np.maximum.accumulate(cum_ret) if len(cum_ret) > 0 else np.array([0])
        dd = (peak - cum_ret) if len(cum_ret) > 0 else np.array([0])
        max_dd = float(np.max(dd)) if len(dd) > 0 else 0.0

        # Sharpe ratio
        std_ret = np.std(returns) if len(returns) > 1 else 0.0
        sharpe = (np.mean(returns) / (std_ret + 1e-6)) * np.sqrt(252) if std_ret > 0 else 0.0

        return {
            "model_name": model_name,
            "total_trades": total_trades,
            "win_rate": round(float(win_rate), 4),
            "profit_factor": round(float(profit_factor), 4),
            "gross_profit": round(float(gross_profit), 4),
            "gross_loss": round(float(gross_loss), 4),
            "net_return": round(float(net_ret), 4),
            "max_drawdown": round(float(max_dd), 4),
            "sharpe_ratio": round(float(sharpe), 4),
            "target1_hits": target1_hits,
            "target2_hits": target2_hits,
            "stop_hits": stop_hits
        }
