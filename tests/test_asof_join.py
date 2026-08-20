import pytest
import pandas as pd
import numpy as np
from backend.features.asof_join import point_in_time_asof_join

def test_asof_join_backward_only():
    df_prices = pd.DataFrame({
        "date": pd.date_range(start="2026-01-01", periods=5, freq="D"),
        "close": [100, 101, 102, 103, 104]
    })

    # Fundamental filing released on 2026-01-03
    df_fundamentals = pd.DataFrame({
        "date": [pd.Timestamp("2026-01-03")],
        "eps": [2.5]
    })

    merged = point_in_time_asof_join(df_prices, df_fundamentals, on_timestamp_col="date")

    # On Jan 1 and Jan 2 (before filing date), eps MUST be NaN
    assert pd.isna(merged.at[0, "eps"])
    assert pd.isna(merged.at[1, "eps"])

    # On Jan 3, Jan 4, Jan 5 (after filing date), eps MUST be 2.5
    assert merged.at[2, "eps"] == 2.5
    assert merged.at[3, "eps"] == 2.5
    assert merged.at[4, "eps"] == 2.5
