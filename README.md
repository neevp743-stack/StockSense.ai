# StockSense AI — Machine Learning Market Intelligence & Production Platform

**StockSense AI** is a state-of-the-art market intelligence platform combining real-time cryptocurrency, equity, and commodity price telemetry with machine learning predictive models and automated 24/7 uptime monitoring.

---

## 🌐 Live Production Deployments

- **Production Web Application (Vercel):** [`https://stock-sense-ai-lilac.vercel.app`](https://stock-sense-ai-lilac.vercel.app)
- **Production Backend API (Render):** [`https://stocksense-ai-backend-sdyo.onrender.com`](https://stocksense-ai-backend-sdyo.onrender.com)
- **Watchtower Health Endpoint:** [`https://stocksense-ai-backend-sdyo.onrender.com/health`](https://stocksense-ai-backend-sdyo.onrender.com/health)

---

## 🚀 Key Features

1. **Machine Learning Predictions:** Sub-second inference across 128 production ML models (`RandomForest`, `LightGBM`, `XGBoost`, `PyTorch` neural architectures). 100% invariant SHA-256 model hashes.
2. **Real-Time Telemetry Stream:** Coinbase WebSocket stream integration for real-time crypto ticks (`BTC-USD`, `SOL-USD`) combined with Twelve Data REST routing for Indian Equities (`RELIANCE`) and Forex (`XAUUSD`).
3. **Production Watchtower & Uptime Monitoring:** External, deduplicated uptime monitoring engine running via GitHub Actions (`.github/workflows/watchtower_monitoring.yml`). Outage (3-failure) and recovery (2-success) state machines with non-blocking WhatsApp alert integration.
4. **Authentication & RBAC Security:** JWT authentication with Bcrypt password hashing. Role-Based Access Control (`USER` vs `ADMIN`) restricting diagnostics endpoints with `403 Forbidden`.
5. **High Concurrency Database:** SQLite WAL mode with 30,000ms busy timeout supporting 30+ concurrent write threads with 0 lock errors.

---

## 📚 Technical Documentation Index

- [`docs/PROJECT_DOCUMENTATION_INDEX.md`](file:///c:/Users/neevp/OneDrive/Desktop/Stock%20Sense%20Ai/docs/PROJECT_DOCUMENTATION_INDEX.md) — Complete documentation catalog and navigation index.
- [`docs/PROJECT_NAMING_STANDARD.md`](file:///c:/Users/neevp/OneDrive/Desktop/Stock%20Sense%20Ai/docs/PROJECT_NAMING_STANDARD.md) — Official naming guidelines and standards.
- [`docs/PRODUCTION_WATCHTOWER_OPERATIONAL_REPORT.md`](file:///c:/Users/neevp/OneDrive/Desktop/Stock%20Sense%20Ai/docs/PRODUCTION_WATCHTOWER_OPERATIONAL_REPORT.md) — External GitHub Actions Watchtower operational report.
- [`docs/PRODUCTION_STABILITY_VALIDATION_REPORT.md`](file:///c:/Users/neevp/OneDrive/Desktop/Stock%20Sense%20Ai/docs/PRODUCTION_STABILITY_VALIDATION_REPORT.md) — Live production latency benchmarks and smoke test results.
- [`docs/SECURITY_AND_COMPLIANCE_SPEC.md`](file:///c:/Users/neevp/OneDrive/Desktop/Stock%20Sense%20Ai/docs/SECURITY_AND_COMPLIANCE_SPEC.md) — Security policies, CORS rules, and secret protection specifications.

---

## 🛠️ Quickstart & Development Setup

### Backend (Python / FastAPI)
```bash
# Initialize Python virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn backend.main:app --reload --port 8000
```

### Frontend (React / Vite)
```bash
cd frontend
npm install
npm run dev
```

### Running Test Suite
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v
```
