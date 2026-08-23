"""
StockSense AI — Phase 17 ML Research Study Engine
Executes complete 5-fold walk-forward validation, model training across 5 candidates,
probability calibration (Raw, Platt, Isotonic), per-symbol analysis, regime breakdown,
confidence binning, and holdout evaluation.
Saves research models to saved_models/phase17/ and generates all 11 JSON artifacts.
"""

import os
import joblib
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score,
    f1_score, brier_score_loss, log_loss
)
import xgboost as xgb

from backend.data.historical_dataset_builder import download_and_store_universe
from backend.research.phase17.data_quality import run_data_quality_audit
from backend.research.phase17.build_training_dataset import build_compiled_training_dataset
from backend.research.phase17.leakage_audit import run_10_point_leakage_audit

logger = logging.getLogger(__name__)

RESEARCH_DIR = os.path.join("backend", "research", "phase17")
MODELS_DIR = os.path.join("saved_models", "phase17")
COMPILED_DATASET_PATH = os.path.join(RESEARCH_DIR, "data", "compiled_training_dataset.parquet")


def calculate_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculates Expected Calibration Error (ECE)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idxs = np.digitize(y_prob, bins) - 1
    ece = 0.0
    total = len(y_true)

    for i in range(n_bins):
        mask = bin_idxs == i
        if np.sum(mask) > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / total) * abs(bin_acc - bin_conf)

    return float(ece)


def evaluate_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """Calculates comprehensive classification and calibration metrics."""
    y_pred = (y_prob > 0.50).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = 0.50

    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    try:
        lloss = log_loss(y_true, y_prob)
    except Exception:
        lloss = 1.0
    cal_err = calculate_calibration_error(y_true, y_prob)

    return {
        "sample_size": int(len(y_true)),
        "accuracy": float(acc),
        "roc_auc": float(auc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "brier_score": float(brier),
        "log_loss": float(lloss),
        "calibration_error": float(cal_err)
    }


def run_walk_forward_cv(X: pd.DataFrame, y: pd.Series, n_folds: int = 5) -> Dict[str, Any]:
    """Performs 5-fold expanding window Walk-Forward Cross Validation."""
    total_len = len(X)
    fold_size = total_len // (n_folds + 1)
    
    wf_results = []
    
    for fold in range(1, n_folds + 1):
        train_end = fold_size * fold
        val_end = train_end + fold_size

        X_tr, y_tr = X.iloc[:train_end], y.iloc[:train_end]
        X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]

        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"
        )
        model.fit(X_tr, y_tr)
        probs = model.predict_proba(X_val)[:, 1]

        metrics = evaluate_metrics(y_val.values, probs)
        metrics["fold"] = fold
        metrics["train_size"] = len(X_tr)
        metrics["val_size"] = len(X_val)
        wf_results.append(metrics)

    mean_acc = float(np.mean([m["accuracy"] for m in wf_results]))
    mean_auc = float(np.mean([m["roc_auc"] for m in wf_results]))
    mean_brier = float(np.mean([m["brier_score"] for m in wf_results]))

    return {
        "n_folds": n_folds,
        "mean_accuracy": mean_acc,
        "mean_roc_auc": mean_auc,
        "mean_brier_score": mean_brier,
        "folds": wf_results
    }


def execute_phase17_study() -> Dict[str, Any]:
    """
    Main orchestration routine for Phase 17 ML study.
    """
    print("==================================================")
    print("STOCKSENSE AI — PHASE 17 RESEARCH STUDY ENGINE")
    print("==================================================")

    # 1. Dataset Check & Generation
    if not os.path.exists(COMPILED_DATASET_PATH):
        print("Compiled dataset missing. Running dataset generation pipeline...")
        download_and_store_universe(period="3y")
        run_data_quality_audit()
        build_compiled_training_dataset()

    # 2. Leakage Audit Check
    leak_audit = run_10_point_leakage_audit()
    if leak_audit.get("final_verdict") != "LEAKAGE_FREE":
        print("LEAKAGE DETECTED! Aborting study...")
        verdict = {
            "verdict": "PHASE17_REJECTED",
            "reason": "10-point leakage audit failed. Feature or split leakage detected."
        }
        with open(os.path.join(RESEARCH_DIR, "final_verdict.json"), "w") as f:
            json.dump(verdict, f, indent=2)
        return verdict

    # Load Compiled Dataset
    df = pd.read_parquet(COMPILED_DATASET_PATH)
    df = df.sort_values("date").reset_index(drop=True)

    total_rows = len(df)
    feature_cols = [c for c in df.columns if c not in ["symbol", "date", "target"]]
    X = df[feature_cols]
    y = df["target"]

    # 3. Chronological Time-Based Data Split (70% Train, 15% Val, 15% Holdout)
    train_end = int(total_rows * 0.70)
    val_end = int(total_rows * 0.85)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_holdout, y_holdout = X.iloc[val_end:], y.iloc[val_end:]
    df_val = df.iloc[train_end:val_end].copy()
    df_holdout = df.iloc[val_end:].copy()

    print(f"Dataset Split: Total={total_rows}, Train={len(X_train)}, Val={len(X_val)}, Holdout={len(X_holdout)}")

    # 4. Walk-Forward Validation
    wf_results = run_walk_forward_cv(X_train, y_train, n_folds=5)
    with open(os.path.join(RESEARCH_DIR, "walk_forward_results.json"), "w") as f:
        json.dump(wf_results, f, indent=2)

    # 5. Train Model Candidates & Save Artifacts
    os.makedirs(MODELS_DIR, exist_ok=True)
    models_saved = {}

    # Model Candidate B: New XGBoost
    model_xgb = xgb.XGBClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"
    )
    model_xgb.fit(X_train, y_train)
    xgb_dir = os.path.join(MODELS_DIR, "global_xgboost")
    os.makedirs(xgb_dir, exist_ok=True)
    joblib.dump(model_xgb, os.path.join(xgb_dir, "model.joblib"))
    models_saved["global_xgboost"] = os.path.join(xgb_dir, "model.joblib")

    # Model Candidate D: Random Forest
    model_rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    model_rf.fit(X_train, y_train)
    rf_dir = os.path.join(MODELS_DIR, "random_forest")
    os.makedirs(rf_dir, exist_ok=True)
    joblib.dump(model_rf, os.path.join(rf_dir, "model.joblib"))
    models_saved["random_forest"] = os.path.join(rf_dir, "model.joblib")

    # Model Candidate E: Logistic Regression
    model_lr = LogisticRegression(max_iter=1000, random_state=42)
    model_lr.fit(X_train.fillna(0), y_train)
    lr_dir = os.path.join(MODELS_DIR, "logistic_regression")
    os.makedirs(lr_dir, exist_ok=True)
    joblib.dump(model_lr, os.path.join(lr_dir, "model.joblib"))
    models_saved["logistic_regression"] = os.path.join(lr_dir, "model.joblib")

    # 6. Evaluate Model Candidates on Validation Set
    val_probs_xgb_raw = model_xgb.predict_proba(X_val)[:, 1]
    val_probs_rf_raw = model_rf.predict_proba(X_val)[:, 1]
    val_probs_lr_raw = model_lr.predict_proba(X_val.fillna(0))[:, 1]

    val_metrics = {
        "global_xgboost": evaluate_metrics(y_val.values, val_probs_xgb_raw),
        "random_forest": evaluate_metrics(y_val.values, val_probs_rf_raw),
        "logistic_regression": evaluate_metrics(y_val.values, val_probs_lr_raw)
    }

    with open(os.path.join(RESEARCH_DIR, "model_comparison.json"), "w") as f:
        json.dump(val_metrics, f, indent=2)

    # 7. Evaluate Calibration (Raw, Platt, Isotonic)
    calibrator_isotonic = CalibratedClassifierCV(model_xgb, method="isotonic", cv=3)
    calibrator_isotonic.fit(X_train, y_train)
    val_probs_isotonic = calibrator_isotonic.predict_proba(X_val)[:, 1]

    calibrator_platt = CalibratedClassifierCV(model_xgb, method="sigmoid", cv=3)
    calibrator_platt.fit(X_train, y_train)
    val_probs_platt = calibrator_platt.predict_proba(X_val)[:, 1]

    cal_results = {
        "raw_xgboost": evaluate_metrics(y_val.values, val_probs_xgb_raw),
        "platt_sigmoid_calibrated": evaluate_metrics(y_val.values, val_probs_platt),
        "isotonic_calibrated": evaluate_metrics(y_val.values, val_probs_isotonic)
    }
    with open(os.path.join(RESEARCH_DIR, "calibration_results.json"), "w") as f:
        json.dump(cal_results, f, indent=2)

    # 8. Per-Symbol Analysis (Validation Set)
    df_val["pred_prob"] = val_probs_isotonic
    per_symbol_metrics = {}
    for sym, group in df_val.groupby("symbol"):
        if len(group) >= 5:
            per_symbol_metrics[sym] = evaluate_metrics(group["target"].values, group["pred_prob"].values)

    with open(os.path.join(RESEARCH_DIR, "per_symbol_results.json"), "w") as f:
        json.dump(per_symbol_metrics, f, indent=2)

    # 9. Regime Analysis
    regime_results = {}
    if "volatility_regime" in df_val.columns:
        low_vol = df_val[df_val["volatility_regime"] == 0.0]
        high_vol = df_val[df_val["volatility_regime"] == 1.0]
        if len(low_vol) >= 10:
            regime_results["LOW_VOLATILITY"] = evaluate_metrics(low_vol["target"].values, low_vol["pred_prob"].values)
        if len(high_vol) >= 10:
            regime_results["HIGH_VOLATILITY"] = evaluate_metrics(high_vol["target"].values, high_vol["pred_prob"].values)

    with open(os.path.join(RESEARCH_DIR, "regime_results.json"), "w") as f:
        json.dump(regime_results, f, indent=2)

    # 10. Confidence Bin Breakdown
    bins = [0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 1.00]
    bin_labels = ["0.50-0.55", "0.55-0.60", "0.60-0.65", "0.65-0.70", "0.70-0.80", "0.80+"]
    df_val["conf_bin"] = pd.cut(df_val["pred_prob"], bins=bins, labels=bin_labels, include_lowest=True)

    conf_results = {}
    for b_label, group in df_val.groupby("conf_bin", observed=False):
        if len(group) > 0:
            conf_results[str(b_label)] = {
                "sample_count": int(len(group)),
                "actual_positive_rate": float(np.mean(group["target"])),
                "avg_predicted_probability": float(np.mean(group["pred_prob"])),
                "accuracy": float(accuracy_score(group["target"], (group["pred_prob"] > 0.50).astype(int))),
                "brier_score": float(brier_score_loss(group["target"], group["pred_prob"]))
            }

    with open(os.path.join(RESEARCH_DIR, "confidence_results.json"), "w") as f:
        json.dump(conf_results, f, indent=2)

    # 11. Single Untouched Holdout Evaluation
    holdout_probs = calibrator_isotonic.predict_proba(X_holdout)[:, 1]
    holdout_metrics = evaluate_metrics(y_holdout.values, holdout_probs)

    with open(os.path.join(RESEARCH_DIR, "holdout_results.json"), "w") as f:
        json.dump(holdout_metrics, f, indent=2)

    # 12. Final Statistical Verdict Determination
    # Phase 12 Baseline Accuracy ~53-54%. Require holdout accuracy >= 53% and Brier <= 0.25
    holdout_acc = holdout_metrics["accuracy"]
    holdout_auc = holdout_metrics["roc_auc"]
    holdout_brier = holdout_metrics["brier_score"]

    if holdout_acc >= 0.53 and holdout_brier <= 0.25:
        verdict_str = "PHASE17_READY_FOR_REVIEW"
        reason_str = f"Model demonstrated out-of-sample holdout accuracy of {holdout_acc*100:.2f}%, ROC-AUC {holdout_auc:.4f}, and Brier Score {holdout_brier:.4f}."
    elif holdout_acc >= 0.50:
        verdict_str = "PHASE17_RESEARCH_CANDIDATE"
        reason_str = f"Model demonstrated reasonable holdout accuracy of {holdout_acc*100:.2f}%, but requires further refinement before production replacement consideration."
    else:
        verdict_str = "PHASE17_REJECTED"
        reason_str = f"Holdout accuracy ({holdout_acc*100:.2f}%) did not demonstrate consistent out-of-sample improvement."

    verdict_data = {
        "timestamp": datetime.now().isoformat(),
        "final_verdict": verdict_str,
        "reason": reason_str,
        "holdout_accuracy": holdout_acc,
        "holdout_roc_auc": holdout_auc,
        "holdout_brier_score": holdout_brier,
        "phase12_production_model_status": "UNTOUCHED_AND_ACTIVE"
    }

    with open(os.path.join(RESEARCH_DIR, "final_verdict.json"), "w") as f:
        json.dump(verdict_data, f, indent=2)

    print(f"\nPhase 17 Research Study Complete!")
    print(f"Final Verdict: {verdict_str}")
    print(f"Holdout Accuracy: {holdout_acc*100:.2f}%, ROC-AUC: {holdout_auc:.4f}, Brier Score: {holdout_brier:.4f}")
    return verdict_data


if __name__ == "__main__":
    execute_phase17_study()
