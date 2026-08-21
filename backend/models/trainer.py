import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.config import DEFAULT_UNIVERSE, TRAIN_RATIO, VAL_RATIO, TEST_RATIO, PROJECT_ROOT
from backend.db.database import SessionLocal, init_db
from backend.db.models import ModelMetadata, FeatureRecord
from backend.data.data_service import get_historical_data_from_db, sync_stock_universe
from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS
from backend.models.splitter import chronological_split
from backend.models.baseline_models import ModelPipeline, evaluate_predictions
from backend.models.lstm_model import LSTMPipeline
from backend.models.ensemble_model import EnsemblePipeline

def train_all_models_for_symbol(symbol: str) -> Dict[str, Any]:
    """
    Executes model training pipeline following strict TRAINING ORDER (Refinement 9):
    1. Data Ingestion & Retrieval
    2. Feature Engineering & Target Construction
    3. Chronological Split (Train 70%, Val 15%, Test 15%)
    4. Logistic Regression Baseline
    5. Random Forest Baseline
    6. XGBoost Baseline
    7. Evaluation on Validation Set
    8. PyTorch LSTM Sequence Classifier
    9. Calibrated Probability Ensemble Model
    10. Evaluation on Test Set & DB Metadata persistence
    """
    symbol_clean = symbol.upper().strip()
    df_raw = get_historical_data_from_db(symbol_clean)

    if df_raw.empty:
        raise ValueError(f"No historical market data found in database for '{symbol_clean}'. Run data sync first.")

    df_feat = compute_features_and_target(df_raw)
    if df_feat.empty or len(df_feat) < 100:
        raise ValueError(f"Insufficient feature data ({len(df_feat)} rows) to train models for '{symbol_clean}'.")

    # Save feature records to SQLite using bulk operations
    from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
    from backend.cache import prediction_cache, model_cache
    db = SessionLocal()
    try:
        feat_records = []
        for row in df_feat.to_dict(orient="records"):
            target_val = int(row["target"]) if pd.notnull(row.get("target")) else None
            feat_records.append({
                "symbol": symbol_clean,
                "date": row["date"],
                "sma_10": float(row["sma_10"]),
                "sma_20": float(row["sma_20"]),
                "sma_50": float(row["sma_50"]),
                "ema_10": float(row["ema_10"]),
                "ema_20": float(row["ema_20"]),
                "rsi": float(row["rsi"]),
                "macd": float(row["macd"]),
                "macd_signal": float(row["macd_signal"]),
                "macd_hist": float(row["macd_hist"]),
                "bb_upper": float(row["bb_upper"]),
                "bb_lower": float(row["bb_lower"]),
                "bb_width": float(row["bb_width"]),
                "daily_return": float(row["daily_return"]),
                "rolling_volatility": float(row["rolling_volatility"]),
                "volume_change": float(row["volume_change"]),
                "target": target_val
            })

        if feat_records:
            stmt = sqlite_upsert(FeatureRecord)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["symbol", "date"],
                set_={
                    "sma_10": stmt.excluded.sma_10,
                    "sma_20": stmt.excluded.sma_20,
                    "sma_50": stmt.excluded.sma_50,
                    "ema_10": stmt.excluded.ema_10,
                    "ema_20": stmt.excluded.ema_20,
                    "rsi": stmt.excluded.rsi,
                    "macd": stmt.excluded.macd,
                    "macd_signal": stmt.excluded.macd_signal,
                    "macd_hist": stmt.excluded.macd_hist,
                    "bb_upper": stmt.excluded.bb_upper,
                    "bb_lower": stmt.excluded.bb_lower,
                    "bb_width": stmt.excluded.bb_width,
                    "daily_return": stmt.excluded.daily_return,
                    "rolling_volatility": stmt.excluded.rolling_volatility,
                    "volume_change": stmt.excluded.volume_change,
                    "target": stmt.excluded.target
                }
            )
            db.execute(upsert_stmt, feat_records)
            db.commit()
    finally:
        db.close()


    # Filter out rows with target = NaN for training
    df_trainable = df_feat.dropna(subset=["target"]).copy()
    train_df, val_df, test_df = chronological_split(df_trainable, TRAIN_RATIO, VAL_RATIO, TEST_RATIO)

    trained_models = {}

    # 1. Majority Class Baseline
    maj_pipe = ModelPipeline("MajorityBaseline", symbol_clean)
    maj_metrics = maj_pipe.train(train_df, val_df)
    trained_models["MajorityBaseline"] = maj_pipe

    # 2. Logistic Regression
    lr_pipe = ModelPipeline("LogisticRegression", symbol_clean)
    lr_metrics = lr_pipe.train(train_df, val_df)
    trained_models["LogisticRegression"] = lr_pipe

    # 3. Random Forest
    rf_pipe = ModelPipeline("RandomForest", symbol_clean)
    rf_metrics = rf_pipe.train(train_df, val_df)
    trained_models["RandomForest"] = rf_pipe

    # 4. XGBoost
    xgb_pipe = ModelPipeline("XGBoost", symbol_clean)
    xgb_metrics = xgb_pipe.train(train_df, val_df)
    trained_models["XGBoost"] = xgb_pipe

    # 5. PyTorch LSTM
    lstm_pipe = LSTMPipeline(symbol_clean)
    try:
        lstm_metrics = lstm_pipe.train(train_df, val_df, epochs=20)
        trained_models["LSTM"] = lstm_pipe
    except Exception as e:
        print(f"LSTM training failed for {symbol_clean}: {e}")

    # 6. Probability Ensemble Model
    ens_pipe = EnsemblePipeline(symbol_clean)
    ens_pipe.fit_weights_from_val(val_df, trained_models)
    
    # Evaluate Ensemble on Validation Set
    ens_preds, ens_probs = ens_pipe.predict(val_df, trained_models)
    ens_metrics = evaluate_predictions(val_df["target"].values.astype(int), ens_preds, ens_probs)
    ens_pipe.metrics = ens_metrics
    trained_models["Ensemble"] = ens_pipe

    # Test Set Evaluation (Held out until final evaluation)
    test_eval_results = {}
    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df["target"].values.astype(int)

    for name, m in trained_models.items():
        if name == "Ensemble":
            preds, probs = ens_pipe.predict(test_df, trained_models)
        elif name == "LSTM":
            preds, probs = m.predict(test_df)
            if len(preds) < len(y_test):
                pad = len(y_test) - len(preds)
                y_test_sub = y_test[pad:]
                test_eval_results[name] = evaluate_predictions(y_test_sub, preds, probs)
                continue
        else:
            preds, probs = m.predict(test_df)

        test_eval_results[name] = evaluate_predictions(y_test, preds, probs)

    # Persist model metadata in SQLite DB
    db = SessionLocal()
    try:
        training_start_date = train_df["date"].iloc[0]
        training_end_date = train_df["date"].iloc[-1]

        from backend.assets.asset_registry import get_asset_info
        asset_info = get_asset_info(symbol_clean)
        aclass = asset_info["asset_class"] if asset_info else "INDIAN_EQUITY"

        for name, m in trained_models.items():
            metrics_dict = test_eval_results.get(name, m.metrics if hasattr(m, "metrics") else {})
            meta = ModelMetadata(
                model_name=name,
                version="v1.0.0",
                symbol=symbol_clean,
                asset_class=aclass,
                training_start=training_start_date,
                training_end=training_end_date,
                features_list=json.dumps(FEATURE_COLUMNS),
                hyperparameters=json.dumps({"model_type": name, "symbol": symbol_clean}),
                metrics_json=json.dumps(metrics_dict),
                file_path=f"saved_models/{symbol_clean}_{name}.joblib",
                created_at=datetime.utcnow()
            )
            db.add(meta)
        db.commit()

        # Write metadata.json for artifact registry
        asset_dir = os.path.join(PROJECT_ROOT, "saved_models", symbol_clean)
        os.makedirs(asset_dir, exist_ok=True)
        meta_json_path = os.path.join(asset_dir, "metadata.json")
        meta_content = {
            "symbol": symbol_clean,
            "asset_class": aclass,
            "trained_at": datetime.utcnow().isoformat(),
            "training_period": {
                "start": str(training_start_date),
                "end": str(training_end_date)
            },
            "features_used": FEATURE_COLUMNS,
            "test_metrics": test_eval_results
        }
        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(meta_content, f, indent=2)

        # Invalidate prediction cache for this symbol so fresh predictions use new model
        prediction_cache.invalidate(symbol_clean)
        model_cache.invalidate(symbol_clean)

    finally:
        db.close()

    return {
        "symbol": symbol_clean,
        "validation_metrics": {name: m.metrics for name, m in trained_models.items() if hasattr(m, "metrics")},
        "test_metrics": test_eval_results,
        "trained_models": trained_models
    }


def train_entire_universe(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Syncs market data and trains models for all stocks in initial universe."""
    if symbols is None:
        symbols = DEFAULT_UNIVERSE

    print("Step 1: Syncing real market data (if needed)...")
    try:
        sync_stock_universe(symbols)
    except Exception as e:
        print(f"Market data sync skipped or network unavailable: {e}. Proceeding with stored SQLite data.")

    print("Step 2: Training baseline, LSTM, and ensemble models...")
    universe_results = {}
    for sym in symbols:
        print(f"--- Training models for {sym} ---")
        try:
            res = train_all_models_for_symbol(sym)
            universe_results[sym] = res
        except Exception as e:
            print(f"Error training {sym}: {e}")
            universe_results[sym] = {"error": str(e)}

    # Generate docs/model_evaluation.md
    generate_model_evaluation_report(universe_results)
    return universe_results

def generate_model_evaluation_report(universe_results: Dict[str, Any]):
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs"))
    os.makedirs(docs_dir, exist_ok=True)
    report_file = os.path.join(docs_dir, "model_evaluation.md")

    md = "# StockSense AI — Model Evaluation & Performance Report\n\n"
    md += "> **IMPORTANT**: Metrics reported below are strictly empirical evaluations on the held-out 15% test set. Higher model accuracy on historical data does not guarantee future financial returns.\n\n"

    for sym, res in universe_results.items():
        md += f"## Stock: {sym}\n\n"
        if "test_metrics" in res:
            md += "| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |\n"
            md += "|---|---|---|---|---|---|---|\n"
            for model_name, metrics in res["test_metrics"].items():
                acc = metrics.get("accuracy", 0.0) * 100.0
                prec = metrics.get("precision", 0.0) * 100.0
                rec = metrics.get("recall", 0.0) * 100.0
                f1 = metrics.get("f1_score", 0.0)
                auc = metrics.get("roc_auc", 0.5)
                brier = metrics.get("brier_score", 0.0)
                md += f"| **{model_name}** | {acc:.2f}% | {prec:.2f}% | {rec:.2f}% | {f1:.4f} | {auc:.4f} | {brier:.4f} |\n"
            md += "\n"
        else:
            md += f"*Training failed or insufficient data: {res.get('error', 'Unknown error')}*\n\n"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Model evaluation report written to {report_file}")
