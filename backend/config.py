import os
from typing import Dict, List

# Stock Universe Configuration
DEFAULT_UNIVERSE = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

SYMBOL_MAP: Dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
}

from dotenv import load_dotenv

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ROOT_ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Load environment variables strictly from project root .env
load_dotenv(dotenv_path=ROOT_ENV_PATH, override=True)

DB_PATH = os.path.join(PROJECT_ROOT, "stocksense.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Real-Time Market Data Provider Configuration
REALTIME_PROVIDER = os.getenv("REALTIME_PROVIDER", "FINNHUB").strip()
REALTIME_API_KEY = os.getenv("REALTIME_API_KEY", "").strip()
REALTIME_WS_URL = os.getenv("REALTIME_WS_URL", "wss://ws.finnhub.io").strip()
STALE_TICK_THRESHOLD_SECONDS = int(os.getenv("STALE_TICK_THRESHOLD_SECONDS", "30"))

# Production Environment & Security
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip()
CORS_ORIGINS_RAW = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000,http://127.0.0.1:5173,http://127.0.0.1:8000")
CORS_ALLOWED_ORIGINS: List[str] = [orig.strip() for orig in CORS_ORIGINS_RAW.split(",") if orig.strip()]


# Manual fallback parser for root .env if os.getenv was not set by process environment
if os.path.exists(ROOT_ENV_PATH):
    try:
        with open(ROOT_ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("REALTIME_API_KEY="):
                    val = line_str.split("=", 1)[1].strip()
                    if val:
                        REALTIME_API_KEY = val
                elif line_str.startswith("REALTIME_PROVIDER="):
                    val = line_str.split("=", 1)[1].strip()
                    if val:
                        REALTIME_PROVIDER = val
                elif line_str.startswith("REALTIME_WS_URL="):
                    val = line_str.split("=", 1)[1].strip()
                    if val:
                        REALTIME_WS_URL = val
    except Exception:
        pass


# Secret Key for JWT Authentication
SECRET_KEY = os.getenv("STOCKSENSE_SECRET_KEY", "stocksense-research-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# Time Series Split Ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Sequence Model (LSTM) Window
LSTM_SEQUENCE_LENGTH = 10

# Transaction Cost Default for Backtester
DEFAULT_TRANSACTION_COST = 0.001  # 0.1% per trade
DEFAULT_SLIPPAGE = 0.0005        # 0.05% slippage

# Research Disclaimer Notice
RESEARCH_DISCLAIMER = (
    "StockSense AI is a research and decision-support tool created strictly for "
    "educational evaluating of directional stock price modeling. It is NOT financial "
    "advice. Predictions and backtests do NOT guarantee future performance or returns. "
    "Direction probability is an empirical estimate, NOT a guarantee of directional outcome."
)

def get_ticker_symbol(symbol: str) -> str:
    """Returns Yahoo Finance ticker symbol for a given stock symbol."""
    clean_sym = symbol.upper().strip()
    if clean_sym in SYMBOL_MAP:
        return SYMBOL_MAP[clean_sym]
    if not clean_sym.endswith(".NS") and not clean_sym.endswith(".BO"):
        return f"{clean_sym}.NS"
    return clean_sym
