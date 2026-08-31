# StockSense AI — Phase 22 Forensic Architecture Audit Report

**Phase:** Phase 22 — Production End-to-End Prediction Repair & Verification  
**Task:** Full Repository Forensic Audit  
**Date:** August 31, 2026  
**Audit Status:** `FORENSIC_AUDIT_COMPLETE`  

---

## 1. Architecture Overview

StockSense AI is structured as a decoupled web application with a FastAPI backend server hosted on Render and a React + Vite single-page application hosted on Vercel.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Browser (Vercel SPA)                       │
│    https://stock-sense-ai-lilac.vercel.app (React + Vite + Recharts)       │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ REST API / WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Server (Render)                      │
│               https://stocksense-ai-backend-sdyo.onrender.com               │
│                                                                             │
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐ │
│ │  Authentication &    │  ┌ Real-Time Telemetry  │  │ Machine Learning    │ │
│ │  RBAC (`/auth`)      │  │ Router               │  │ Inference Engine    │ │
│ └──────────────────────┘  └──────────┬───────────┘  └──────────┬──────────┘ │
│                                      │                         │            │
│ ┌────────────────────────────────────┴─────────────────────────┴──────────┐ │
│ │                  SQLite WAL Database (`stocksense.db`)                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTP / WebSocket Outbound
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      External Market Data Providers                         │
│   • Coinbase WS Stream (Crypto: BTC-USD, SOL-USD)                           │
│   • Twelve Data REST API (Equities & Forex: XAUUSD)                         │
│   • Finnhub & yfinance REST Fallbacks                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend → Backend Request Flow

1. **API Client (`frontend/src/api.js`):**
   - Base URL auto-normalized from `import.meta.env.VITE_API_BASE_URL` or defaults to `https://stocksense-ai-backend-sdyo.onrender.com/api`.
   - Interceptors automatically attach `Authorization: Bearer <token>` from `localStorage.getItem('stocksense_token')`.
   - Implements `cachedGet` with bounded TTLs (5s for quotes/predictions, 15s for dashboard data, 30s for history).
2. **Dashboard Data Consolidation (`App.jsx` L133):**
   - Calls `api.getDashboardData(symbol, modelName)` $\rightarrow$ `GET /api/stocks/{symbol}/dashboard-data`.
   - Backend endpoint consolidates history (`ensure_historical_data_in_db`), latest prediction (`get_stock_prediction`), technical analysis (`get_technical_analysis`), and asset info (`get_asset_info`).

---

## 3. Market Data Flow

1. **Real-Time Telemetry Stream (`backend/data/realtime_provider.py` & `provider_router.py`):**
   - **Crypto (BTC-USD, SOL-USD):** Coinbase Public WebSocket (`CoinbaseWSProvider`) streams live ticker ticks into in-memory `RealtimeCache`.
   - **Equities / Commodities (RELIANCE, AAPL, XAUUSD):** Twelve Data REST Provider (`TwelveDataProvider`) and Finnhub REST Provider query live quotes with a 5-second TTL.
   - **Historical OHLCV:** `ensure_historical_data_in_db` checks local SQLite `stock_prices` table; if stale (>1 day), syncs historical candles from provider into SQLite.

---

## 4. Prediction Flow

1. **Model Storage (`saved_models/`):**
   - 128 trained ML models (`XGBoost`, `LightGBM`, `RandomForest`, `LogisticRegression`, `PyTorch` neural checkpoints) for universe assets (`RELIANCE`, `INFY`, `TCS`, `AAPL`, `NVDA`, `BTC-USD`, `ETH-USD`, `SOL-USD`).
2. **Inference Pipeline (`ModelPipeline.load_model` & `live_prediction_service.py`):**
   - Feature engineering (`compute_features_and_target`) extracts 20+ technical indicators (RSI, MACD, Bollinger Bands, ATR, Return Momentum, Volume Volatility).
   - Latest feature vector `df_feat.iloc[[-1]]` is passed into `pipe.predict(latest_row)`.
   - Outputs predicted direction (`UP` / `DOWN`), calibrated probabilities (`probability_up`, `probability_down`), risk category (`categorize_risk_and_signal`), and market regime classification.
3. **Database Telemetry Persistence:**
   - Prediction runs are logged to SQLite table `predictions` or `live_predictions` with `as_of_date`, `prediction_date`, `model_version`, and SHAP explanation metadata.

---

## 5. Chart Flow

1. **Frontend Component (`AdvancedStockChart.jsx`):**
   - Uses `recharts` / `lightweight-charts` to visualize historical OHLCV candles.
   - Consumes `historyData` array returned by `/api/stocks/{symbol}/history` or consolidated `/api/stocks/{symbol}/dashboard-data`.
   - Formats timestamps to locale dates and formats prices dynamically based on asset currency (`₹` for Indian equities, `$` for Crypto/US equities).

---

## 6. Authentication Flow

1. **Login Endpoint (`POST /api/v1/auth/login`):**
   - Verifies email and password using `passlib` / `bcrypt`.
   - Returns signed JWT access token (`HS256`, 7-day expiration).
2. **Role-Based Access Control (RBAC):**
   - `ROLE = USER`: Granted access to markets, quotes, candles, predictions, and user profile. Blocked from `/api/admin/*` with `403 Forbidden`.
   - `ROLE = ADMIN`: Granted access to system diagnostics (`/api/admin/diagnostics`) and Watchtower telemetry.
3. **Test Account Standard:**
   - Non-admin test account `test@stocksense.local` / `StockSense@2026` seeded via standalone CLI script `backend/db/seed_test_user.py`.

---

## 7. Environment-Variable Dependencies

| Env Var Name | Location | Required / Optional | Purpose |
| :--- | :--- | :---: | :--- |
| `SECRET_KEY` | Backend (`.env`) | **REQUIRED** | JWT token signing key |
| `DATABASE_URL` | Backend (`.env`) | **REQUIRED** | SQLite WAL file path (`sqlite:///./stocksense.db`) |
| `CRON_SECRET` | Backend / GitHub | **REQUIRED** | Watchtower endpoint Bearer authorization |
| `TWELVE_DATA_API_KEY` | Backend (`.env`) | OPTIONAL | Twelve Data REST API key for equities |
| `FINNHUB_API_KEY` | Backend (`.env`) | OPTIONAL | Finnhub REST API fallback key |
| `WHATSAPP_API_KEY` | Backend (`.env`) | OPTIONAL | Outage alert WhatsApp integration |
| `VITE_API_BASE_URL` | Frontend (`.env`) | **REQUIRED** | Production API URL endpoint |

---

## 8. Production URLs & Deployment Configuration

- **Production Frontend (Vercel):** `https://stock-sense-ai-lilac.vercel.app`
- **Production Backend (Render):** `https://stocksense-ai-backend-sdyo.onrender.com`
- **Watchtower Health Target:** `https://stocksense-ai-backend-sdyo.onrender.com/health`
- **Watchtower Cron Target:** `https://stocksense-ai-backend-sdyo.onrender.com/api/watchtower/cron`
- **Vercel Config (`frontend/vercel.json`):** SPA rewrites to `index.html` + cron schedule `*/5 * * * *`.
- **GitHub Actions Workflow (`.github/workflows/watchtower_monitoring.yml`):** 5-minute external heartbeat trigger.

---

## 9. Current Observations & Potential Risk Areas

1. **Render Free-Tier Cold Starts:**
   - Inactive backend instances sleep after 15 minutes, producing 30-45 second initial request latency.
   - Frontend needs explicit cold-start status states ("Waking backend...", "Running prediction...") to prevent user confusion.
2. **Client-Side Cache Invalidation:**
   - `api.getDashboardData` uses a 15s client-side cache TTL; when switching symbols quickly, stale cached data must be properly invalidated or revalidated.
3. **Data Availability for Rare Symbols:**
   - If an unsupported asset symbol is requested, the endpoint must return a structured HTTP 404 or clear `"Prediction unavailable"` payload without failing silently.

---

## 10. Root Cause Hypotheses & Remediation Strategy

1. **Hypothesis 1 — Cold Start UX Disconnect:**
   - *Issue:* When Render backend is sleeping, prediction requests timeout or show empty states before the backend finishes booting.
   - *Fix:* Implement graceful timeout and state notifications ("Waking backend...") on prediction loading spinners.
2. **Hypothesis 2 — Schema Strictness in Frontend Components:**
   - *Issue:* Frontend prediction components expect a specific key structure (`probability_up` vs `confidence`, `predicted_direction` vs `direction`).
   - *Fix:* Ensure backend JSON response payload provides all standardized fields (`symbol`, `latest_price`, `predicted_direction`, `probability_up`, `signal`, `prediction_horizon`, `model_version`, `timestamp`).
3. **Hypothesis 3 — Model Checkpoint Invariance:**
   - *Issue:* Any modification to `saved_models/` would break verification.
   - *Fix:* Enforce strict model file invariance (`python scratch/test_ml_integrity.py`) to confirm zero model tampering.
