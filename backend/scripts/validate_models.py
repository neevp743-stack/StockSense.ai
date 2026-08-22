import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from backend.config import PROJECT_ROOT
from backend.db.database import SessionLocal
from backend.data.data_service import ensure_historical_data_in_db
from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS
from backend.models.splitter import chronological_split
from backend.models.baseline_models import ModelPipeline, evaluate_predictions, MajorityClassBaseline

VALIDATION_DIR = os.path.join(PROJECT_ROOT, "backend", "research", "ml_validation")
os.makedirs(VALIDATION_DIR, exist_ok=True)

TARGET_ASSETS = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]

def evaluate_previous_direction_baseline(y_true: np.ndarray, prev_returns: np.ndarray) -> Dict[str, Any]:
    """Previous-Direction Baseline: predicts price will continue in direction of past return."""
    y_pred = (prev_returns > 0).astype(int)
    y_prob = np.where(prev_returns > 0, 0.7, 0.3)
    return evaluate_predictions(y_true, y_pred, y_prob)

def validate_and_benchmark_asset(symbol: str) -> Dict[str, Any]:
    clean_symbol = symbol.upper().strip()
    db = SessionLocal()
    try:
        df_raw = ensure_historical_data_in_db(clean_symbol, db=db)
        if df_raw.empty or len(df_raw) < 100:
            return {"symbol": clean_symbol, "status": "INSUFFICIENT_DATA"}

        df_feat = compute_features_and_target(df_raw)
        df_trainable = df_feat.dropna(subset=["target"] + FEATURE_COLUMNS).copy().sort_values("date").reset_index(drop=True)

        if len(df_trainable) < 100:
            return {"symbol": clean_symbol, "status": "INSUFFICIENT_FEATURE_ROWS"}

        # Strict Chronological 70/15/15 split
        train_df, val_df, test_df = chronological_split(df_trainable, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)

        # 1. Train XGBoost Model Pipeline
        pipe = ModelPipeline("XGBoost", clean_symbol)
        train_metrics = pipe.train(train_df, val_df)

        # 2. Out-of-Sample Test Set Evaluation
        test_preds, test_probs = pipe.predict(test_df)
        y_test = test_df["target"].values.astype(int)
        model_test_metrics = evaluate_predictions(y_test, test_preds, test_probs)

        # 3. Majority Class Baseline on Test Set
        maj_base = MajorityClassBaseline().fit(train_df[FEATURE_COLUMNS].values, train_df["target"].values.astype(int))
        maj_preds = maj_base.predict(test_df[FEATURE_COLUMNS].values)
        maj_probs = maj_base.predict_proba(test_df[FEATURE_COLUMNS].values)[:, 1]
        maj_metrics = evaluate_predictions(y_test, maj_preds, maj_probs)

        # 4. Previous Direction Baseline on Test Set
        prev_returns = test_df["daily_return"].values
        prev_dir_metrics = evaluate_previous_direction_baseline(y_test, prev_returns)

        # Save model & metadata artifact
        extra_meta = {
            "chronological_split": {
                "train_rows": len(train_df),
                "val_rows": len(val_df),
                "test_rows": len(test_df),
                "train_dates": [str(train_df["date"].iloc[0]), str(train_df["date"].iloc[-1])],
                "val_dates": [str(val_df["date"].iloc[0]), str(val_df["date"].iloc[-1])],
                "test_dates": [str(test_df["date"].iloc[0]), str(test_df["date"].iloc[-1])],
            },
            "test_out_of_sample_metrics": model_test_metrics,
            "majority_baseline_metrics": maj_metrics,
            "prev_dir_baseline_metrics": prev_dir_metrics
        }
        pipe.save_model(extra_meta=extra_meta)

        report = {
            "symbol": clean_symbol,
            "validated_at": datetime.utcnow().isoformat() + "Z",
            "evaluation_methodology": "STRICT_CHRONOLOGICAL_OUT_OF_SAMPLE_HOLDOUT",
            "chronological_periods": extra_meta["chronological_split"],
            "model_performance": {
                "model_name": "XGBoost (Calibrated)",
                "out_of_sample_test_metrics": model_test_metrics
            },
            "baseline_comparisons": {
                "majority_class_baseline": maj_metrics,
                "previous_direction_baseline": prev_dir_metrics
            },
            "outperforming_majority_baseline": model_test_metrics["accuracy"] >= maj_metrics["accuracy"],
            "calibration": {
                "brier_score": model_test_metrics["brier_score"],
                "interpretation": "Brier score measures probability calibration accuracy (lower is better, 0.0 is perfect)."
            },
            "disclaimer": "Educational and research purposes only. Past accuracy does not guarantee future financial returns."
        }

        # Write validation JSON report artifact
        json_path = os.path.join(VALIDATION_DIR, f"{clean_symbol}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    finally:
        db.close()

def run_all_validations():
    print("==================================================")
    print("RUNNING PHASE 11 ML VALIDATION & BASELINE BENCHMARK")
    print("==================================================")
    summary = {}
    for sym in TARGET_ASSETS:
        print(f"Validating asset: {sym:10s}...")
        res = validate_and_benchmark_asset(sym)
        summary[sym] = res.get("model_performance", {}).get("out_of_sample_test_metrics", {})
        acc = summary[sym].get("accuracy", "N/A")
        f1 = summary[sym].get("f1_score", "N/A")
        print(f"  -> Acc: {acc} | F1: {f1}")

    print("\nML Validation Complete! Reports saved to backend/research/ml_validation/")
    return summary

if __name__ == "__main__":
    run_all_validations()
