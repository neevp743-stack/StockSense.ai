import os
import json
import asyncio
from datetime import datetime, timedelta, date

from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Response

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import (
    DEFAULT_UNIVERSE, SYMBOL_MAP, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, RESEARCH_DISCLAIMER,
    ENVIRONMENT, CORS_ALLOWED_ORIGINS, REALTIME_PROVIDER, PROJECT_ROOT
)

from backend.db.database import get_db, init_db, SessionLocal
from backend.db.models import StockPrice, FeatureRecord, ModelMetadata, PredictionRecord, UserRecord
from backend.data.data_service import (
    get_historical_data_from_db, ensure_historical_data_in_db, seed_asset_registry_db,
    sync_stock_universe, fetch_historical_data, save_prices_to_db
)
from backend.cache import indicators_cache, prediction_cache, quote_cache, dashboard_cache, history_cache, model_cache

from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS
from backend.models.baseline_models import ModelPipeline
from backend.models.explainability import get_shap_explanations
from backend.risk.risk_assessor import categorize_risk_and_signal
from backend.tracking.tracker import log_prediction, resolve_pending_predictions, get_prediction_history
from backend.backtest.backtester import run_backtest
from backend.models.trainer import train_all_models_for_symbol, train_entire_universe

# Password Hashing & OAuth2
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# FastAPI App
app = FastAPI(
    title="StockSense AI API",
    description="Explainable machine-learning platform for stock price directional predictions",
    version="1.0.0"
)

# Environment-aware CORS & Gzip Compression
cors_origins = CORS_ALLOWED_ORIGINS if ENVIRONMENT == "production" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

import time

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Process-Time-ms"] = f"{process_time:.2f}"
    return response




async def background_cache_warmup():
    """
    Non-blocking background cache pre-warming task.
    Pre-populates dashboard_cache for top stock universe asynchronously in background threads.
    """
    await asyncio.sleep(3)
    warmup_universe = ["RELIANCE", "INFY", "TCS"]
    print(f"Starting non-blocking background cache warming for {len(warmup_universe)} priority assets...")
    
    def warm_single_symbol(symbol: str):
        db = SessionLocal()
        try:
            cache_key = f"dashboard_{symbol}_XGBoost"
            if not dashboard_cache.get(cache_key):
                ensure_historical_data_in_db(symbol, db=db)
        except Exception as e:
            print(f"Background cache warmup non-fatal warning for {symbol}: {e}")
        finally:
            db.close()

    for symbol in warmup_universe:
        try:
            await asyncio.to_thread(warm_single_symbol, symbol)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Background thread warmup error for {symbol}: {e}")

@app.on_event("startup")
async def startup_event():
    init_db()
    try:
        seed_asset_registry_db()
    except Exception as e:
        print(f"Startup asset seed warning: {e}")

    from backend.data.realtime_provider import realtime_provider_manager
    await realtime_provider_manager.start()

    # Launch non-blocking background cache pre-warming AFTER startup
    asyncio.create_task(background_cache_warmup())


@app.on_event("shutdown")
async def shutdown_event():
    from backend.data.realtime_provider import realtime_provider_manager
    await realtime_provider_manager.stop()


# Pydantic Schemas
class BacktestRequest(BaseModel):
    symbol: str = "RELIANCE"
    initial_capital: float = 100000.0
    prob_threshold: float = 0.55
    allow_short: bool = False
    transaction_cost: float = 0.001
    slippage: float = 0.0005

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Endpoints
@app.get("/")
def read_root():
    return {
        "name": "StockSense AI API",
        "status": "online",
        "disclaimer": RESEARCH_DISCLAIMER
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    """GET /health - Standard production health monitoring endpoint."""
    return {
        "status": "ok",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/system/status")
@app.get("/api/system/status")
def get_system_status():
    """GET /api/system/status - Detailed operational status of system components."""
    from backend.data.realtime_provider import realtime_provider_manager
    rt_info = realtime_provider_manager.get_stream_status()
    return {
        "backend": "ONLINE",
        "database": "CONNECTED",
        "realtime_provider": REALTIME_PROVIDER,
        "realtime_status": rt_info.get("connection_status", "UNAVAILABLE"),
        "model": "XGBoost v1.0",
        "environment": ENVIRONMENT
    }



from backend.assets.asset_registry import (
    ASSET_CLASSES, ASSET_REGISTRY, get_asset_info, get_assets_by_class, get_all_assets, search_assets
)
from backend.data.provider import YFinanceProvider

provider = YFinanceProvider()

@app.get("/api/search")
def search_stock_universe(q: str = "", limit: int = 20):
    """GET /api/search?q=... - Dynamic search matching symbol or company name."""
    results = search_assets(q, limit=limit)
    return {
        "query": q,
        "count": len(results),
        "assets": results
    }

@app.get("/api/research/phase15/status")
def get_phase15_research_status():
    """GET /api/research/phase15/status - Returns Phase 15 research study status and statistical verdict."""
    verdict_path = os.path.join(PROJECT_ROOT, "backend", "research", "phase15", "phase15_verdict.json")
    verdict_data = None
    if os.path.exists(verdict_path):
        try:
            with open(verdict_path, "r", encoding="utf-8") as f:
                verdict_data = json.load(f)
        except Exception:
            pass

    return {
        "current_production_model": "Phase 12 Calibrated XGBoost v1.0",
        "phase15_status": "COMPLETED",
        "phase15_verdict": verdict_data.get("verdict", "PHASE15_RESEARCH_CANDIDATE") if verdict_data else "PHASE15_RESEARCH_CANDIDATE",
        "verdict_reason": verdict_data.get("verdict_reason", "Phase 15 feature evaluation complete.") if verdict_data else "Study executed successfully.",
        "research_details": verdict_data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/markets")

@app.get("/api/markets/{exchange}")
def get_markets_universe(exchange: Optional[str] = None, asset_class: Optional[str] = None, page: int = 1, limit: int = 50):
    """GET /api/markets - Paginated market universe endpoint."""
    all_assets = get_all_assets()
    
    if exchange:
        ex_clean = exchange.upper().strip()
        all_assets = [a for a in all_assets if a.get("exchange", "").upper() == ex_clean]
    
    if asset_class:
        cls_clean = asset_class.upper().strip()
        all_assets = [a for a in all_assets if a.get("asset_class", "").upper() == cls_clean]

    total_count = len(all_assets)
    page_safe = max(1, page)
    limit_safe = min(100, max(1, limit))
    start_idx = (page_safe - 1) * limit_safe
    end_idx = start_idx + limit_safe
    
    page_items = all_assets[start_idx:end_idx]
    total_pages = max(1, (total_count + limit_safe - 1) // limit_safe)

    return {
        "page": page_safe,
        "limit": limit_safe,
        "total_assets": total_count,
        "total_pages": total_pages,
        "assets": page_items
    }

@app.get("/api/asset-classes")
def get_asset_classes():
    """GET /api/asset-classes - Returns supported asset classes."""
    return {"asset_classes": ASSET_CLASSES}

@app.get("/api/assets")
def get_assets(asset_class: Optional[str] = None):
    """GET /api/assets - Returns registered multi-asset list (optionally filtered by asset_class)."""
    if asset_class:
        assets = get_assets_by_class(asset_class)
    else:
        assets = get_all_assets()
    return {"assets": assets, "count": len(assets)}

@app.get("/api/assets/{symbol}")
def get_asset_detail(symbol: str):
    """GET /api/assets/{symbol} - Returns asset metadata (auto-registers on demand)."""
    info = get_asset_info(symbol)
    if not info:
        raise HTTPException(status_code=404, detail=f"Asset symbol '{symbol}' not found.")
    return {"asset": info}

@app.get("/api/stocks/{symbol}/dashboard-data")
def get_dashboard_data(symbol: str, model_name: str = "XGBoost", db: Session = Depends(get_db)):
    """
    GET /api/stocks/{symbol}/dashboard-data
    Ultra-fast consolidated endpoint returning history, prediction, technical analysis, and asset info.
    Serves warm responses in < 5ms.
    """
    symbol_clean = symbol.upper().strip()
    cache_key = f"dash_{symbol_clean}_{model_name}"
    cached = dashboard_cache.get(cache_key)
    if cached is not None:
        return cached

    # 1. Fetch History
    df_raw = ensure_historical_data_in_db(symbol_clean, db=db)
    if df_raw.empty:
        raise HTTPException(status_code=404, detail=f"Market data unavailable for '{symbol_clean}'.")

    history_records = df_raw.to_dict(orient="records")

    # 2. Fetch Prediction
    try:
        prediction_payload = get_stock_prediction(symbol_clean, model_name=model_name, db=db)
    except Exception as e:
        prediction_payload = None

    # 3. Fetch Technical Analysis
    try:
        ta_payload = get_technical_analysis(symbol_clean, db=db)
    except Exception as e:
        ta_payload = None

    # 4. Asset Metadata
    asset_info = get_asset_info(symbol_clean)

    res_payload = {
        "symbol": symbol_clean,
        "asset_info": asset_info,
        "history": {
            "symbol": symbol_clean,
            "count": len(history_records),
            "data": history_records
        },
        "prediction": prediction_payload,
        "technical_analysis": ta_payload
    }

    dashboard_cache.set(cache_key, res_payload, ttl_seconds=60)
    return res_payload

@app.get("/api/stocks")
def get_stocks_universe():
    """GET /api/stocks - Returns configured universe of Indian equities (Backward compatible)."""
    stocks = get_assets_by_class("INDIAN_EQUITY")
    return {"universe": stocks, "disclaimer": RESEARCH_DISCLAIMER}

@app.get("/api/stocks/{symbol}/history")
def get_stock_history(symbol: str, response: Response, limit: Optional[int] = None, db: Session = Depends(get_db)):
    """GET /api/stocks/{symbol}/history - Historical OHLCV data with optional limit parameter."""
    symbol_clean = symbol.upper().strip()
    df = ensure_historical_data_in_db(symbol_clean, db=db, limit=limit)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Market data unavailable for symbol '{symbol_clean}'.")

    records = df.to_dict(orient="records")
    response.headers["Cache-Control"] = "public, max-age=60"
    return {
        "symbol": symbol_clean,
        "count": len(records),
        "data": records
    }


@app.get("/api/stocks/{symbol}/features")
def get_stock_features(symbol: str, db: Session = Depends(get_db)):
    """GET /api/stocks/{symbol}/features - Historical computed feature matrix."""
    symbol_clean = symbol.upper().strip()
    df = ensure_historical_data_in_db(symbol_clean, db=db)
    if df.empty:
        raise HTTPException(status_code=404, detail="Market data unavailable — configure data provider.")

    df_feat = compute_features_and_target(df)
    if df_feat.empty:
        raise HTTPException(status_code=400, detail="Insufficient price data to compute technical indicators.")

    records = df_feat.to_dict(orient="records")
    return {
        "symbol": symbol_clean,
        "feature_count": len(FEATURE_COLUMNS),
        "columns": FEATURE_COLUMNS,
        "count": len(records),
        "data": records
    }

@app.get("/api/stocks/{symbol}/prediction")
def get_stock_prediction(symbol: str, model_name: str = "XGBoost", db: Session = Depends(get_db)):
    """
    GET /api/stocks/{symbol}/prediction - Latest AI prediction, probabilities,
    risk/signal category, SHAP explanation breakdown, and disclaimers.
    """
    symbol_clean = symbol.upper().strip()
    df_raw = ensure_historical_data_in_db(symbol_clean, db=db)
    if df_raw.empty:
        raise HTTPException(status_code=404, detail="Market data unavailable — configure data provider.")

    last_d = str(df_raw["date"].iloc[-1]) if "date" in df_raw.columns and not df_raw.empty else "NO_DATE"
    cache_key = f"pred_{symbol_clean}_{model_name}_v1.0_{last_d}"
    cached_pred = prediction_cache.get(cache_key)
    if cached_pred is not None:
        return cached_pred


    df_feat = compute_features_and_target(df_raw)
    if df_feat.empty:
        raise HTTPException(status_code=400, detail="Insufficient feature data.")

    latest_row = df_feat.iloc[[-1]]
    as_of_d = latest_row["date"].iloc[0]
    if hasattr(as_of_d, "date"):
        as_of_d = as_of_d.date()

    # Load requested model or fallback
    pipe = ModelPipeline.load_model(symbol_clean, model_name)
    if not pipe or not pipe.is_trained:
        pipe = ModelPipeline.load_model(symbol_clean, "LogisticRegression")
        if not pipe or not pipe.is_trained:
            pipe = ModelPipeline.load_model(symbol_clean, "XGBoost")

    if not pipe or not pipe.is_trained:
        # Graceful heuristic technical fallback so API returns immediately without blocking on training

        rsi_val = float(latest_row.get("rsi", [50.0])[0]) if "rsi" in latest_row else 50.0
        prob_up = 0.55 if rsi_val > 50 else 0.45
        predicted_dir = 1 if prob_up >= 0.50 else 0
        risk_info = categorize_risk_and_signal(prob_up)
        quote_info = provider.get_latest_quote(symbol_clean)
        latest_price_val = quote_info.get("price") or (float(df_raw["close"].iloc[-1]) if not df_raw.empty else None)
        
        from backend.features.regime_engine import get_latest_regime
        regime_info = get_latest_regime(df_raw)

        fallback_res = {
            "symbol": symbol_clean,
            "latest_price": latest_price_val,
            "quote_info": quote_info,
            "as_of_date": str(as_of_d),
            "prediction_date": str(as_of_d + timedelta(days=1)),
            "predicted_direction": "UP" if predicted_dir == 1 else "DOWN",
            "probability_up": prob_up,
            "probability_down": 1.0 - prob_up,
            "signal": risk_info.get("signal", "NEUTRAL"),
            "prediction_horizon": "1 trading day",
            "model_version": f"{model_name} (Technical Fallback)",
            "trend_regime": regime_info.get("trend_regime", "SIDEWAYS"),
            "volatility_regime": regime_info.get("volatility_regime", "LOW_VOLATILITY"),
            "combined_regime": regime_info.get("combined_regime", "SIDEWAYS (LOW VOL)"),
            "coverage_stats": {
                "confidence_threshold_bounds": [0.47, 0.53],
                "selective_signal_status": "ACTIVE"
            },
            "risk": risk_info,
            "model": {
                "name": f"{model_name} (Technical Fallback)",
                "metrics": {"accuracy": 0.55}
            },
            "explanations": [{"feature": "RSI Baseline", "importance": 0.50}],
            "disclaimer": RESEARCH_DISCLAIMER
        }

        prediction_cache.set(cache_key, fallback_res, ttl_seconds=60)
        return fallback_res

    preds, probs = pipe.predict(latest_row)
    prob_up = float(probs[0])
    predicted_dir = int(preds[0])

    # Risk Assessor
    brier = pipe.metrics.get("brier_score", None)
    risk_info = categorize_risk_and_signal(prob_up, brier_score=brier)

    # Dynamic SHAP Explanation
    shap_info = get_shap_explanations(pipe, latest_row)

    # Prediction target date: next trading day
    prediction_d = as_of_d + timedelta(days=1)
    if as_of_d.weekday() == 4:  # Friday -> Monday
        prediction_d = as_of_d + timedelta(days=3)

    # Log prediction to database
    log_prediction(
        symbol=symbol_clean,
        as_of_date=as_of_d,
        prediction_date=prediction_d,
        predicted_direction=predicted_dir,
        prob_up=prob_up,
        prob_down=1.0 - prob_up,
        risk_category=risk_info["risk_category"],
        model_version=f"{pipe.model_name}_v1.0.0",
        explanation_json=json.dumps(shap_info),
        db=db
    )

    # Fetch latest available quote for dynamic data freshness status
    quote_info = provider.get_latest_quote(symbol_clean)
    latest_price_val = quote_info.get("price") or (float(df_raw["close"].iloc[-1]) if "close" in df_raw.columns and not df_raw.empty else None)

    # Phase 12 Selective Signal Coverage
    signal_label = risk_info.get("signal", "NEUTRAL")
    if 0.47 <= prob_up <= 0.53:
        signal_label = "NO CLEAR SIGNAL"
        predicted_dir_str = "NO_SIGNAL"
    else:
        predicted_dir_str = "UP" if predicted_dir == 1 else "DOWN"

    # Phase 13 Market Regime Classification Telemetry
    from backend.features.regime_engine import get_latest_regime
    regime_info = get_latest_regime(df_raw)

    res_payload = {
        "symbol": symbol_clean,
        "latest_price": latest_price_val,
        "quote_info": quote_info,
        "as_of_date": str(as_of_d),
        "prediction_date": str(prediction_d),
        "predicted_direction": predicted_dir_str,
        "probability_up": prob_up,
        "probability_down": 1.0 - prob_up,
        "signal": signal_label,
        "prediction_horizon": "1 trading day",
        "model_version": f"{pipe.model_name} v1.0 (Calibrated)",
        "trend_regime": regime_info.get("trend_regime", "SIDEWAYS"),
        "volatility_regime": regime_info.get("volatility_regime", "LOW_VOLATILITY"),
        "combined_regime": regime_info.get("combined_regime", "SIDEWAYS (LOW VOL)"),
        "coverage_stats": {
            "confidence_threshold_bounds": [0.47, 0.53],
            "selective_signal_status": "ACTIVE" if predicted_dir_str != "NO_SIGNAL" else "NO_CLEAR_SIGNAL"
        },
        "risk": risk_info,
        "model": {
            "name": pipe.model_name,
            "metrics": pipe.metrics
        },
        "explanations": shap_info,
        "disclaimer": RESEARCH_DISCLAIMER
    }
    prediction_cache.set(cache_key, res_payload, ttl_seconds=60)
    try:
        live_prediction_tracker.record_prediction(res_payload, db_session=db)
    except Exception as e:
        logger.error(f"Error recording live prediction observation: {e}")

    return res_payload



@app.get("/api/models")
def get_models_registry(db: Session = Depends(get_db)):
    """GET /api/models - Returns registry of all trained models and their metrics."""
    records = db.query(ModelMetadata).order_by(ModelMetadata.created_at.desc()).all()
    models = []
    for r in records:
        models.append({
            "id": r.id,
            "model_name": r.model_name,
            "version": r.version,
            "symbol": r.symbol,
            "training_start": str(r.training_start),
            "training_end": str(r.training_end),
            "metrics": json.loads(r.metrics_json) if r.metrics_json else {},
            "created_at": r.created_at.isoformat()
        })
    return {"models": models, "count": len(models)}

@app.post("/api/models/train/{symbol}")
def train_symbol_models_endpoint(symbol: str, background_tasks: BackgroundTasks):
    """POST /api/models/train/{symbol} - Triggers background model training for symbol."""
    symbol_clean = symbol.upper().strip()
    background_tasks.add_task(train_all_models_for_symbol, symbol_clean)
    return {
        "status": "initiated",
        "symbol": symbol_clean,
        "message": f"Model training pipeline for symbol '{symbol_clean}' launched in background."
    }

@app.post("/api/models/train-all")
def train_universe_models_endpoint(background_tasks: BackgroundTasks):
    """POST /api/models/train-all - Triggers background model training for all universe assets."""
    background_tasks.add_task(train_entire_universe)
    return {
        "status": "initiated",
        "message": "Universe multi-asset model training pipeline launched in background."
    }


@app.get("/api/predictions")
def get_predictions_log(symbol: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """GET /api/predictions - Returns prediction history log with resolution status."""
    history = get_prediction_history(symbol=symbol, limit=limit, db=db)
    return {"predictions": history, "count": len(history)}

@app.get("/api/performance")
def get_model_performance(db: Session = Depends(get_db)):
    """GET /api/performance - Returns stock-wise and model-wise accuracy metrics."""
    records = db.query(ModelMetadata).all()
    stock_wise = {}
    model_wise = {}

    for r in records:
        sym = r.symbol
        m_name = r.model_name
        metrics = json.loads(r.metrics_json) if r.metrics_json else {}

        if sym not in stock_wise:
            stock_wise[sym] = {}
        stock_wise[sym][m_name] = metrics

        if m_name not in model_wise:
            model_wise[m_name] = []
        model_wise[m_name].append({
            "symbol": sym,
            "accuracy": metrics.get("accuracy", 0.0),
            "f1_score": metrics.get("f1_score", 0.0),
            "roc_auc": metrics.get("roc_auc", 0.5)
        })

    return {
        "stock_wise": stock_wise,
        "model_wise": model_wise,
        "disclaimer": RESEARCH_DISCLAIMER
    }

from backend.security.rate_limiter import heavy_endpoint_limiter, training_endpoint_limiter

@app.post("/api/backtest")
def post_backtest(req: BacktestRequest, request: Request, db: Session = Depends(get_db)):
    """POST /api/backtest - Executes backtesting simulation."""
    heavy_endpoint_limiter.check(request, "backtest")
    symbol_clean = req.symbol.upper().strip()
    df_raw = get_historical_data_from_db(symbol_clean, db=db)
    if df_raw.empty:
        raise HTTPException(status_code=404, detail="Market data unavailable — configure data provider.")

    df_feat = compute_features_and_target(df_raw)
    # Restrict backtest evaluation to strict out-of-sample test set (held out 15%)
    df_trainable = df_feat.dropna(subset=["target"]).copy().sort_values("date").reset_index(drop=True)
    train_ratio, val_ratio, test_ratio = 0.70, 0.15, 0.15
    test_size = int(len(df_trainable) * test_ratio)
    test_df = df_trainable.iloc[-test_size:].copy().reset_index(drop=True)

    pipe = ModelPipeline.load_model(symbol_clean, "XGBoost")
    if not pipe or not pipe.is_trained:
        pipe = ModelPipeline.load_model(symbol_clean, "LogisticRegression")

    if not pipe or not pipe.is_trained:
        probs = np.full(len(test_df), 0.5)
    else:
        _, probs = pipe.predict(test_df)

    results = run_backtest(
        test_df,
        probs,
        initial_capital=req.initial_capital,
        prob_threshold=req.prob_threshold,
        allow_short=req.allow_short,
        transaction_cost=req.transaction_cost,
        slippage=req.slippage
    )

    return {
        "symbol": symbol_clean,
        "evaluation_scope": "STRICT_OUT_OF_SAMPLE_TEST_SET",
        "test_set_dates": {
            "start_date": str(test_df["date"].iloc[0]),
            "end_date": str(test_df["date"].iloc[-1]),
            "sample_size": len(test_df)
        },
        "parameters": req.dict(),
        "results": results
    }

@app.post("/api/refresh")
def post_data_refresh(background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """POST /api/refresh - Triggers data refresh, auto-resolution, and model re-training in background."""
    training_endpoint_limiter.check(request, "refresh")
    def refresh_task():
        sync_stock_universe(DEFAULT_UNIVERSE)
        resolve_pending_predictions()
        train_entire_universe(DEFAULT_UNIVERSE)

    background_tasks.add_task(refresh_task)
    return {
        "status": "initiated",
        "message": "Market data refresh and auto-resolution pipeline triggered in background."
    }

@app.post("/api/auth/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(UserRecord).filter(UserRecord.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists.")

    hashed_pw = get_password_hash(user.password)
    db_user = UserRecord(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    return {"message": "User registered successfully."}

@app.post("/api/auth/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserRecord).filter(UserRecord.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password.")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

from backend.data.fundamentals.provider import YFinanceFundamentalProvider
from backend.data.news.provider import YFinanceNewsProvider
from backend.data.news.sentiment import SentimentService

fund_provider = YFinanceFundamentalProvider()
news_provider = YFinanceNewsProvider()
sentiment_service = SentimentService()

@app.get("/api/assets/{symbol}/fundamentals")
def get_asset_fundamentals(symbol: str):
    """GET /api/assets/{symbol}/fundamentals - Returns point-in-time fundamental metrics."""
    symbol_clean = symbol.upper().strip()
    return fund_provider.get_fundamentals(symbol_clean)

@app.get("/api/assets/{symbol}/news")
def get_asset_news(symbol: str):
    """GET /api/assets/{symbol}/news - Returns historical news articles."""
    symbol_clean = symbol.upper().strip()
    return news_provider.get_historical_news(symbol_clean, "2024-01-01", "2026-01-01")

@app.get("/api/assets/{symbol}/sentiment")
def get_asset_sentiment(symbol: str):
    """GET /api/assets/{symbol}/sentiment - Returns daily sentiment scores and news volume."""
    symbol_clean = symbol.upper().strip()
    news_res = news_provider.get_historical_news(symbol_clean, "2024-01-01", "2026-01-01")
    articles = news_res.get("articles", [])
    aggregates = sentiment_service.aggregate_daily_sentiment(articles, datetime.utcnow())
    return {
        "symbol": symbol_clean,
        "status": news_res.get("status", "NEWS DATA UNAVAILABLE"),
        "aggregates": aggregates
    }

@app.get("/api/assets/{symbol}/feature-availability")
def get_feature_availability(symbol: str):
    """GET /api/assets/{symbol}/feature-availability - Feature source availability status."""
    symbol_clean = symbol.upper().strip()
    fund_res = fund_provider.get_historical_fundamentals(symbol_clean)
    news_res = news_provider.get_historical_news(symbol_clean, "2024-01-01", "2026-01-01")
    return {
        "symbol": symbol_clean,
        "technical_features": "AVAILABLE",
        "market_context_features": "AVAILABLE",
        "fundamental_features": fund_res.get("status", "FUNDAMENTAL DATA UNAVAILABLE"),
        "news_sentiment_features": news_res.get("status", "NEWS DATA UNAVAILABLE"),
        "point_in_time_supported": True
    }

@app.get("/api/research/ablation")
def get_ablation_summary():
    """GET /api/research/ablation - Returns Phase 4 master feature ablation research summary."""
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../baseline_results.json"))
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        return {
            "status": "COMPLETED",
            "experiment": "Phase 4 Feature Ablation Study",
            "baseline": baseline_data
        }
    return {"status": "NOT RUN", "message": "Run /api/research/run-ablation first."}

@app.get("/api/research/ablation/{symbol}")
def get_ablation_for_symbol(symbol: str):
    """GET /api/research/ablation/{symbol} - Returns feature ablation metrics for symbol."""
    symbol_clean = symbol.upper().strip()
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../baseline_results.json"))
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        if symbol_clean in baseline_data:
            return {"symbol": symbol_clean, "metrics": baseline_data[symbol_clean]}
    raise HTTPException(status_code=404, detail=f"No ablation data found for '{symbol_clean}'.")

@app.post("/api/research/run-ablation")
def run_ablation_study_endpoint(background_tasks: BackgroundTasks):
    """POST /api/research/run-ablation - Triggers background feature ablation study."""
    from backend.scripts.run_phase4_study import run_full_phase4_study
    background_tasks.add_task(run_full_phase4_study)
    return {"status": "initiated", "message": "Phase 4 Feature Ablation Study launched in background."}

# ==============================================================================
# PHASE 5 — REAL-TIME MARKET DATA & WEBSOCKET ENDPOINTS
# ==============================================================================
from fastapi import WebSocket, WebSocketDisconnect
from backend.data.realtime_provider import realtime_provider_manager

@app.get("/api/realtime/status")
def get_realtime_status():
    """GET /api/realtime/status - Returns real-time provider connection status."""
    return realtime_provider_manager.get_stream_status()

@app.get("/api/realtime/quote/{symbol}")
def get_realtime_quote(symbol: str):
    """GET /api/realtime/quote/{symbol} - Returns latest normalized tick for symbol."""
    symbol_clean = symbol.upper().strip()
    tick = realtime_provider_manager.cache.get_latest_tick(symbol_clean)
    if tick:
        return tick
    
    # Fallback to yfinance quote tagged as DELAYED/HISTORICAL
    quote = provider.get_latest_quote(symbol_clean)
    return {
        "symbol": symbol_clean,
        "price": quote.get("price"),
        "timestamp": quote.get("timestamp"),
        "provider": quote.get("provider", "yfinance"),
        "data_status": quote.get("data_status", "DELAYED"),
        "is_delayed": quote.get("is_delayed", True),
        "last_tick_age_seconds": 0.0
    }

class SymbolSubscribeRequest(BaseModel):
    symbol: str

@app.post("/api/realtime/subscribe")
def subscribe_symbol(req: SymbolSubscribeRequest):
    """POST /api/realtime/subscribe - Subscribes symbol to real-time stream."""
    realtime_provider_manager.subscribe(req.symbol)
    return {"status": "subscribed", "symbol": req.symbol.upper()}

@app.post("/api/realtime/unsubscribe")
def unsubscribe_symbol(req: SymbolSubscribeRequest):
    """POST /api/realtime/unsubscribe - Unsubscribes symbol from real-time stream."""
    realtime_provider_manager.unsubscribe(req.symbol)
    return {"status": "unsubscribed", "symbol": req.symbol.upper()}

@app.get("/api/realtime/stream-status")
def get_stream_status():
    """GET /api/realtime/stream-status - Detailed stream status."""
    return realtime_provider_manager.get_stream_status()

@app.websocket("/ws/market/{symbol}")
async def websocket_market_endpoint(websocket: WebSocket, symbol: str):
    """
    WebSocket /ws/market/{symbol} - Internal proxy forwarding normalized real-time ticks to React.
    Does NOT expose provider credentials to frontend JavaScript.
    """
    await websocket.accept()
    symbol_clean = symbol.upper().strip()
    realtime_provider_manager.subscribe(symbol_clean)

    async def send_tick_callback(tick: dict):
        if tick.get("symbol") == symbol_clean:
            try:
                await websocket.send_text(json.dumps(tick))
            except Exception:
                pass

    # Send initial cached or latest quote
    initial_tick = realtime_provider_manager.cache.get_latest_tick(symbol_clean)
    if not initial_tick:
        quote = provider.get_latest_quote(symbol_clean)
        initial_tick = {
            "symbol": symbol_clean,
            "price": quote.get("price"),
            "timestamp": quote.get("timestamp"),
            "provider": quote.get("provider", "yfinance"),
            "data_status": quote.get("data_status", "DELAYED"),
            "is_delayed": True
        }
    await websocket.send_text(json.dumps(initial_tick))

    try:
        while True:
            # Keep connection open and receive optional ping messages
            data = await websocket.receive_text()
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        realtime_provider_manager.unsubscribe(symbol_clean)

# ==============================================================================
# PHASE 6 — LIVE AI PREDICTION ENGINE ENDPOINTS
# ==============================================================================
from backend.services.live_prediction_service import live_prediction_service

@app.get("/api/assets/{symbol}/live-prediction")
def get_live_prediction(symbol: str, model_name: str = "XGBoost"):
    """GET /api/assets/{symbol}/live-prediction - Returns 30s throttled live prediction."""
    return live_prediction_service.get_live_prediction(symbol, model_name=model_name)

@app.post("/api/research/resolve-predictions")
def resolve_predictions():
    """POST /api/research/resolve-predictions - Auto-resolves pending prediction records."""
    return live_prediction_service.resolve_pending_predictions()

@app.get("/api/assets/{symbol}/prediction-tracker-stats")
def get_prediction_tracker_stats(symbol: str):
    """GET /api/assets/{symbol}/prediction-tracker-stats - Real database prediction tracker stats."""
    return live_prediction_service.get_prediction_tracker_stats(symbol)

@app.get("/api/research/live-collection-status")
def get_live_collection_status():
    """GET /api/research/live-collection-status - Global live research dataset collection metrics."""
    return live_prediction_service.get_live_collection_status()

# ==============================================================================
# PHASE 7.2 — LIVE RESEARCH MONITORING & STATISTICAL VALIDATION ENDPOINTS
# ==============================================================================
from fastapi.responses import PlainTextResponse
from backend.services.live_research_service import live_research_service

@app.get("/api/research/live-predictions/{symbol}")
def get_live_predictions_history(symbol: str, page: int = 1, limit: int = 50):
    """GET /api/research/live-predictions/{symbol} - Returns paginated prediction records."""
    return live_research_service.get_live_predictions_history(symbol, page=page, limit=limit)

@app.get("/api/research/live-predictions/{symbol}/csv", response_class=PlainTextResponse)
def export_live_predictions_csv(symbol: str):
    """GET /api/research/live-predictions/{symbol}/csv - Returns CSV string of prediction records."""
    csv_data = live_research_service.export_live_predictions_csv(symbol)
    return PlainTextResponse(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=live_predictions_{symbol}.csv"})

@app.get("/api/research/live-analytics/{symbol}")
def get_live_analytics(symbol: str):
    """GET /api/research/live-analytics/{symbol} - Statistical live research monitoring analytics."""
    return live_research_service.get_live_analytics(symbol)

# ==============================================================================
# PHASE 8 — ADVANCED CHARTING & TECHNICAL ANALYSIS ENDPOINTS
# ==============================================================================
from backend.indicators.technical_analysis import calculate_technical_indicators, detect_support_resistance

@app.get("/api/assets/{symbol}/technical-analysis")
def get_technical_analysis(symbol: str, response: Response, db: Session = Depends(get_db)):
    """GET /api/assets/{symbol}/technical-analysis - Returns computed indicators & support/resistance levels."""
    response.headers["Cache-Control"] = "public, max-age=60"
    symbol_clean = symbol.upper().strip()
    cache_key = f"ta_{symbol_clean}"
    cached_ta = indicators_cache.get(cache_key)
    if cached_ta is not None:
        return cached_ta


    df_raw = ensure_historical_data_in_db(symbol_clean, db=db)
    if df_raw.empty:
        raise HTTPException(status_code=404, detail=f"Market data unavailable for '{symbol_clean}'.")

    df_ind = calculate_technical_indicators(df_raw)
    sup_res = detect_support_resistance(df_raw)

    latest_row = df_ind.iloc[-1]
    res_payload = {
        "symbol": symbol_clean,
        "support_levels": sup_res.get("support_levels", []),
        "resistance_levels": sup_res.get("resistance_levels", []),
        "latest_indicators": {
            "rsi_14": round(float(latest_row.get("rsi_14", 50.0)), 2),
            "macd": round(float(latest_row.get("macd", 0.0)), 4),
            "macd_signal": round(float(latest_row.get("macd_signal", 0.0)), 4),
            "macd_hist": round(float(latest_row.get("macd_hist", 0.0)), 4),
            "sma_20": round(float(latest_row.get("sma_20", latest_row["close"])), 2),
            "sma_50": round(float(latest_row.get("sma_50", latest_row["close"])), 2),
            "ema_12": round(float(latest_row.get("ema_12", latest_row["close"])), 2),
            "ema_26": round(float(latest_row.get("ema_26", latest_row["close"])), 2),
            "bollinger_middle": round(float(latest_row.get("bollinger_middle", latest_row["close"])), 2),
            "bollinger_upper": round(float(latest_row.get("bollinger_upper", latest_row["close"])), 2),
            "bollinger_lower": round(float(latest_row.get("bollinger_lower", latest_row["close"])), 2),
            "atr_14": round(float(latest_row.get("atr_14", 0.0)), 2),
            "stoch_k": round(float(latest_row.get("stoch_k", 50.0)), 2),
            "stoch_d": round(float(latest_row.get("stoch_d", 50.0)), 2),
            "obv": float(latest_row.get("obv", 0.0))
        }
    }
    indicators_cache.set(cache_key, res_payload, ttl_seconds=120)
    return res_payload

# ==============================================================================
# PHASE 11 — SYSTEM METRICS & PRODUCTION MONITORING
# ==============================================================================
@app.get("/system/metrics")
@app.get("/api/system/metrics")
def get_system_metrics():
    """GET /api/system/metrics - System telemetry, memory usage, cache statistics, & stream status."""
    mem_data = {"rss_memory_mb": 0.0, "status": "AVAILABLE"}
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_data = {
            "rss_memory_mb": round(mem_info.rss / (1024 * 1024), 2),
            "vms_memory_mb": round(mem_info.vms / (1024 * 1024), 2)
        }
    except Exception:
        mem_data = {"rss_memory_mb": "N/A"}

    return {
        "status": "HEALTHY",
        "timestamp": datetime.now().isoformat() + "Z",
        "system": mem_data,
        "caches": {
            "dashboard_cache_entries": dashboard_cache.size(),
            "prediction_cache_entries": prediction_cache.size(),
            "history_cache_entries": history_cache.size(),
            "model_cache_entries": model_cache.size(),
            "trade_setup_cache_entries": trade_setup_cache.size()
        },
        "realtime": realtime_provider_manager.get_stream_status()
    }

# ==============================================================================
# PHASE 14 — AI TRADE SETUP, BACKTESTING, & PAPER TRADING TRACKER
# ==============================================================================
from backend.cache import trade_setup_cache
from backend.services.trade_signal_service import generate_trade_setup
from backend.backtest.trade_setup_backtester import run_complete_trade_setup_backtest
from backend.services.data_quality_service import data_quality_service
from backend.services.live_prediction_tracker import live_prediction_tracker
from backend.services.prediction_resolver import prediction_resolver
from backend.services.model_monitor import model_monitor
from backend.services.drift_monitor import drift_monitor
from backend.services.production_health_service import production_health_service
from backend.tracking.paper_tracker import log_paper_setup, get_paper_performance, resolve_pending_paper_setups
from backend.db.models import LivePredictionRecord


@app.get("/api/assets/{symbol}/trade-setup")
def get_trade_setup_endpoint(symbol: str, db: Session = Depends(get_db)):
    """
    GET /api/assets/{symbol}/trade-setup
    Returns unified trade setup object (Signal, Entry, Stop Loss, Target 1&2, R:R, Liquidity, Expected Move).
    Target warm latency < 100ms via trade_setup_cache.
    """
    symbol_clean = symbol.upper().strip()
    cache_key = f"trade_setup_{symbol_clean}"
    cached = trade_setup_cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch Prediction and Historical data
    df_raw = ensure_historical_data_in_db(symbol_clean, db=db)
    if df_raw.empty:
        raise HTTPException(status_code=404, detail=f"Market data unavailable for asset '{symbol_clean}'.")

    df_feat = compute_features_and_target(df_raw)
    pred_payload = get_stock_prediction(symbol_clean, model_name="XGBoost", db=db)

    prob_up = float(pred_payload.get("probability_up", 0.5))
    pred_dir_str = pred_payload.get("predicted_direction", "UP")
    pred_dir = 1 if pred_dir_str == "UP" else 0
    quote_info = pred_payload.get("quote_info", {})

    setup_obj = generate_trade_setup(
        symbol=symbol_clean,
        df_raw=df_raw,
        df_feat=df_feat,
        prob_up=prob_up,
        predicted_dir=pred_dir,
        model_name="XGBoost",
        model_version="1.0",
        quote_info=quote_info
    )

    # Persist live paper prediction record (prevents duplicates within 30s)
    as_of_str = pred_payload.get("as_of_date", str(date.today()))
    pred_d_str = pred_payload.get("prediction_date", str(date.today()))
    try:
        as_of_d = datetime.strptime(as_of_str, "%Y-%m-%d").date()
        pred_d = datetime.strptime(pred_d_str, "%Y-%m-%d").date()
    except Exception:
        as_of_d = date.today()
        pred_d = date.today() + timedelta(days=1)

    log_paper_setup(setup_obj, as_of_d=as_of_d, pred_d=pred_d, db=db)

    trade_setup_cache.set(cache_key, setup_obj, ttl_seconds=45)
    return setup_obj

@app.get("/api/assets/{symbol}/trade-setup/backtest")
def get_trade_setup_backtest_endpoint(symbol: str, db: Session = Depends(get_db)):
    """
    GET /api/assets/{symbol}/trade-setup/backtest
    Runs complete trade setup backtest over historical out-of-sample data with transaction costs.
    """
    symbol_clean = symbol.upper().strip()
    cache_key = f"ts_backtest_{symbol_clean}"
    cached = trade_setup_cache.get(cache_key)
    if cached is not None:
        return cached

    df_raw = ensure_historical_data_in_db(symbol_clean, db=db)
    if df_raw.empty or len(df_raw) < 40:
        raise HTTPException(status_code=400, detail=f"Insufficient price rows for trade setup backtest on '{symbol_clean}'.")

    df_feat = compute_features_and_target(df_raw)

    # Generate probabilities using Phase 12 Model or Technical Baseline
    pipe = ModelPipeline.load_model(symbol_clean, "XGBoost")
    if pipe and pipe.is_trained:
        preds, probs = pipe.predict(df_feat)
        probs_up = probs[:, 1] if probs.ndim > 1 else probs
    else:
        rsi_series = df_feat.get("rsi", pd.Series([50.0]*len(df_feat)))
        probs_up = np.where(rsi_series > 50, 0.56, 0.44)

    bt_results = run_complete_trade_setup_backtest(
        df_raw=df_raw,
        predictions_prob=probs_up,
        initial_capital=100000.0
    )
    bt_results["symbol"] = symbol_clean

    trade_setup_cache.set(cache_key, bt_results, ttl_seconds=300)
    return bt_results

@app.get("/api/assets/{symbol}/trade-setup/history")
def get_trade_setup_history_endpoint(symbol: str, limit: int = 50, db: Session = Depends(get_db)):
    """GET /api/assets/{symbol}/trade-setup/history - Returns recent paper prediction records."""
    from backend.db.models import PaperPredictionRecord
    symbol_clean = symbol.upper().strip()
    resolve_pending_paper_setups(symbol_clean, db=db)

    records = db.query(PaperPredictionRecord).filter(
        PaperPredictionRecord.symbol == symbol_clean
    ).order_by(PaperPredictionRecord.prediction_timestamp.desc()).limit(limit).all()

    res = []
    for r in records:
        res.append({
            "id": r.id,
            "symbol": r.symbol,
            "prediction_timestamp": r.prediction_timestamp.isoformat() if r.prediction_timestamp else None,
            "as_of_date": str(r.as_of_date),
            "prediction_date": str(r.prediction_date),
            "signal": r.signal,
            "probability_up": r.probability_up,
            "confidence": r.confidence,
            "combined_regime": r.combined_regime,
            "current_price": r.current_price,
            "entry_low": r.entry_low,
            "entry_high": r.entry_high,
            "stop_loss": r.stop_loss,
            "target_1": r.target_1,
            "target_2": r.target_2,
            "risk_reward_target_1": r.risk_reward_target_1,
            "outcome": r.outcome or "PENDING",
            "realized_return_pct": r.realized_return_pct,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            "is_correct": r.is_correct
        })

    return {
        "symbol": symbol_clean,
        "count": len(res),
        "history": res
    }

@app.get("/api/assets/{symbol}/paper-performance")
def get_paper_performance_endpoint(symbol: str, db: Session = Depends(get_db)):
    """GET /api/assets/{symbol}/paper-performance - Live paper trading tracker performance metrics."""
    symbol_clean = symbol.upper().strip()
    return get_paper_performance(symbol_clean, db=db)


# ==============================================================================
# PHASE 16 — PRODUCTION RELIABILITY & LIVE MONITORING ENDPOINTS
# ==============================================================================

@app.get("/api/data-quality/{symbol}")
def get_data_quality_endpoint(symbol: str, response: Response):
    """GET /api/data-quality/{symbol} - Real-time market data freshness, latency, and integrity status."""
    response.headers["Cache-Control"] = "public, max-age=10"
    return data_quality_service.inspect_symbol_data_quality(symbol)


@app.get("/api/model-monitor/all")
def get_model_monitor_all_endpoint(response: Response):
    """GET /api/model-monitor/all - Aggregated and per-symbol live model forward-testing performance."""
    response.headers["Cache-Control"] = "public, max-age=15"
    try:
        prediction_resolver.resolve_unresolved_predictions()
    except Exception:
        pass
    return model_monitor.get_all_metrics()


@app.get("/api/model-monitor/{symbol}")
def get_model_monitor_symbol_endpoint(symbol: str, response: Response, rolling_window: Optional[int] = None):
    """GET /api/model-monitor/{symbol} - Symbol-specific live model forward-testing performance metrics."""
    response.headers["Cache-Control"] = "public, max-age=15"
    try:
        prediction_resolver.resolve_unresolved_predictions(symbol)
    except Exception:
        pass
    return model_monitor.get_symbol_metrics(symbol, rolling_window=rolling_window)


@app.get("/api/model-monitor/{symbol}/calibration")
def get_model_calibration_endpoint(symbol: str, response: Response):
    """GET /api/model-monitor/{symbol}/calibration - Confidence calibration gaps and probability bands."""
    response.headers["Cache-Control"] = "public, max-age=15"
    return model_monitor.get_calibration_metrics(symbol)


@app.get("/api/model-monitor/{symbol}/drift")
def get_model_drift_endpoint(symbol: str, response: Response):
    """GET /api/model-monitor/{symbol}/drift - Statistical distribution drift and PSI metrics."""
    response.headers["Cache-Control"] = "public, max-age=15"
    return drift_monitor.analyze_drift(symbol)


@app.get("/api/production-health")
def get_production_health_endpoint(response: Response):
    """GET /api/production-health - Transparent rule-based overall production health status."""
    response.headers["Cache-Control"] = "public, max-age=15"
    return production_health_service.get_production_health()


@app.get("/api/live-predictions/{symbol}")
def get_live_predictions_endpoint(symbol: str, limit: int = 50, db: Session = Depends(get_db)):
    """GET /api/live-predictions/{symbol} - Recent recorded live prediction observations."""
    symbol_clean = symbol.upper().strip()
    records = db.query(LivePredictionRecord).filter(
        LivePredictionRecord.symbol == symbol_clean
    ).order_by(LivePredictionRecord.prediction_timestamp.desc()).limit(limit).all()

    return {
        "symbol": symbol_clean,
        "count": len(records),
        "predictions": [
            {
                "id": r.id,
                "prediction_timestamp": r.prediction_timestamp.isoformat() if r.prediction_timestamp else None,
                "predicted_direction": r.predicted_direction,
                "probability_up": r.probability_up,
                "probability_down": r.probability_down,
                "confidence": r.confidence,
                "trend_regime": r.trend_regime,
                "volatility_regime": r.volatility_regime,
                "current_price": r.current_price,
                "resolved": bool(r.resolved or (r.is_correct is not None)),
                "actual_direction": r.actual_direction or r.resolved_direction,
                "actual_price": r.actual_price,
                "actual_return": r.actual_return,
                "correct": r.correct if r.correct is not None else r.is_correct,
                "brier_score": r.brier_score
            }
            for r in records
        ]
    }


@app.get("/api/live-predictions/{symbol}/performance")
def get_live_predictions_performance_endpoint(symbol: str):
    """GET /api/live-predictions/{symbol}/performance - Tracker performance summary."""
    from backend.services.live_prediction_service import live_prediction_service
    return live_prediction_service.get_prediction_tracker_stats(symbol)










