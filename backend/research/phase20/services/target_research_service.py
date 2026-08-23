"""
StockSense AI — Phase 20 Target Research Service
Evaluates multi-horizon research targets:
- Target A (T+1 direction)
- Target B (T+3 direction)
- Target C (T+5 direction)
- Target D (Return Classification: UP/FLAT/DOWN)
- Target E (Risk-Adjusted Return Classification)
Ensures strictly future-shifted label generation without feature matrix contamination.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


class TargetResearchService:
    """Evaluates multi-horizon research targets on historical OHLCV series."""

    @staticmethod
    def generate_research_targets(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates research target labels on historical OHLCV data.
        Assumes df contains ['close', 'high', 'low', 'symbol'].
        """
        df_out = df.copy()

        # Sort chronologically per symbol
        if "symbol" in df_out.columns and "date" in df_out.columns:
            df_out = df_out.sort_values(["symbol", "date"]).reset_index(drop=True)

        def add_targets(group):
            g = group.copy()
            close = g["close"]

            # Target A: T+1 Direction (strictly future shifted -1)
            fwd_ret_1 = close.shift(-1) / close - 1.0
            g["target_a_t1_dir"] = (fwd_ret_1 > 0).astype(int)

            # Target B: T+3 Direction
            fwd_ret_3 = close.shift(-3) / close - 1.0
            g["target_b_t3_dir"] = (fwd_ret_3 > 0).astype(int)

            # Target C: T+5 Direction
            fwd_ret_5 = close.shift(-5) / close - 1.0
            g["target_c_t5_dir"] = (fwd_ret_5 > 0).astype(int)

            # Target D: Future Return Class (UP: >0.5%, DOWN: <-0.5%, FLAT: between)
            g["target_d_return_class"] = np.where(fwd_ret_1 > 0.005, 1, np.where(fwd_ret_1 < -0.005, 0, 2))

            # Target E: Risk-Adjusted Return Class (Return / Rolling Volatility)
            roll_vol = g["close"].pct_change().rolling(20).std()
            sharpe_fwd = fwd_ret_1 / (roll_vol.shift(-1) + 1e-6)
            g["target_e_risk_adj_class"] = np.where(sharpe_fwd > 0.5, 1, np.where(sharpe_fwd < -0.5, 0, 2))

            return g

        if "symbol" in df_out.columns:
            df_out = df_out.groupby("symbol", group_keys=False).apply(add_targets)
        else:
            df_out = add_targets(df_out)

        return df_out

    def evaluate_target_horizons(self, df_with_targets: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates predictability, balance, and autocorrelation across research targets.
        """
        results = {}
        for tgt_col in ["target_a_t1_dir", "target_b_t3_dir", "target_c_t5_dir", "target_d_return_class", "target_e_risk_adj_class"]:
            if tgt_col in df_with_targets.columns:
                valid = df_with_targets[tgt_col].dropna()
                counts = valid.value_counts().to_dict()
                balance = {str(k): round(float(v) / len(valid), 4) for k, v in counts.items()} if len(valid) > 0 else {}
                results[tgt_col] = {
                    "total_samples": int(len(valid)),
                    "class_distribution": balance,
                    "autocorrelation_lag1": round(float(valid.autocorr(lag=1)), 4) if len(valid) > 10 else 0.0
                }

        return {
            "research_targets_evaluated": list(results.keys()),
            "horizon_breakdown": results,
            "recommended_primary_target": "target_a_t1_dir"
        }
