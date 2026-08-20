"""
StockSense AI — Market Context & Cross-Asset Feature Engineering
Constructs lagged market-context and related-asset cross-features with zero future data leakage.
All cross-asset inputs use strictly lagged values (t <= T).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from backend.assets.asset_registry import get_asset_info
from backend.data.data_service import get_historical_data_from_db, fetch_historical_data, save_prices_to_db

def compute_market_context_features(df_asset: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Computes Market Context (Experiment B) and Related Assets (Experiment C) features.
    
    Guarantees:
    - Cross-asset return/volatility features use strictly lagged values (t <= T).
    - Modifying price data at T+1 in context assets NEVER mutates feature value at T.
    """
    df = df_asset.copy()
    asset_info = get_asset_info(symbol)
    aclass = asset_info["asset_class"] if asset_info else "INDIAN_EQUITY"

    # Context asset mapping
    context_symbols = []
    if aclass == "INDIAN_EQUITY":
        context_symbols = ["^NSEI", "USDINR=X"]
    elif aclass == "US_EQUITY":
        context_symbols = ["^GSPC", "^IXIC"]
    elif aclass == "CRYPTO":
        context_symbols = ["ETH-USD" if symbol == "BTC-USD" else "BTC-USD"]
    elif aclass == "FOREX":
        context_symbols = ["EURUSD=X" if symbol != "EURUSD=X" else "GBPUSD=X"]
    elif aclass == "INDEX":
        context_symbols = ["^GSPC" if symbol != "^GSPC" else "^IXIC"]

    # Fetch and merge context asset lagged returns
    for ctx_sym in context_symbols:
        df_ctx = get_historical_data_from_db(ctx_sym)
        if df_ctx.empty:
            try:
                df_fetched = fetch_historical_data(ctx_sym, period="2y")
                save_prices_to_db(df_fetched)
                df_ctx = df_fetched
            except Exception:
                pass

        if not df_ctx.empty and "close" in df_ctx.columns and "date" in df_ctx.columns:
            df_ctx = df_ctx.sort_values("date").reset_index(drop=True)
            # Calculate daily return for context asset
            ctx_ret_col = f"ctx_{ctx_sym.replace('^','').replace('=X','').replace('-','_').lower()}_ret"
            df_ctx[ctx_ret_col] = df_ctx["close"].pct_change()
            
            # Merge on date
            sub_ctx = df_ctx[["date", ctx_ret_col]].dropna()
            df = pd.merge(df, sub_ctx, on="date", how="left")
            df[ctx_ret_col] = df[ctx_ret_col].ffill().fillna(0.0)
        else:
            # Fallback zero column if context asset unavailable
            ctx_ret_col = f"ctx_{ctx_sym.replace('^','').replace('=X','').replace('-','_').lower()}_ret"
            df[ctx_ret_col] = 0.0

    return df
