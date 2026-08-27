# StockSense AI — Repository Structure & Component Architecture

**Feature:** Repository Structure & Architecture Reference  
**Scope:** Workspace Directory Layout & Core Modules  

---

## 1. Directory Layout

```
Stock Sense Ai/
├── .github/
│   └── workflows/
│       └── watchtower_monitoring.yml    # External GitHub Actions 5-min uptime scheduler
├── backend/
│   ├── data/
│   │   ├── providers/                   # Market data REST providers (Twelve Data, Finnhub)
│   │   └── realtime_provider.py         # Coinbase WebSocket & stream manager
│   ├── db/
│   │   ├── database.py                  # SQLite engine, WAL mode, busy timeout
│   │   ├── models.py                    # Core domain entities (Asset, Price, Feature, User)
│   │   ├── models_watchtower.py         # Watchtower telemetry tables
│   │   └── seed_test_user.py            # Standalone CLI test account seed script
│   ├── research/                        # Verification, audit, and benchmark reports
│   ├── services/
│   │   ├── production_watchtower_service.py # Watchtower state machine & alert engine
│   │   └── user_service.py              # Auth, Bcrypt hashing, JWT generation
│   └── main.py                          # FastAPI application routes & endpoints
├── docs/                                # Central technical documentation directory
├── frontend/                            # React + Vite web application
│   ├── src/
│   │   ├── components/                  # UI pages (AdminDiagnosticsPage, MarketsPage, etc.)
│   │   └── api.ts                       # Frontend API client
│   └── vercel.json                      # Vercel deployment rewrite rules & crons
├── saved_models/                        # 128 production ML models (.joblib, .pt)
├── tests/                               # Pytest unit & integration test suite
└── README.md                            # Professional project presentation
```

---

## 2. Component Boundaries

1. **Backend Service Layer (`backend/services/`):** Decoupled business logic isolated from HTTP routing.
2. **Database Models (`backend/db/`):** SQLAlchemy models inheriting from declarative Base. All schema changes register cleanly in SQLite WAL database.
3. **Frontend UI (`frontend/src/components/`):** React components styled with vanilla CSS design system and modern micro-animations.
