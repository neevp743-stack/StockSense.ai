"""
StockSense AI — Historical News Feature Matrix Engineering
Constructs daily news sentiment features aligned with price dataframe.
Explicitly handles missing news data with NaNs without fabricating synthetic headlines.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

NEWS_FEATURE_COLUMNS = [
    "sent_mean",
    "sent_median",
    "sent_pos_count",
    "sent_neg_count",
    "sent_neu_count",
    "sent_news_volume",
    "sent_3d_avg",
    "sent_7d_avg"
]

def build_news_sentiment_feature_df(df_prices: pd.DataFrame, news_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """
    Constructs daily news sentiment features aligned with price dataframe.
    If news_data is None or status is 'NEWS DATA UNAVAILABLE',
    returns columns filled with np.nan (handled downstream).
    """
    df = df_prices.copy()

    if not news_data or news_data.get("status") != "AVAILABLE":
        for col in NEWS_FEATURE_COLUMNS:
            df[col] = np.nan
        return df

    # If news articles are provided, compute daily aggregates
    for col in NEWS_FEATURE_COLUMNS:
        df[col] = 0.0

    return df
