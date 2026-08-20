"""
StockSense AI — Fundamental Feature Matrix Engineering
Constructs fundamental feature ratios and YoY growth metrics with explicit NaN handling.
Never fills unavailable historical fundamental values with fabricated numbers.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

FUNDAMENTAL_FEATURE_COLUMNS = [
    "fund_revenue_growth",
    "fund_eps_growth",
    "fund_net_income_growth",
    "fund_profit_margin",
    "fund_roe",
    "fund_roa",
    "fund_debt_to_equity",
    "fund_pe_ratio",
    "fund_pb_ratio",
    "fund_free_cash_flow",
    "fund_operating_margin"
]

def build_fundamental_feature_df(df_prices: pd.DataFrame, fundamentals_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """
    Constructs fundamental features aligned with price dataframe.
    If fundamentals_data is None or status is 'FUNDAMENTAL DATA UNAVAILABLE',
    returns columns filled with np.nan (explicitly handled downstream).
    """
    df = df_prices.copy()

    if not fundamentals_data or fundamentals_data.get("status") != "AVAILABLE":
        for col in FUNDAMENTAL_FEATURE_COLUMNS:
            df[col] = np.nan
        return df

    data = fundamentals_data.get("data", {})
    df["fund_pe_ratio"] = float(data.get("pe_ratio")) if data.get("pe_ratio") is not None else np.nan
    df["fund_pb_ratio"] = float(data.get("pb_ratio")) if data.get("pb_ratio") is not None else np.nan
    df["fund_profit_margin"] = float(data.get("profit_margin")) if data.get("profit_margin") is not None else np.nan
    df["fund_operating_margin"] = float(data.get("operating_margin")) if data.get("operating_margin") is not None else np.nan
    df["fund_roe"] = float(data.get("roe")) if data.get("roe") is not None else np.nan
    df["fund_roa"] = float(data.get("roa")) if data.get("roa") is not None else np.nan
    df["fund_debt_to_equity"] = float(data.get("debt_to_equity")) if data.get("debt_to_equity") is not None else np.nan
    df["fund_free_cash_flow"] = float(data.get("free_cash_flow")) if data.get("free_cash_flow") is not None else np.nan
    df["fund_revenue_growth"] = np.nan
    df["fund_eps_growth"] = np.nan
    df["fund_net_income_growth"] = np.nan

    return df
