# StockSense AI — Phase 21.9 Forensic Audit Report
**Brutally Honest System Security, Performance & ML Integrity Audit**
**Date:** August 26, 2026

---

## Executive Summary
This document presents a deep-dive forensic audit of the StockSense AI architecture. It exposes critical performance bottlenecks, architectural design flaws, hidden bugs, and security weaknesses present in the codebase. 

---

## Part 1: Detailed Findings (All 25 Items)

### 1. Backend Going OFFLINE Repeatedly
* **Classification:** P1
* **Evidence:** Periodic operational failures, database lock trace logs, and service unresponsiveness in production.
* **Root Cause:** High-frequency concurrent writes (prediction logging, paper trading setup resolution, and background collection updates) executing synchronously against a single-threaded SQLite database without connection timeout configurations.
* **Impact:** Operational crashes under concurrent user traffic due to database contention.
* **Recommended Fix:** Configure SQLite connection pooling with an explicit write queue, or append `timeout=30` to connection strings.
* **Risk of Fix:** Low.

### 2. Render Cold-Start and Startup Delays
* **Classification:** P1
* **Evidence:** Boot times of 30–50 seconds on Render instances.
* **Root Cause:** Render free tier spins down service on 15 minutes of inactivity. Additionally, blocking synchronous routines (`init_db()`, `seed_asset_registry_db()`, `realtime_provider_manager.start()`) run inside the FastAPI startup event loop.
* **Impact:** Render port-binding health checks fail and terminate the boot container.
* **Recommended Fix:** Move database initializations and seedings to a non-blocking background thread or execute them asynchronously after FastAPI listens. Setup a keep-alive ping worker.
* **Risk of Fix:** Low/Medium.

### 3. Slow BTC/SOL/XAU Charts
* **Classification:** P1
* **Evidence:** BTC-USD candles takes 1752ms; XAUUSD candles takes 3240ms.
* **Root Cause:** The endpoint `/api/market/{symbol}/candles` is not optimized. It imports and calls `get_market_analysis()`, which calculates EMAs, RSI, MACD, swing points, fair value gaps, order blocks, confluence scores, and setups, even though raw candlestick data is all that is requested.
* **Impact:** Extreme CPU waste and high chart-drawing latency.
* **Recommended Fix:** Update `@app.get("/api/v1/market/{symbol}/candles")` and legacy endpoints to call the lightweight `get_historical_candles()` function.
* **Risk of Fix:** Low.

### 4. Vercel "Server Failure"
* **Classification:** P1
* **Evidence:** Vercel 504 errors on production deploy.
* **Root Cause:** Vercel Serverless Functions have a strict 10–15s execution timeout. If a request triggers slow synchronous external API calls (e.g. yfinance fallback) or attempts to open persistent WebSockets (unsupported by Vercel serverless), the functions fail.
* **Impact:** UI breaks and crashes when requesting live tickers or charts.
* **Recommended Fix:** Keep WebSocket streaming off Vercel serverless; host the FastAPI backend on a dedicated container (Render/VPS), using Vercel exclusively for static React file hosting.
* **Risk of Fix:** Low.

### 5. Slow API Endpoints
* **Classification:** P1
* **Evidence:** `/api/stocks/RELIANCE/prediction` takes 787–1197ms.
* **Root Cause:** The endpoint loads model files via `joblib.load()` on disk on cache miss, computes indicators, and makes blocking synchronous `provider.get_latest_quote()` calls to Yahoo Finance on every request.
* **Impact:** Sluggish user experience on dashboard.
* **Recommended Fix:** Retrieve current price from `realtime_provider_manager.cache.get_latest_tick()` instead of calling Yahoo Finance synchronously. Warm ML models in memory on startup instead of lazy-loading from disk.
* **Risk of Fix:** Medium.

### 6. Excessive API Requests
* **Classification:** P2
* **Evidence:** Duplicate calls visible in browser network tab.
* **Root Cause:** React components lack unified context/state management for current asset data. Concurrent fetches trigger concurrent `cachedGet` calls, causing cache-miss collisions before the first response is stored.
* **Impact:** Redundant network overhead and client-side processing.
* **Recommended Fix:** Implement a single React context provider for symbol data or use React Query/SWR to deduplicate requests.
* **Risk of Fix:** Medium.

### 7. Duplicate WebSocket Connections
* **Classification:** P2
* **Evidence:** WS log messages showing double connection setups.
* **Root Cause:** Lack of strict singleton orchestration. Multiple manager start calls or double instantiations.
* **Impact:** Double bandwidth, double message volume, and potential Coinbase rate-limiting/banning.
* **Recommended Fix:** Guard the WebSocket initialization with a global locks/state check.
* **Risk of Fix:** Low.

### 8. Background Asyncio/Task Leaks
* **Classification:** P2
* **Evidence:** Cancelled tasks not awaited in `stop()` of providers.
* **Root Cause:** In `RealTimeWebSocketProvider.stop()`, background tasks are cancelled but not awaited to handle the `CancelledError` transition safely.
* **Impact:** Deprecation warnings and memory footprint creep.
* **Recommended Fix:** Await cancelled tasks inside a `try...except` block in `stop()`.
* **Risk of Fix:** Low.

### 9. Memory Leaks or RAM Spikes
* **Classification:** P2
* **Evidence:** RSS memory growth over time.
* **Root Cause:** High-volume ticks caching, model caching, and massive pandas dataframe reconstructions on every request.
* **Impact:** Server out-of-memory crashes on small instances.
* **Recommended Fix:** Bounded queues for cache storage and avoiding deep copies of large dataframes.
* **Risk of Fix:** Medium.

### 10. CPU-Heavy Operations
* **Classification:** P2
* **Evidence:** High CPU usage on chart requests.
* **Root Cause:** $O(N)$ double loops inside `analyze_market_structure_and_features` running swing points, OB confirmations, and fair value gaps calculations.
* **Impact:** High CPU core usage, slowing other parallel requests on single-core instances.
* **Recommended Fix:** Optimize loop steps or port core loops to Cython/NumPy vector operations.
* **Risk of Fix:** Medium.

### 11. Database Bottlenecks or SQLite Problems
* **Classification:** P1
* **Evidence:** Database locks during concurrent write operations.
* **Root Cause:** Missing `timeout` settings in `create_engine` connections list.
* **Impact:** Frequent OperationalErrors.
* **Recommended Fix:** Add `timeout=30` and `journal_mode=WAL` to database.py initialization.
* **Risk of Fix:** Low/Medium.

### 12. Provider Failures Causing Cascading Failures
* **Classification:** P1
* **Evidence:** Rate limits on Twelve Data (HTTP 429) causing system failures.
* **Root Cause:** Active polling in `_rest_fallback_loop` on 30s intervals makes repeated external quote calls.
* **Impact:** Service is locked out by third-party APIs.
* **Recommended Fix:** Implement smart circuit breakers and increase poll intervals on Rate Limit responses.
* **Risk of Fix:** Medium.

### 13. Frontend Unnecessary Renders/API Calls
* **Classification:** P2
* **Evidence:** Multiple component re-mounts triggering fetches.
* **Root Cause:** Raw component state updates propagate re-renders. Short (15s) caching TTL.
* **Impact:** UI jitter and api spam.
* **Recommended Fix:** Raise cache TTLs, use React `useMemo` and unified data store context.
* **Risk of Fix:** Low.

### 14. Authentication/Security Weaknesses
* **Classification:** P1
* **Evidence:** Hardcoded `SECRET_KEY` fallback in `config.py`.
* **Root Cause:** Fallback string `"stocksense-research-super-secret-key-2026"` is used when `STOCKSENSE_SECRET_KEY` is not defined in env.
* **Impact:** Attacker can compromise and forge token signatures, gaining full system admin control.
* **Recommended Fix:** Enforce a strict exception raise if `STOCKSENSE_SECRET_KEY` is missing in production environments.
* **Risk of Fix:** Low.

### 15. User-to-User Data Access/IDOR Risks
* **Classification:** KEEP
* **Evidence:** Verification of CRUD logic.
* **Root Cause:** Secure filtering is implemented on `current_user.id`.
* **Impact:** Solid security coverage.
* **Recommended Fix:** None needed.
* **Risk of Fix:** N/A.

### 16. API Abuse/Rate-Limit Weaknesses
* **Classification:** P2
* **Evidence:** Rate limit checks inside `rate_limiter.py`.
* **Root Cause:** Sliding-window arrays stored in thread-unsafe Python collections (`defaultdict(list)`).
* **Impact:** Potential API rate limiter bypass or crash under multi-threaded requests.
* **Recommended Fix:** Implement thread-safe locks or use Redis-based token-bucket rate limiter.
* **Risk of Fix:** Medium.

### 17. JWT/Authentication Problems
* **Classification:** P2
* **Evidence:** Generous expiration token (24 hours).
* **Root Cause:** Long expiration window without token revocation support.
* **Impact:** Compromised tokens remain active for a full day.
* **Recommended Fix:** Set shorter token life (15-30m) with sliding refresh token mechanics.
* **Risk of Fix:** Medium.

### 18. WhatsApp/OTP Security Problems
* **Classification:** KEEP
* **Evidence:** Cooldown checks, randbelow random codes, expiration gates, and attempt limit counts are verified.
* **Root Cause:** Excellent secure coding practices.
* **Impact:** Solid verification security.
* **Recommended Fix:** None needed.
* **Risk of Fix:** N/A.

### 19. API Key or Secret Leakage
* **Classification:** P1
* **Evidence:** `.env` file containing actual keys present in workspace.
* **Root Cause:** Storing development configuration secrets in `.env` is normal, but they should never be checked in or outputted raw in logs.
* **Impact:** Security risk.
* **Recommended Fix:** Keep `.env` in gitignore (which it is), redact all logs, use secure vaults.
* **Risk of Fix:** Low.

### 20. Frontend Bundle/Source-Map Leakage
* **Classification:** KEEP
* **Evidence:** Successful production Vite build did not generate `.map` files.
* **Root Cause:** Vite config has standard default configurations.
* **Impact:** Clean deployment bundle.
* **Recommended Fix:** None needed.
* **Risk of Fix:** N/A.

### 21. Internal Backend Information Exposed to Users
* **Classification:** P1
* **Evidence:** Typos causing NameErrors (`get_prediction_endpoint`).
* **Root Cause:** Typos in new versioned API configurations.
* **Impact:** Crashes versioned API endpoint completely (500 NameError).
* **Recommended Fix:** Replace `get_prediction_endpoint` with `get_stock_prediction`. Add automated integration test suites for versioned routing.
* **Risk of Fix:** Low.

### 22. ML Target Leakage/Look-Ahead Bias
* **Classification:** KEEP
* **Evidence:** Target construction code explicitly masks final `h` rows to NaN.
* **Root Cause:** Solid causal indexing.
* **Impact:** Reliable predictive integrity.
* **Recommended Fix:** None needed.
* **Risk of Fix:** N/A.

### 23. Feature Leakage in the Phase 12 Pipeline
* **Classification:** KEEP
* **Evidence:** Scale fit is strictly executed on training set only.
* **Root Cause:** Good ML split boundaries.
* **Impact:** Accurate evaluation.
* **Recommended Fix:** None.
* **Risk of Fix:** N/A.

### 24. Any Research/Shadow Model Accidentally Affecting Production
* **Classification:** KEEP
* **Evidence:** Shadow models write predictions in separate table, never affecting main user flow.
* **Root Cause:** Isolated databases structure.
* **Impact:** No side effects.
* **Recommended Fix:** None.
* **Risk of Fix:** N/A.

### 25. Unnecessary Files, Dependencies, APIs, or Features Slowing the Project
* **Classification:** REMOVE
* **Evidence:** `shap` in `requirements.txt`.
* **Root Cause:** SHAP is in `requirements.txt` but not used.
* **Impact:** Heavy build container size.
* **Recommended Fix:** Remove `shap` from requirements.
* **Risk of Fix:** Low.

---

## Part 2: Answers to the Five Core Questions

### A. Why does the backend go offline?
1. **Render Free Tier Sleep:** The free instance sleeps after 15 minutes of inactivity. When it wakes up, blocking startup routines (synchronous DB creation and seeding) delay port binding, causing Render port health checks to fail and terminate the container.
2. **SQLite Write Locks:** Concurrent write calls (prediction logging, paper trading setup resolution, background task updates) trigger write conflicts and raise unhandled `database is locked` OperationalErrors. Without a timeout configuration in SQLAlchemy, the API crashes.

### B. Why are charts slow?
1. **Non-Optimized `/candles` Endpoint:** The endpoint `/candles` calls `get_market_analysis()`, which triggers heavy technical indicator, market structure, FVG, OB, and confluence calculations across 300 data points instead of returning raw candle details.
2. **Short Cache TTL:** The cache TTL is set to a brief 15 seconds. Once expired, the backend makes synchronous network requests to Twelve Data or Yahoo Finance, causing latency spikes of 1.7s to 3.2s.

### C. Where can data/security leakage happen?
1. **Hardcoded SECRET_KEY Fallback:** In `config.py`, if the env variable `STOCKSENSE_SECRET_KEY` is not set, it defaults to a hardcoded string. An attacker who knows this fallback string can forge signatures on JWT tokens to bypass authentication gates.
2. **Thread-Unsafe Rate Limiter:** The RateLimiter stores arrays in plain Python dictionaries without thread-locking controls, which could leak request rates or crash under multi-threaded requests.

### D. Is there actual ML leakage?
* **No.** The ML features construction strictly enforces chronological boundaries, scaling parameters are fit solely on training partitions, and target values for future horizons are masked to `NaN`.

### E. What should we fix BEFORE adding any more features?
1. **Broken Endpoint Typo:** Correct the NameError typo `get_prediction_endpoint` -> `get_stock_prediction` in `backend/main.py`.
2. **Candles Endpoint Optimization:** Refactor `@app.get("/api/v1/market/{symbol}/candles")` to call `get_historical_candles()` instead of `get_market_analysis()`.
3. **SQLite Database Timeout:** Add `timeout=30` and `journal_mode=WAL` to connection arguments in `database.py`.
4. **Non-Blocking Startup:** Move heavy database migrations and seedings to a background thread to prevent container startup failures.
5. **Enforce Secret Key:** Raise an error if `STOCKSENSE_SECRET_KEY` is missing in production environments instead of falling back to a hardcoded string.

---

## Part 3: Actionable Summary

### TOP 10 PROBLEMS
1. Typo NameError in versioned prediction endpoint `/api/v1/stocks/{symbol}/prediction`.
2. Extremely slow `/candles` endpoint computing full market structures on raw charts.
3. Thread-unsafe in-memory Rate Limiter dictionary.
4. Missing database write timeout configs on SQLite causing crashes.
5. Hardcoded JWT `SECRET_KEY` fallback in configuration.
6. Synchronous, blocking Twelve Data and YFinance requests on hot-path quote APIs.
7. Short 15s cache TTL for candles forcing repeated external requests.
8. Blocking, synchronous database seeds and table alterations on application boot.
9. Unawaited canceled background tasks generating task leaks.
10. Unnecessary heavyweight package `shap` in dependencies list.

### TOP 10 FIXES
1. Map `/api/v1/stocks/{symbol}/prediction` to the existing `get_stock_prediction` handler.
2. Direct `/candles` endpoint calls to the lightweight `get_historical_candles` service.
3. Add a threading lock to RateLimiter methods.
4. Append `connect_args={"check_same_thread": False, "timeout": 30}` to SQLite engine.
5. Raise error if `STOCKSENSE_SECRET_KEY` is missing in production.
6. Retrieve prices from the LiveTickCache inside prediction endpoints instead of yfinance.
7. Increase `CACHE_TTL` for candles to 300 seconds.
8. Run `init_db()` and seeds in a non-blocking background thread on startup.
9. Safely `await` canceled asyncio tasks inside `stop()`.
10. Remove `shap` from `requirements.txt`.

### WHAT TO KEEP
1. Strict chronological time-series cross-validation splits.
2. Secure WhatsApp verification mechanics (hashed OTP, cooldowns, attempts limit).
3. The 128/128 production models with invariant hashes.
4. Glassmorphism terminal frontend login dashboard layout.
5. Causal target masking logic.

### WHAT TO REMOVE
1. `shap` dependency from `requirements.txt`.
2. Legacy, unused endpoints and redundant technical jargon references.
3. Duplicate Coinbase WebSocket instantiation calls.

### WHAT TO OPTIMIZE
1. Bounded queue constraints on Tick cache sizes.
2. Vectorized pandas calculations for swing point detection.
3. Memory load warmup procedures for ML models.

### NEXT 3 PHASES
1. **Phase 22.0 (Resilience & Caching):** Fix SQL timeouts, apply async startup warmup, and increase candles cache limits.
2. **Phase 22.1 (Endpoint Optimization):** Bind lightweight candles directly and eliminate inline yfinance quote lookups.
3. **Phase 22.2 (Security Hardening):** Enforce strict secrets loading, implement thread-safe rate limiters, and clean unused dependencies.
