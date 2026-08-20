# StockSense AI — Phase 5: Real-Time Market Data Audit Report

> **ZERO FALSE CLAIMS & ACADEMIC AUDIT NOTICE**:  
> In strict compliance with the Zero False Claims policy, `yfinance` data feeds are tagged as `🟡 DELAYED` or `⚪ HISTORICAL`, and are **NEVER** labeled `🟢 LIVE`. Unless an authenticated WebSocket credentials key is configured in `.env`, the system explicitly reports `REAL-TIME PROVIDER NOT CONFIGURED` / `🔴 UNAVAILABLE`.

---

## 1. Provider & Stream Status Summary

| Configuration Field | System Value | Audit Status |
|---|---|---|
| **Real-Time Provider** | Finnhub / Polygon.io Proxy | `CONFIGURED (Backend Proxy)` |
| **Authentication Status** | Backend Environment (`.env`) | `REAL-TIME PROVIDER NOT CONCONFIGURED` (Missing API Key) |
| **Frontend Exposure** | React WebSocket (`/ws/market/{symbol}`) | `SECURE` (Zero API key exposure to JS) |
| **WebSocket Connection Status** | FastAPI Internal Proxy | `UNAVAILABLE` (Unconfigured Credentials) |
| **Stale Tick Threshold** | 30 Seconds | `ENFORCED` |
| **Historical Dataset Isolation** | `stock_prices` DB Table | `STRICTLY ISOLATED` (Live ticks use in-memory cache) |

---

## 2. Supported Asset Stream Mapping

| Asset Class | Symbols | Streaming Provider | Real-Time Status | Fallback Feed |
|---|---|---|---|---|
| **`INDIAN_EQUITY`** | `RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ICICIBANK` | Finnhub / NSE WebSocket | `UNAVAILABLE` | `🟡 DELAYED` (15-min Yahoo Finance) |
| **`US_EQUITY`** | `AAPL`, `MSFT`, `NVDA`, `AMZN`, `GOOGL` | Finnhub / Polygon WebSocket | `UNAVAILABLE` | `🟡 DELAYED` (15-min Yahoo Finance) |
| **`CRYPTO`** | `BTC-USD`, `ETH-USD` | Binance / Finnhub WebSocket | `UNAVAILABLE` | `🟡 DELAYED` (15-min Yahoo Finance) |
| **`FOREX`** | `USDINR=X`, `EURUSD=X`, `GBPUSD=X`, `USDJPY=X` | OANDA / Finnhub WebSocket | `UNAVAILABLE` | `🟡 DELAYED` (15-min Yahoo Finance) |
| **`INDEX`** | `^NSEI`, `^NSEBANK`, `^GSPC`, `^IXIC`, `^DJI` | Global Index Stream | `UNAVAILABLE` | `🟡 DELAYED` (15-min Yahoo Finance) |

---

## 3. Data Freshness Lifecycle State Machine

1. **`🟢 LIVE`**: Active authenticated WebSocket connection receiving ticks within 30 seconds.
2. **`🟡 DELAYED`**: 15-minute delayed market quote.
3. **`🟠 RECONNECTING`**: Connection lost; automatic exponential backoff reconnect in progress.
4. **`🔴 STALE`**: Active stream but no new tick received within 30-second threshold.
5. **`🔴 UNAVAILABLE`**: Real-time provider API key unconfigured or provider unreachable.
6. **`⚪ MARKET CLOSED`**: Exchange session currently closed.

---

## 4. Manual Live Verification Results

1. **Unconfigured Key Test**: Verified that launching backend without `REALTIME_API_KEY` displays `🔴 DATA UNAVAILABLE` / `REAL-TIME PROVIDER NOT CONCONFIGURED`, correctly avoiding fake `LIVE` claims.
2. **Mock Tick Integration**: In-memory `LiveTickCache` correctly normalizes ticks and updates React UI over `/ws/market/{symbol}` with pulse visual animations.
3. **Historical Data Isolation**: Verified that live ticks populate `LiveTickCache` only, leaving SQLite `stock_prices` and training data 100% untouched.

---

## 5. Architectural Limitations & Next Steps

- Free tier API credentials do not grant 24/7 level-2 WebSocket streaming for all 21 assets simultaneously.
- To activate production live streaming for US stocks, add a valid Finnhub or Polygon API key to `.env`:
  ```env
  REALTIME_PROVIDER=FINNHUB
  REALTIME_API_KEY=your_realtime_api_key_here
  ```
