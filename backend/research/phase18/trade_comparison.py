"""
StockSense AI — Trade Comparison Engine (Phase 18)
Passes Champion (Phase 12) and Challenger (Phase 17) shadow predictions through identical,
unmodified Phase 14 Trade Setup logic and compares signal distributions, win rates, and returns.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

from backend.services.trade_signal_service import generate_trade_setup
from backend.research.phase18.shadow_prediction_tracker import shadow_prediction_tracker

logger = logging.getLogger(__name__)


class TradeComparisonEngine:
    """
    Evaluates Phase 14 trade setup outcomes for Champion vs Challenger models.
    """

    def compare_trade_setups(self, df_raw: Optional[pd.DataFrame] = None, df_feat: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Runs paired resolved predictions through Phase 14 trade setup engine and evaluates performance.
        """
        pairs = shadow_prediction_tracker.get_paired_records(resolved_only=True)
        n = len(pairs)

        if n < 10:
            return {
                "sample_size": n,
                "status": "INSUFFICIENT_DATA",
                "reason": "insufficient_forward_validation_data",
                "champion": {"total_setups": 0, "signal_counts": {}},
                "challenger": {"total_setups": 0, "signal_counts": {}},
                "comparison": {}
            }

        champ_signals = {"BUY": 0, "SELL": 0, "HOLD": 0}
        chall_signals = {"BUY": 0, "SELL": 0, "HOLD": 0}

        champ_trades = []
        chall_trades = []

        transaction_cost = 0.001  # 0.1% per trade

        for p_champ, p_chall in pairs:
            # Dummy or mock minimal dataframes if not provided
            if df_raw is None or df_raw.empty:
                prices = [p_champ.current_price or 100.0] * 10
                df_r = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=10), "open": prices, "close": prices, "high": [p + 1.0 for p in prices], "low": [p - 1.0 for p in prices], "volume": [10000.0] * 10})
                df_f = df_r.copy()
            else:
                df_r = df_raw.copy()
                if "date" not in df_r.columns:
                    df_r = df_r.reset_index()
                    if "index" in df_r.columns:
                        df_r = df_r.rename(columns={"index": "date"})
                df_f = df_feat.copy() if df_feat is not None else df_r.copy()
                if "date" not in df_f.columns:
                    df_f = df_f.reset_index()
                    if "index" in df_f.columns:
                        df_f = df_f.rename(columns={"index": "date"})

            dir_champ_num = 1 if p_champ.predicted_direction == "UP" else 0
            dir_chall_num = 1 if p_chall.predicted_direction == "UP" else 0

            # Pass through Phase 14 trade setup
            setup_c = generate_trade_setup(p_champ.symbol, df_r, df_f, p_champ.probability_up, dir_champ_num)
            setup_ch = generate_trade_setup(p_chall.symbol, df_r, df_f, p_chall.probability_up, dir_chall_num)

            sig_c = setup_c.get("signal", "HOLD")
            sig_ch = setup_ch.get("signal", "HOLD")

            champ_signals[sig_c] = champ_signals.get(sig_c, 0) + 1
            chall_signals[sig_ch] = chall_signals.get(sig_ch, 0) + 1

            ret = p_champ.actual_return if p_champ.actual_return is not None else 0.0

            # Champion trade simulation
            if sig_c in ["BUY", "SELL"]:
                trade_ret_c = ret if sig_c == "BUY" else -ret
                net_ret_c = trade_ret_c - transaction_cost
                champ_trades.append({
                    "signal": sig_c,
                    "gross_return": trade_ret_c,
                    "net_return": net_ret_c,
                    "correct": (trade_ret_c > 0)
                })

            # Challenger trade simulation
            if sig_ch in ["BUY", "SELL"]:
                trade_ret_ch = ret if sig_ch == "BUY" else -ret
                net_ret_ch = trade_ret_ch - transaction_cost
                chall_trades.append({
                    "signal": sig_ch,
                    "gross_return": trade_ret_ch,
                    "net_return": net_ret_ch,
                    "correct": (trade_ret_ch > 0)
                })

        # Summary statistics
        def summarize_trades(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
            if not trades:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_net_return": 0.0,
                    "cumulative_net_return": 0.0,
                    "profit_factor": 0.0
                }
            wins = sum(1 for t in trades if t["correct"])
            win_rate = float(wins / len(trades))
            net_rets = [t["net_return"] for t in trades]
            avg_net = float(np.mean(net_rets))
            cum_net = float(np.sum(net_rets))

            gains = sum(t["net_return"] for t in trades if t["net_return"] > 0)
            losses = abs(sum(t["net_return"] for t in trades if t["net_return"] < 0))
            pf = float(gains / losses) if losses > 0 else (99.0 if gains > 0 else 0.0)

            return {
                "total_trades": len(trades),
                "win_rate": win_rate,
                "avg_net_return": avg_net,
                "cumulative_net_return": cum_net,
                "profit_factor": pf
            }

        c_summary = summarize_trades(champ_trades)
        ch_summary = summarize_trades(chall_trades)

        return {
            "sample_size": n,
            "status": "EVALUATED",
            "champion": {
                "signal_distribution": champ_signals,
                "trade_performance": c_summary
            },
            "challenger": {
                "signal_distribution": chall_signals,
                "trade_performance": ch_summary
            },
            "comparison": {
                "win_rate_delta": ch_summary["win_rate"] - c_summary["win_rate"],
                "avg_return_delta": ch_summary["avg_net_return"] - c_summary["avg_net_return"],
                "profit_factor_delta": ch_summary["profit_factor"] - c_summary["profit_factor"]
            }
        }


trade_comparison_engine = TradeComparisonEngine()
