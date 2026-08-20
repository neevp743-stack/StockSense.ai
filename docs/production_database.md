# StockSense AI — Production Database Architecture & Isolation Strategy

> **ZERO FALSE CLAIMS & DATA INTEGRITY NOTICE**:  
> Historical ML datasets in `stock_prices` are strictly isolated from real-time WebSocket ticks and live research predictions. Live predictions are recorded in `live_predictions` and `predictions` tables without ever altering historical training features or backtest evaluation bars.

---

## 1. Database Architecture Overview

StockSense AI uses SQLite for default embedded deployment (`backend/stocksense.db`) and supports production migration to PostgreSQL via `DATABASE_URL`.

### Database Schema Map

```
+-------------------+      +--------------------------+      +-------------------------+
|    stock_prices   |      |      feature_records     |      |     model_metadata      |
+-------------------+      +--------------------------+      +-------------------------+
| symbol (VARCHAR)  |      | symbol (VARCHAR)         |      | id (INTEGER PK)         |
| date (DATE)       | ---> | date (DATE)              |      | model_name (VARCHAR)    |
| open (FLOAT)      |      | rsi_14, macd, etc.       |      | symbol, version         |
| high, low, close  |      | target (INTEGER)         |      | metrics_json (TEXT)     |
| volume (FLOAT)    |      +--------------------------+      +-------------------------+
+-------------------+
                                                                     |
                                                                     v
+-----------------------------+                      +--------------------------------+
|     live_predictions        |                      |          predictions           |
+-----------------------------+                      +--------------------------------+
| symbol, timestamp           |                      | symbol, as_of_date             |
| model_version               |                      | prediction_date                |
| prob_up, prob_down          |                      | predicted_direction            |
| resolved_direction, correct |                      | resolved_direction, is_correct |
+-----------------------------+                      +--------------------------------+
```

---

## 2. Historical Data Isolation Protocol

1. **Read-Only Feature Generation**: Live prediction features are calculated in-memory from existing `stock_prices` historical bars and current WebSocket tick state.
2. **Zero In-Place Mutation**: Incoming Finnhub WebSocket ticks update the ephemeral `LiveTickCache` in memory. They **NEVER** insert or update rows in `stock_prices`.
3. **Point-In-Time Resolution**: `LivePredictionRecord` entries are resolved exclusively by future market price observations after the prediction horizon has elapsed.

---

## 3. Database Backup & Migration Strategy

### SQLite Backup Command (Production)

```bash
# Periodic live backup without database lock
sqlite3 backend/stocksense.db ".backup 'backend/backups/stocksense_backup_$(date +%Y%m%d).db'"
```

### PostgreSQL Migration Path

To migrate from SQLite to PostgreSQL in production:

1. Update `.env`:
   ```ini
   DATABASE_URL=postgresql://user:password@localhost:5432/stocksense_db
   ```
2. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```
3. Run SQLAlchemy Schema Creation:
   ```bash
   python -c "from backend.db.database import init_db; init_db()"
   ```
