"""
StockSense AI — Point-in-Time As-Of Feature Join Engine
Implements timestamp-safe backward merge_asof joins to align price, fundamental, and news data.
Guarantees zero future data leakage: information published at timestamp T_pub can ONLY be joined
to prediction rows where t >= T_pub.
"""

import pandas as pd
import numpy as np
from typing import Optional

def point_in_time_asof_join(
    df_base: pd.DataFrame, 
    df_extra: pd.DataFrame, 
    on_timestamp_col: str = "date",
    by_symbol_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Executes a strict backward as-of join using pandas.merge_asof.
    
    Parameters:
    - df_base: Main price/prediction dataframe sorted by date/timestamp.
    - df_extra: Fundamental or news feature dataframe sorted by availability date/timestamp.
    - on_timestamp_col: Date/timestamp column name to join on.
    - by_symbol_col: Optional symbol column to match exact asset.
    
    Returns:
    - Merged DataFrame where extra features are assigned strictly from available_timestamp <= base_timestamp.
    """
    if df_extra is None or df_extra.empty:
        return df_base.copy()

    df_b = df_base.copy()
    df_e = df_extra.copy()

    # Ensure date/timestamp format and sorting
    df_b[on_timestamp_col] = pd.to_datetime(df_b[on_timestamp_col])
    df_e[on_timestamp_col] = pd.to_datetime(df_e[on_timestamp_col])

    df_b = df_b.sort_values(on_timestamp_col).reset_index(drop=True)
    df_e = df_e.sort_values(on_timestamp_col).reset_index(drop=True)

    if by_symbol_col and by_symbol_col in df_b.columns and by_symbol_col in df_e.columns:
        merged = pd.merge_asof(
            df_b, 
            df_e, 
            on=on_timestamp_col, 
            by=by_symbol_col, 
            direction="backward"
        )
    else:
        merged = pd.merge_asof(
            df_b, 
            df_e, 
            on=on_timestamp_col, 
            direction="backward"
        )

    return merged
