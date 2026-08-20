# StockSense AI — Production Deployment Guide

> **Production Setup Instructions for Static Frontend + FastAPI/WebSocket Backend Hosting**

---

## 1. Required Environment Variables (`.env`)

```ini
ENVIRONMENT=production
REALTIME_PROVIDER=FINNHUB
REALTIME_API_KEY=your_actual_finnhub_key_here
REALTIME_WS_URL=wss://ws.finnhub.io
STALE_TICK_THRESHOLD_SECONDS=30
DATABASE_URL=sqlite:///./backend/stocksense.db
CORS_ALLOWED_ORIGINS=https://stocksense-ai.vercel.app,https://your-domain.com
```

---

## 2. Frontend Production Build & Static Deployment

### Step A: Build Static Dist Bundle

```bash
cd frontend
npm install
npm run build
```

The compiled assets will be generated in `frontend/dist/`.

### Step B: Deploy to Vercel / Netlify / Render Static Site

- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: Set `VITE_API_BASE_URL=https://your-fastapi-backend.onrender.com/api`

---

## 3. Backend Production Deployment (FastAPI + WebSockets)

Deploy the Python backend to a service that supports persistent WebSockets (e.g. Render, Railway, AWS EC2, DigitalOcean App Platform, Fly.io).

### Render / Railway Start Command

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
```

> **Note on Workers**: When running Finnhub WebSocket background streaming, use `--workers 1` or run a single process so that `realtime_provider_manager` maintains a single WebSocket connection to Finnhub.

---

## 4. HTTPS & WSS WebSocket Protocol

The frontend automatically detects SSL:
- On `http://localhost:5173`, it uses `ws://localhost:8000/ws/market/{symbol}`.
- On `https://your-app.vercel.app`, it uses `wss://your-backend.onrender.com/ws/market/{symbol}`.

---

## 5. System Health Verification

Verify backend deployment using health check endpoints:
- `GET https://your-backend.onrender.com/health`
- `GET https://your-backend.onrender.com/api/system/status`
