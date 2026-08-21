import yfinance as yf
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from backend.config import get_ticker_symbol, DEFAULT_UNIVERSE
from backend.assets.asset_registry import get_asset_info, ASSET_REGISTRY
from backend.db.database import SessionLocal, init_db
from backend.db.models import StockPrice, AssetRecord
from backend.data.data_validator import validate_market_data
from backend.data.provider import YFinanceProvider

class DataProviderUnavailableException(Exception):
    """Raised when external market data provider fails or returns no data."""
    pass

provider_instance = YFinanceProvider()

def seed_asset_registry_db(db: Optional[Session] = None):
    """Seeds AssetRecord table with the 21 registered multi-asset configurations."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        for sym, info in ASSET_REGISTRY.items():
            stmt = sqlite_upsert(AssetRecord).values(
                symbol=info["symbol"],
                display_name=info["display_name"],
                asset_class=info["asset_class"],
                exchange=info["exchange"],
                market=info["market"],
                currency=info["currency"],
                currency_symbol=info["currency_symbol"],
                provider_symbol=info["provider_symbol"],
                active=info["active"],
                trading_calendar=info["trading_calendar"],
                timezone=info["timezone"]
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "display_name": info["display_name"],
                    "asset_class": info["asset_class"],
                    "exchange": info["exchange"],
                    "currency": info["currency"],
                    "currency_symbol": info["currency_symbol"],
                    "provider_symbol": info["provider_symbol"],
                    "active": info["active"]
                }
            )
            db.execute(stmt)
        db.commit()
    finally:
        if close_db:
            db.close()

def fetch_historical_data(symbol: str, period: str = "5y", start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieves real historical market data via MarketDataProvider abstraction.
    STRICT RULE: Never fabricates or synthesizes market data.
    """
    df = provider_instance.get_historical_data(symbol, period=period)
    if df.empty:
        raise DataProviderUnavailableException(
            f"Real market data unavailable for symbol '{symbol}'."
        )
    df["symbol"] = symbol.upper().strip()
    return df

    # Flatten multi-index columns if yfinance returns multi-index
    if isinstance(df_raw.columns, pd.MultiIndex):
        df_raw.columns = df_raw.columns.get_level_values(0)

    # Reset index to get Date as a column
    df = df_raw.reset_index()

    # Standardize column names to lowercase
    cols = {col: str(col).lower() for col in df.columns}
    df = df.rename(columns=cols)

    # Ensure required columns exist
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataProviderUnavailableException(
            f"Market data malformed — missing columns {missing} for '{ticker}'."
        )

    # Filter to required columns and convert data types
    df = df[required].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    for num_col in ["open", "high", "low", "close", "volume"]:
        df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    # Drop any row with NaNs in date or close
    df = df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    df["symbol"] = symbol.upper().strip()

    return df

from backend.cache import history_cache

def save_prices_to_db(df: pd.DataFrame, db: Optional[Session] = None) -> int:
    """Saves/upserts cleaned historical prices to SQLite database using bulk operations."""
    if df is None or df.empty:
        return 0

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        symbol_name = df["symbol"].iloc[0] if "symbol" in df.columns and not df.empty else None
        records_data = []
        for row in df.to_dict(orient="records"):
            records_data.append({
                "symbol": str(row["symbol"]).upper().strip(),
                "date": row["date"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
            })

        if records_data:
            stmt = sqlite_upsert(StockPrice)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["symbol", "date"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume
                }
            )
            db.execute(upsert_stmt, records_data)
            db.commit()

        if symbol_name:
            history_cache.invalidate(str(symbol_name).upper().strip())
        return len(records_data)
    finally:
        if close_db:
            db.close()

def get_historical_data_from_db(symbol: str, db: Optional[Session] = None, limit: Optional[int] = None) -> pd.DataFrame:
    """Retrieves stored historical OHLCV data from SQLite database with in-memory TTL caching."""
    symbol_clean = symbol.upper().strip()
    cache_key = f"hist_{symbol_clean}_{limit or 'all'}"
    cached_df = history_cache.get(cache_key)
    if cached_df is not None:
        return cached_df

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        if limit and limit > 0:
            records = db.query(StockPrice).filter(StockPrice.symbol == symbol_clean).order_by(StockPrice.date.desc()).limit(limit).all()
            records.reverse()
        else:
            records = db.query(StockPrice).filter(StockPrice.symbol == symbol_clean).order_by(StockPrice.date.asc()).all()

        if not records:
            empty_df = pd.DataFrame()
            history_cache.set(cache_key, empty_df, ttl_seconds=60)
            return empty_df

        data = [{
            "symbol": r.symbol,
            "date": r.date,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume
        } for r in records]

        df = pd.DataFrame(data)
        history_cache.set(cache_key, df, ttl_seconds=600)
        return df
    finally:
        if close_db:
            db.close()


def ensure_historical_data_in_db(symbol: str, db: Optional[Session] = None, period: str = "2y", limit: Optional[int] = None) -> pd.DataFrame:
    """
    Ensures historical OHLCV market data exists in SQLite DB for symbol.
    If DB is empty for symbol, fetches real historical data from provider on-the-fly and saves to DB.
    Never fabricates synthetic prices.
    """
    symbol_clean = symbol.upper().strip()
    df = get_historical_data_from_db(symbol_clean, db=db, limit=limit)
    if df.empty:
        try:
            df_fetched = fetch_historical_data(symbol_clean, period=period)
            save_prices_to_db(df_fetched, db=db)
            return get_historical_data_from_db(symbol_clean, db=db, limit=limit)
        except Exception as e:
            print(f"Unable to fetch historical data on-the-fly for '{symbol_clean}': {e}")
            return pd.DataFrame()
    return df



def sync_stock_universe(symbols: Optional[List[str]] = None, period: str = "5y") -> Dict[str, Any]:
    """
    Downloads historical data for all symbols in the universe, validates each,
    saves to DB, and returns audit reports for each stock.
    """
    init_db()
    seed_asset_registry_db()
    if symbols is None:
        symbols = DEFAULT_UNIVERSE

    reports = {}
    db = SessionLocal()
    try:
        for sym in symbols:
            try:
                df = fetch_historical_data(sym, period=period)
                audit_report = validate_market_data(df, sym)
                save_prices_to_db(df, db=db)
                reports[sym] = {
                    "status": "success",
                    "rows_saved": len(df),
                    "audit": audit_report
                }
            except DataProviderUnavailableException as e:
                reports[sym] = {
                    "status": "failed",
                    "error": str(e),
                    "audit": None
                }
            except Exception as e:
                reports[sym] = {
                    "status": "error",
                    "error": str(e),
                    "audit": None
                }
        return reports
    finally:
        db.close()
