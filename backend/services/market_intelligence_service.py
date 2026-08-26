"""
StockSense AI — Advanced Market Intelligence Service (Phase 21.5)
Provides causal computations for technical indicators, market structure,
liquidity sweeps, fair value gaps, order blocks, regimes, confluences, and setup parameters.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes trend, momentum, volatility, and volume indicators causally.
    Input df should have columns: open, high, low, close, volume.
    Returns a copy of df with indicator columns appended.
    """
    df = df.copy()
    if df.empty:
        return df

    # Standardize types
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype(float)

    # 1. EMAs & SMAs
    df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
    
    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()
    df["sma_200"] = df["close"].rolling(window=200).mean()

    # 2. RSI (Wilder's smoothing)
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, 1e-9)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # 3. MACD
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema_12 - ema_26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]

    # 4. True Range & ATR
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr_14"] = tr.ewm(alpha=1/14, adjust=False).mean()

    # 5. Bollinger Bands (20, 2)
    df["bb_middle"] = df["sma_20"]
    bb_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_middle"] + (2 * bb_std)
    df["bb_lower"] = df["bb_middle"] - (2 * bb_std)

    # 6. Volume metrics
    df["volume_sma"] = df["volume"].rolling(window=20).mean()
    df["relative_volume"] = df["volume"] / df["volume_sma"].replace(0.0, 1e-9)
    df["relative_volume"] = df["relative_volume"].fillna(1.0)

    # 7. VWAP
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    cum_vol = df["volume"].cumsum()
    df["vwap"] = (tp * df["volume"]).cumsum() / cum_vol.replace(0.0, 1e-9)
    df["vwap"] = df["vwap"].fillna(df["close"])

    return df

def analyze_market_structure_and_features(df_indicators: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes market structure, FVG, liquidity sweeps, OB, regimes, and confluence causally.
    Input df_indicators must be computed from calculate_indicators.
    Returns a dictionary of analysis metrics for the latest index (index -1).
    """
    if df_indicators.empty or len(df_indicators) < 15:
        return {}

    # Standardize to list of records
    records = df_indicators.to_dict(orient="records")
    n = len(records)
    
    # 1. Causal Swing Point & Structure Tracking
    # Window size: 5 left, 5 right -> swing points confirmed at index i - 5.
    left_win = 5
    right_win = 5
    
    swing_highs = [] # list of dicts: {"index": idx, "price": val, "type": "HH"/"LH"}
    swing_lows = []  # list of dicts: {"index": idx, "price": val, "type": "HL"/"LL"}
    
    trend = "RANGE"
    confidence = 50
    events = [] # list of dicts: {"event": "BOS"/"CHoCH", "direction": "BULL"/"BEAR", "index": idx, "price": val}

    # Running boundaries
    last_confirmed_high = None
    last_confirmed_low = None
    
    # Imbalance (FVG) and Order Block tracking lists
    bullish_fvgs = []  # list of dicts: {"upper": val, "lower": val, "index": idx, "mitigated": bool}
    bearish_fvgs = []  # list of dicts: {"upper": val, "lower": val, "index": idx, "mitigated": bool}
    bullish_obs = []   # list of dicts: {"upper": val, "lower": val, "index": idx, "mitigated": bool}
    bearish_obs = []   # list of dicts: {"upper": val, "lower": val, "index": idx, "mitigated": bool}
    
    sweeps = [] # list of dicts: {"direction": "BULLISH"/"BEARISH", "index": idx, "price": val}

    # Causal loop
    for i in range(10, n):
        row = records[i]
        
        # A. FVG Creation
        # Bullish FVG: Low of i > High of i - 2
        if records[i]["low"] > records[i-2]["high"]:
            bullish_fvgs.append({
                "upper": records[i]["low"],
                "lower": records[i-2]["high"],
                "index": i - 1,
                "mitigated": False
            })
        # Bearish FVG: High of i < Low of i - 2
        if records[i]["high"] < records[i-2]["low"]:
            bearish_fvgs.append({
                "upper": records[i-2]["low"],
                "lower": records[i]["high"],
                "index": i - 1,
                "mitigated": False
            })

        # B. FVG Mitigation check
        # Bullish FVG filled if close or low breaks below lower bound
        for fvg in bullish_fvgs:
            if not fvg["mitigated"] and i > fvg["index"] + 1:
                if row["close"] < fvg["lower"] or row["low"] < fvg["lower"]:
                    fvg["mitigated"] = True
        # Bearish FVG filled if close or high breaks above upper bound
        for fvg in bearish_fvgs:
            if not fvg["mitigated"] and i > fvg["index"] + 1:
                if row["close"] > fvg["upper"] or row["high"] > fvg["upper"]:
                    fvg["mitigated"] = True

        # C. Order Blocks candidates
        # Bullish OB: last down close body prior to strong up close (Close > previous High)
        if records[i-1]["close"] < records[i-1]["open"] and row["close"] > row["open"] and row["close"] > records[i-1]["high"]:
            bullish_obs.append({
                "upper": max(records[i-1]["close"], records[i-1]["open"]),
                "lower": records[i-1]["low"],
                "index": i - 1,
                "mitigated": False
            })
        # Bearish OB: last up close body prior to strong down close
        if records[i-1]["close"] > records[i-1]["open"] and row["close"] < row["open"] and row["close"] < records[i-1]["low"]:
            bearish_obs.append({
                "upper": records[i-1]["high"],
                "lower": min(records[i-1]["close"], records[i-1]["open"]),
                "index": i - 1,
                "mitigated": False
            })

        # D. OB Mitigation check
        for ob in bullish_obs:
            if not ob["mitigated"] and i > ob["index"]:
                if row["close"] < ob["lower"]:
                    ob["mitigated"] = True
        for ob in bearish_obs:
            if not ob["mitigated"] and i > ob["index"]:
                if row["close"] > ob["upper"]:
                    ob["mitigated"] = True

        # E. Swing points identification (confirmed at index i - right_win)
        confirm_idx = i - right_win
        
        # Swing High check
        target_high = records[confirm_idx]["high"]
        is_swing_high = True
        for offset in range(-left_win, right_win + 1):
            if records[confirm_idx + offset]["high"] > target_high:
                is_swing_high = False
                break
        if is_swing_high:
            sh_type = "HH"
            if swing_highs and target_high < swing_highs[-1]["price"]:
                sh_type = "LH"
            swing_highs.append({"index": confirm_idx, "price": target_high, "type": sh_type})
            last_confirmed_high = target_high

        # Swing Low check
        target_low = records[confirm_idx]["low"]
        is_swing_low = True
        for offset in range(-left_win, right_win + 1):
            if records[confirm_idx + offset]["low"] < target_low:
                is_swing_low = False
                break
        if is_swing_low:
            sl_type = "LL"
            if swing_lows and target_low > swing_lows[-1]["price"]:
                sl_type = "HL"
            swing_lows.append({"index": confirm_idx, "price": target_low, "type": sl_type})
            last_confirmed_low = target_low

        # F. Liquidity Sweeps
        if last_confirmed_high and row["high"] > last_confirmed_high and row["close"] < last_confirmed_high:
            # Bearish liquidity sweep (swept high and closed below)
            sweeps.append({"direction": "BEARISH", "index": i, "price": last_confirmed_high})
        if last_confirmed_low and row["low"] < last_confirmed_low and row["close"] > last_confirmed_low:
            # Bullish liquidity sweep (swept low and closed above)
            sweeps.append({"direction": "BULLISH", "index": i, "price": last_confirmed_low})

        # G. Structure Break (BOS / CHoCH) on Close Breaches
        if last_confirmed_high and row["close"] > last_confirmed_high:
            # Bullish Break
            direction = "BULL"
            event_type = "BOS" if trend == "BULLISH" else "CHoCH"
            trend = "BULLISH"
            confidence = min(100, confidence + 10)
            events.append({"event": event_type, "direction": direction, "index": i, "price": last_confirmed_high})
            # Reset boundary
            last_confirmed_high = None
        elif last_confirmed_low and row["close"] < last_confirmed_low:
            # Bearish Break
            direction = "BEAR"
            event_type = "BOS" if trend == "BEARISH" else "CHoCH"
            trend = "BEARISH"
            confidence = min(100, confidence + 10)
            events.append({"event": event_type, "direction": direction, "index": i, "price": last_confirmed_low})
            # Reset boundary
            last_confirmed_low = None
        else:
            # Decay confidence slightly in ranging
            confidence = max(30, confidence - 0.5)

    # 2. Extract final analysis for the last candle
    latest_row = records[-1]
    latest_price = latest_row["close"]

    # Retrieve last confirmations
    active_sh = swing_highs[-1] if swing_highs else {"price": latest_price, "type": "LH"}
    active_sl = swing_lows[-1] if swing_lows else {"price": latest_price, "type": "HL"}

    # Unmitigated FVG & OB Count
    unmit_bull_fvg = [f for f in bullish_fvgs if not f["mitigated"]]
    unmit_bear_fvg = [f for f in bearish_fvgs if not f["mitigated"]]
    unmit_bull_ob = [o for o in bullish_obs if not o["mitigated"]]
    unmit_bear_ob = [o for o in bearish_obs if not o["mitigated"]]

    latest_sweep = sweeps[-1] if sweeps else None
    
    # 3. Regime engine classification
    # Multiple variables: EMAs, ATR, RSI, MACD
    ema_bullish = latest_row["ema_9"] > latest_row["ema_21"] > latest_row["ema_50"] > latest_row["ema_200"]
    ema_bearish = latest_row["ema_9"] < latest_row["ema_21"] < latest_row["ema_50"] < latest_row["ema_200"]
    
    rsi_val = latest_row["rsi_14"]
    macd_val = latest_row["macd_line"]
    macd_sig = latest_row["macd_signal"]
    
    volatility_high = (latest_price > 0) and (latest_row["atr_14"] / latest_price > 0.03)  # >3% ATR
    volatility_low = (latest_price > 0) and (latest_row["atr_14"] / latest_price < 0.01)   # <1% ATR
    
    if ema_bullish and rsi_val > 50 and macd_val > macd_sig:
        regime = "TRENDING_BULLISH"
    elif ema_bearish and rsi_val < 50 and macd_val < macd_sig:
        regime = "TRENDING_BEARISH"
    elif volatility_high:
        regime = "HIGH_VOLATILITY"
    elif volatility_low:
        regime = "LOW_VOLATILITY"
    elif abs(rsi_val - 50) < 10:
        regime = "RANGING"
    else:
        regime = "TRANSITION"

    # 4. Confluence scoring engine
    conf_score = 0
    score_reasons = []
    score_penalties = []

    # Trend (Max 20)
    if regime == "TRENDING_BULLISH":
        conf_score += 20
        score_reasons.append("+ Bullish Exponential Moving Average (EMA) alignment (9 > 21 > 50 > 200)")
    elif regime == "TRENDING_BEARISH":
        score_penalties.append("- Bearish EMA alignment (9 < 21 < 50 < 200)")
    else:
        conf_score += 10
        score_reasons.append("+ Ranging / Neutral EMA crossover context")

    # Structure (Max 20)
    if trend == "BULLISH":
        conf_score += 20
        score_reasons.append(f"+ Bullish structural bias with confirmed CHoCH/BOS (HH/HL series, confidence: {int(confidence)}%)")
    elif trend == "BEARISH":
        score_penalties.append(f"- Bearish structural bias (LH/LL series, confidence: {int(confidence)}%)")
    else:
        conf_score += 10
        score_reasons.append("+ Side-bound ranging market structure")

    # Momentum (Max 15)
    if rsi_val > 50 and macd_val > macd_sig:
        conf_score += 15
        score_reasons.append(f"+ Positive momentum: RSI ({rsi_val:.1f}) > 50 & MACD line crossed above signal")
    elif rsi_val < 50 and macd_val < macd_sig:
        score_penalties.append(f"- Negative momentum: RSI ({rsi_val:.1f}) < 50 & MACD line crossed below signal")
    else:
        conf_score += 7
        score_reasons.append("+ Mixed / Neutral momentum oscillators")

    # Volatility (Max 10)
    if volatility_low:
        conf_score += 10
        score_reasons.append("+ Low volatility compression; potential for breakout expansion")
    elif volatility_high:
        score_penalties.append("- Elevated volatility; high risk of whipsaws")
    else:
        conf_score += 5
        score_reasons.append("+ Volatility parameters within normal parameters")

    # Volume (Max 10)
    if latest_row["relative_volume"] > 1.5:
        conf_score += 10
        score_reasons.append(f"+ Above average relative volume ({latest_row['relative_volume']:.1f}x) confirming direction")
    elif latest_row["relative_volume"] < 0.6:
        score_penalties.append(f"- Below average volume ({latest_row['relative_volume']:.1f}x); low participation")
    else:
        conf_score += 5
        score_reasons.append("+ Average volume participation")

    # Liquidity Sweep (Max 15)
    recent_sweep_bull = False
    recent_sweep_bear = False
    for sw in sweeps[-5:]:
        if sw["direction"] == "BULLISH":
            recent_sweep_bull = True
        elif sw["direction"] == "BEARISH":
            recent_sweep_bear = True
            
    if recent_sweep_bull:
        conf_score += 15
        score_reasons.append("+ Bullish liquidity sweep detected recently (swept low and closed high)")
    elif recent_sweep_bear:
        score_penalties.append("- Bearish liquidity sweep detected recently (swept high and closed low)")

    # Imbalances & OB Context (Max 10)
    if unmit_bull_fvg:
        conf_score += 5
        score_reasons.append(f"+ Presence of unmitigated Bullish Fair Value Gaps (FVG) below price")
    if unmit_bull_ob:
        conf_score += 5
        score_reasons.append(f"+ Support zone verified by unmitigated Bullish Order Blocks")
        
    if unmit_bear_fvg:
        score_penalties.append("- Presence of unmitigated Bearish Fair Value Gaps above price")
    if unmit_bear_ob:
        score_penalties.append("- Resistance zone verified by unmitigated Bearish Order Blocks")

    # Cap score
    conf_score = max(0, min(100, conf_score))

    # 5. Potential Setup Generation (Educational / Research)
    setup = {"bias": "NO QUALIFIED SETUP", "entry_zone": None, "stop_loss": None, "tp1": None, "tp2": None, "rr": 0.0, "reasons": []}
    atr = latest_row["atr_14"]
    
    if conf_score >= 70:
        setup["bias"] = "POTENTIAL LONG SETUP"
        stop_dist = max(1.5 * atr, latest_price * 0.015)
        stop_loss = latest_price - stop_dist
        
        if active_sl and latest_price > active_sl["price"] > stop_loss:
            stop_loss = active_sl["price"] - (0.5 * atr)
            
        entry_lower = latest_price - (0.3 * atr)
        entry_upper = latest_price + (0.1 * atr)
        
        tp1 = latest_price + (1.5 * stop_dist)
        tp2 = latest_price + (3.0 * stop_dist)
        
        rr = round((tp1 - latest_price) / max(1e-9, latest_price - stop_loss), 2)
        
        setup.update({
            "entry_zone": f"${entry_lower:,.2f} - ${entry_upper:,.2f}",
            "stop_loss": round(stop_loss, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "rr": rr,
            "reasons": score_reasons[:3]
        })
    elif conf_score <= 30:
        setup["bias"] = "POTENTIAL SHORT SETUP"
        stop_dist = max(1.5 * atr, latest_price * 0.015)
        stop_loss = latest_price + stop_dist
        
        if active_sh and latest_price < active_sh["price"] < stop_loss:
            stop_loss = active_sh["price"] + (0.5 * atr)
            
        entry_lower = latest_price - (0.1 * atr)
        entry_upper = latest_price + (0.3 * atr)
        
        tp1 = latest_price - (1.5 * stop_dist)
        tp2 = latest_price - (3.0 * stop_dist)
        
        rr = round((latest_price - tp1) / max(1e-9, stop_loss - latest_price), 2)
        
        setup.update({
            "entry_zone": f"${entry_lower:,.2f} - ${entry_upper:,.2f}",
            "stop_loss": round(stop_loss, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "rr": rr,
            "reasons": score_penalties[:3]
        })

    return {
        "price": latest_price,
        "indicators": {
            "ema_9": round(latest_row["ema_9"], 4),
            "ema_21": round(latest_row["ema_21"], 4),
            "ema_50": round(latest_row["ema_50"], 4),
            "ema_200": round(latest_row["ema_200"], 4),
            "sma_20": round(latest_row["sma_20"], 4),
            "sma_50": round(latest_row["sma_50"], 4),
            "sma_200": round(latest_row["sma_200"], 4),
            "rsi_14": round(rsi_val, 2),
            "macd_line": round(macd_val, 4),
            "macd_signal": round(macd_sig, 4),
            "macd_hist": round(latest_row["macd_hist"], 4),
            "atr_14": round(atr, 4),
            "bb_upper": round(latest_row["bb_upper"], 4),
            "bb_lower": round(latest_row["bb_lower"], 4),
            "vwap": round(latest_row["vwap"], 4),
            "relative_volume": round(latest_row["relative_volume"], 2)
        },
        "structure": {
            "trend": trend,
            "confidence": round(confidence, 1),
            "swing_high": round(active_sh["price"], 2),
            "swing_high_type": active_sh["type"],
            "swing_low": round(active_sl["price"], 2),
            "swing_low_type": active_sl["type"]
        },
        "liquidity": {
            "last_sweep_direction": latest_sweep["direction"] if latest_sweep else "NONE",
            "last_sweep_price": round(latest_sweep["price"], 2) if latest_sweep else 0.0,
            "unmitigated_bullish_fvgs": len(unmit_bull_fvg),
            "unmitigated_bearish_fvgs": len(unmit_bear_fvg),
            "unmitigated_bullish_obs": len(unmit_bull_ob),
            "unmitigated_bearish_obs": len(unmit_bear_ob)
        },
        "regime": regime,
        "confluence": {
            "score": conf_score,
            "reasons": score_reasons,
            "penalties": score_penalties
        },
        "setup": setup
    }


import time

# In-memory bounded cache for performance
ANALYSIS_CACHE = {}
CANDLES_CACHE = {}
CACHE_TTL = 15  # 15 seconds Cache TTL

def fetch_candles_dataframe(symbol: str, interval: str = "1d", limit: int = 300) -> Tuple[pd.DataFrame, str]:
    """
    Fetches raw OHLCV DataFrame from either Twelve Data REST or Yahoo Finance REST.
    Normalizes columns to date, open, high, low, close, volume.
    """
    sym_clean = symbol.upper().strip()
    if sym_clean == "BTCUSD":
        sym_clean = "BTC-USD"
    elif sym_clean == "SOLUSD":
        sym_clean = "SOL-USD"
    elif sym_clean == "XAUUSD":
        sym_clean = "XAU/USD"

    # Try cache first
    cache_key = f"{sym_clean}_{interval}_{limit}"
    cached = CANDLES_CACHE.get(cache_key)
    if cached and (time.time() - cached["cached_at"] < CACHE_TTL):
        return cached["df"], cached["provider"]

    # 1. Check if XAU/USD
    if sym_clean == "XAU/USD":
        from backend.data.providers.twelve_data_provider import TwelveDataProvider
        twelve_prov = TwelveDataProvider()
        
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1day",
            "1w": "1week",
            "1m": "1month"
        }
        td_interval = interval_map.get(interval, "1day")
        
        if twelve_prov.is_configured():
            api_key = twelve_prov._api_key
            url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={td_interval}&outputsize={limit}&apikey={api_key.strip()}"
            try:
                data = twelve_prov._fetch_json(url)
                if data and "values" in data:
                    rows = []
                    for v in data["values"]:
                        dt = pd.to_datetime(v.get("datetime"))
                        rows.append({
                            "date": dt,
                            "open": float(v.get("open", 0)),
                            "high": float(v.get("high", 0)),
                            "low": float(v.get("low", 0)),
                            "close": float(v.get("close", 0)),
                            "volume": float(v.get("volume", 0)),
                        })
                    df = pd.DataFrame(rows)
                    if not df.empty:
                        df = df.sort_values("date").reset_index(drop=True)
                        CANDLES_CACHE[cache_key] = {"df": df, "provider": "TWELVE_DATA", "cached_at": time.time()}
                        return df, "TWELVE_DATA"
            except Exception as e:
                logger.warning(f"Twelve Data time_series query failed: {e}")
                
        # Fallback for gold spot in yfinance is GC=F
        provider_symbol = "GC=F"
    else:
        # Standard symbol mapping
        from backend.assets.provider_symbol_mapper import get_provider_symbol
        provider_symbol = get_provider_symbol(sym_clean)

    # yfinance mapping
    period_map = {
        "1m": "1d",
        "5m": "5d",
        "15m": "7d",
        "30m": "30d",
        "1h": "60d",
        "4h": "120d",
        "1d": "2y",
        "1w": "5y",
        "1m": "5y"
    }
    period = period_map.get(interval, "2y")
    
    yf_interval_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "1h",
        "1d": "1d",
        "1w": "1wk",
        "1m": "1mo"
    }
    yf_interval = yf_interval_map.get(interval, "1d")

    try:
        import yfinance as yf
        ticker = yf.Ticker(provider_symbol)
        df_yf = ticker.history(period=period, interval=yf_interval)
        if df_yf.empty:
            return pd.DataFrame(), "YFINANCE"
            
        df_yf = df_yf.reset_index()
        time_col = "Date"
        if "Datetime" in df_yf.columns:
            time_col = "Datetime"
        elif "date" in df_yf.columns:
            time_col = "date"
            
        df_yf["date"] = pd.to_datetime(df_yf[time_col])
        
        column_map = {
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        }
        df_yf = df_yf.rename(columns=column_map)
        
        req_cols = ["date", "open", "high", "low", "close", "volume"]
        df_res = df_yf[req_cols].dropna(subset=["date", "close"])
        df_res = df_res.sort_values("date").reset_index(drop=True)
        
        if interval == "4h":
            df_res.set_index("date", inplace=True)
            df_res = df_res.resample("4h").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna()
            df_res.reset_index(inplace=True)
            
        CANDLES_CACHE[cache_key] = {"df": df_res, "provider": "YFINANCE", "cached_at": time.time()}
        return df_res, "YFINANCE"
    except Exception as e:
        logger.error(f"yfinance query failed for {provider_symbol}: {e}")
        return pd.DataFrame(), "YFINANCE"

def get_market_analysis(symbol: str, interval: str = "1d", limit: int = 300) -> Dict[str, Any]:
    """
    Aggregated entrypoint for frontend. Fetches, computes, and returns the cached analysis.
    """
    sym_clean = symbol.upper().strip()
    if sym_clean == "BTCUSD":
        sym_clean = "BTC-USD"
    elif sym_clean == "SOLUSD":
        sym_clean = "SOL-USD"
    elif sym_clean == "XAUUSD":
        sym_clean = "XAU/USD"

    cache_key = f"{sym_clean}_{interval}_{limit}"
    cached = ANALYSIS_CACHE.get(cache_key)
    if cached and (time.time() - cached["cached_at"] < CACHE_TTL):
        return cached["data"]

    # Fetch candles
    df, provider_name = fetch_candles_dataframe(sym_clean, interval, limit)
    if df.empty:
        return {"error": f"Failed to fetch market data for {sym_clean}"}

    # Compute indicators
    df_ind = calculate_indicators(df)
    
    # Compute structure and confluences
    analysis = analyze_market_structure_and_features(df_ind)
    
    # Add candles for chart mapping
    candles_list = []
    for r in df_ind.to_dict(orient="records"):
        # Format time for lightweight charts:
        # Intraday intervals use unix timestamps
        if interval in ["1m", "5m", "15m", "30m", "1h", "4h"]:
            time_val = int(r["date"].timestamp())
        else:
            time_val = r["date"].strftime("%Y-%m-%d")
            
        candles_list.append({
            "time": time_val,
            "timestamp": r["date"].isoformat(),
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"]
        })

    # Quote info
    from backend.data.realtime_provider import realtime_provider_manager
    live_tick = realtime_provider_manager.cache.get_latest_tick(sym_clean)
    if live_tick:
        quote = {
            "price": live_tick.get("price"),
            "timestamp": live_tick.get("timestamp"),
            "provider": live_tick.get("provider", provider_name),
            "data_status": "LIVE"
        }
    else:
        # Fallback to last close
        quote = {
            "price": df_ind["close"].iloc[-1],
            "timestamp": df_ind["date"].iloc[-1].isoformat(),
            "provider": provider_name,
            "data_status": "RECENT"
        }

    result = {
        "symbol": sym_clean,
        "interval": interval,
        "provider": provider_name,
        "quote": quote,
        "candles": candles_list,
        "indicators": analysis.get("indicators"),
        "structure": analysis.get("structure"),
        "liquidity": analysis.get("liquidity"),
        "regime": analysis.get("regime"),
        "confluence": analysis.get("confluence"),
        "setup": analysis.get("setup")
    }

    ANALYSIS_CACHE[cache_key] = {"data": result, "cached_at": time.time()}
    return result
