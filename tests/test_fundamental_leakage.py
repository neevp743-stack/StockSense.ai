import pytest
import pandas as pd
import numpy as np
from backend.features.asof_join import point_in_time_asof_join

def test_fundamental_leakage_future_revision():
    df_prices = pd.DataFrame({
        "date": pd.date_range(start="2026-01-01", periods=10, freq="D"),
        "close": [100 + i for i in range(10)]
    })

    df_fund1 = pd.DataFrame({
        "date": [pd.Timestamp("2026-01-05")],
        "revenue": [1000.0]
    })

    m1 = point_in_time_asof_join(df_prices, df_fund1, on_timestamp_col="date")
    val_before = m1.at[3, "revenue"]  # Jan 4 (before Jan 5 filing)
    assert pd.isna(val_before)

    # Tamper with future filing on Jan 8
    df_fund2 = pd.DataFrame({
        "date": [pd.Timestamp("2026-01-05"), pd.Timestamp("2026-01-08")],
        "revenue": [1000.0, 5000.0]
    })

    m2 = point_in_time_asof_join(df_prices, df_fund2, on_timestamp_col="date")
    val_after = m2.at[3, "revenue"]

    # Jan 4 value must remain NaN regardless of Jan 8 revision
    assert pd.isna(val_after)
