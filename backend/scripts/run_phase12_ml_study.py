import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss, confusion_matrix

from backend.config import PROJECT_ROOT
from backend.db.database import SessionLocal
from backend.data.data_service import ensure_historical_data_in_db
from backend.features.feature_engine import compute_features_and_target, FEATURE_GROUPS, FEATURE_COLUMNS_V1, FEATURE_COLUMNS_V2
from backend.models.splitter import chronological_split, WalkForwardSplitter
from backend.models.baseline_models import ModelPipeline, evaluate_predictions, MajorityClassBaseline

RESEARCH_DIR = os.path.join(PROJECT_ROOT, "backend", "research", "phase12")
os.makedirs(RESEARCH_DIR, exist_ok=True)

TARGET_ASSETS = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]

# Phase 11 Verified Baseline Numbers
PHASE11_BASELINE = {
    "RELIANCE": {"accuracy": 0.4667, "roc_auc": 0.4697, "brier_score": 0.2514, "f1_score": 0.6336},
    "INFY":     {"accuracy": 0.5500, "roc_auc": 0.5401, "brier_score": 0.2482, "f1_score": 0.3415},
    "TCS":      {"accuracy": 0.5167, "roc_auc": 0.5262, "brier_score": 0.2494, "f1_score": 0.5297},
    "AAPL":     {"accuracy": 0.5507, "roc_auc": 0.5512, "brier_score": 0.2471, "f1_score": 0.6990},
    "NVDA":     {"accuracy": 0.4493, "roc_auc": 0.4412, "brier_score": 0.2520, "f1_score": 0.5778},
    "BTC-USD":  {"accuracy": 0.5049, "roc_auc": 0.5186, "brier_score": 0.2501, "f1_score": 0.4950}
}

def train_eval_xgb(X_tr: np.ndarray, y_tr: np.ndarray, X_va: np.ndarray, y_va: np.ndarray, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Fits calibrated XGBoost model and returns evaluation metrics."""
    default_p = {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 42, "eval_metric": "logloss"}
    if params:
        default_p.update(params)

    base = XGBClassifier(**default_p)
    model = CalibratedClassifierCV(estimator=base, cv=3)
    model.fit(X_tr, y_tr)
    
    probs = model.predict_proba(X_va)[:, 1]
    preds = (probs >= 0.5).astype(int)
    return evaluate_predictions(y_va, preds, probs), model, probs

def run_feature_ablation_study(df_trainable: pd.DataFrame) -> Dict[str, Any]:
    """Tests Base vs Technical vs Momentum vs Volatility vs Volume vs Regime vs All on train/val split."""
    train_df, val_df, _ = chronological_split(df_trainable, 0.70, 0.15, 0.15)
    y_tr = train_df["target"].values.astype(int)
    y_va = val_df["target"].values.astype(int)

    results = {}
    for group_name, cols in FEATURE_GROUPS.items():
        avail_cols = [c for c in cols if c in train_df.columns]
        X_tr = train_df[avail_cols].values
        X_va = val_df[avail_cols].values
        metrics, _, _ = train_eval_xgb(X_tr, y_tr, X_va, y_va)
        results[group_name] = metrics

    # All features combined
    all_cols = [c for c in FEATURE_COLUMNS_V2 if c in train_df.columns]
    metrics_all, _, _ = train_eval_xgb(train_df[all_cols].values, y_tr, val_df[all_cols].values, y_va)
    results["ALL"] = metrics_all
    return results

def run_target_horizon_study(df_raw: pd.DataFrame) -> Dict[str, Any]:
    """Compares 1-day, 5-day, and 10-day prediction targets."""
    horizons = [1, 5, 10]
    results = {}

    for h in horizons:
        df_feat = compute_features_and_target(df_raw, target_horizon=h)
        col_target = f"target_{h}d" if h > 1 else "target"
        cols = [c for c in FEATURE_COLUMNS_V2 if c in df_feat.columns]
        
        df_clean = df_feat.dropna(subset=[col_target] + cols).sort_values("date").reset_index(drop=True)
        train_df, val_df, _ = chronological_split(df_clean, 0.70, 0.15, 0.15)

        X_tr, y_tr = train_df[cols].values, train_df[col_target].values.astype(int)
        X_va, y_va = val_df[cols].values, val_df[col_target].values.astype(int)

        metrics, _, _ = train_eval_xgb(X_tr, y_tr, X_va, y_va)
        metrics["class_balance_up_ratio"] = float(np.mean(y_tr))
        results[f"{h}_day"] = metrics

    return results

def run_walk_forward_study(df_trainable: pd.DataFrame) -> Dict[str, Any]:
    """Executes 5-fold expanding window walk-forward cross-validation."""
    cols = [c for c in FEATURE_COLUMNS_V2 if c in df_trainable.columns]
    splitter = WalkForwardSplitter(min_train_size=250, val_size=60, step_size=60)
    folds = splitter.split(df_trainable)
    
    fold_metrics = []
    for idx, (train_fold, val_fold) in enumerate(folds[:5]):
        X_tr, y_tr = train_fold[cols].values, train_fold["target"].values.astype(int)
        X_va, y_va = val_fold[cols].values, val_fold["target"].values.astype(int)

        metrics, _, _ = train_eval_xgb(X_tr, y_tr, X_va, y_va)
        metrics["fold"] = idx + 1
        metrics["train_dates"] = [str(train_fold["date"].iloc[0]), str(train_fold["date"].iloc[-1])]
        metrics["test_dates"] = [str(val_fold["date"].iloc[0]), str(val_fold["date"].iloc[-1])]
        fold_metrics.append(metrics)

    accuracies = [m["accuracy"] for m in fold_metrics]
    f1_scores = [m["f1_score"] for m in fold_metrics]
    rocs = [m["roc_auc"] for m in fold_metrics]
    briers = [m["brier_score"] for m in fold_metrics]

    return {
        "folds": fold_metrics,
        "summary": {
            "accuracy_mean": float(np.mean(accuracies)),
            "accuracy_median": float(np.median(accuracies)),
            "accuracy_std": float(np.std(accuracies)),
            "f1_mean": float(np.mean(f1_scores)),
            "f1_std": float(np.std(f1_scores)),
            "roc_auc_mean": float(np.mean(rocs)),
            "brier_mean": float(np.mean(briers))
        }
    }

def run_confidence_selective_study(df_trainable: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes hit rates by probability bin and tests selective 'NO CLEAR SIGNAL' thresholding."""
    train_df, val_df, _ = chronological_split(df_trainable, 0.70, 0.15, 0.15)
    cols = [c for c in FEATURE_COLUMNS_V2 if c in train_df.columns]

    X_tr, y_tr = train_df[cols].values, train_df["target"].values.astype(int)
    X_va, y_va = val_df[cols].values, val_df["target"].values.astype(int)

    _, _, probs = train_eval_xgb(X_tr, y_tr, X_va, y_va)
    preds = (probs >= 0.5).astype(int)

    bins = [(0.50, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 1.00)]
    bin_results = {}

    for b_min, b_max in bins:
        mask = ((probs >= b_min) & (probs < b_max)) | ((probs <= 1.0 - b_min) & (probs > 1.0 - b_max))
        if np.sum(mask) > 0:
            bin_acc = float(accuracy_score(y_va[mask], preds[mask]))
            bin_results[f"{b_min:.2f}-{b_max:.2f}"] = {"sample_size": int(np.sum(mask)), "accuracy": bin_acc}
        else:
            bin_results[f"{b_min:.2f}-{b_max:.2f}"] = {"sample_size": 0, "accuracy": 0.0}

    # Selective confidence thresholding evaluation
    # NO CLEAR SIGNAL if probability is inside [0.47, 0.53]
    low_thresh, high_thresh = 0.47, 0.53
    selective_mask = (probs > high_thresh) | (probs < low_thresh)
    
    overall_acc = float(accuracy_score(y_va, preds))
    selective_acc = float(accuracy_score(y_va[selective_mask], preds[selective_mask])) if np.sum(selective_mask) > 0 else overall_acc
    coverage_pct = float(np.mean(selective_mask)) * 100.0

    return {
        "probability_bins": bin_results,
        "all_predictions": {"accuracy": overall_acc, "coverage_pct": 100.0, "total_samples": len(probs)},
        "selective_predictions": {
            "threshold_range": [low_thresh, high_thresh],
            "accuracy": selective_acc,
            "coverage_pct": coverage_pct,
            "no_signal_outcomes": int(len(probs) - np.sum(selective_mask)),
            "active_predictions": int(np.sum(selective_mask))
        }
    }

def run_model_comparison_study(df_trainable: pd.DataFrame) -> Dict[str, Any]:
    """Compares Majority, Previous-Direction, Logistic Regression, Random Forest, XGBoost v1.0, XGBoost v2.0."""
    train_df, val_df, _ = chronological_split(df_trainable, 0.70, 0.15, 0.15)
    y_tr = train_df["target"].values.astype(int)
    y_va = val_df["target"].values.astype(int)

    v1_cols = [c for c in FEATURE_COLUMNS_V1 if c in train_df.columns]
    v2_cols = [c for c in FEATURE_COLUMNS_V2 if c in train_df.columns]

    # 1. Majority Baseline
    maj = MajorityClassBaseline().fit(train_df[v1_cols].values, y_tr)
    maj_preds = maj.predict(val_df[v1_cols].values)
    maj_probs = maj.predict_proba(val_df[v1_cols].values)[:, 1]
    res_maj = evaluate_predictions(y_va, maj_preds, maj_probs)

    # 2. Previous Direction Baseline
    prev_ret = val_df["daily_return"].values
    prev_preds = (prev_ret > 0).astype(int)
    prev_probs = np.where(prev_ret > 0, 0.7, 0.3)
    res_prev = evaluate_predictions(y_va, prev_preds, prev_probs)

    # 3. Logistic Regression
    scaler = StandardScaler().fit(train_df[v2_cols].fillna(0.0).values)
    X_tr_s = scaler.transform(train_df[v2_cols].fillna(0.0).values)
    X_va_s = scaler.transform(val_df[v2_cols].fillna(0.0).values)
    lr = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr_s, y_tr)
    lr_probs = lr.predict_proba(X_va_s)[:, 1]
    lr_preds = (lr_probs >= 0.5).astype(int)
    res_lr = evaluate_predictions(y_va, lr_preds, lr_probs)

    # 4. Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42).fit(train_df[v2_cols].fillna(0.0).values, y_tr)
    rf_probs = rf.predict_proba(val_df[v2_cols].fillna(0.0).values)[:, 1]
    rf_preds = (rf_probs >= 0.5).astype(int)
    res_rf = evaluate_predictions(y_va, rf_preds, rf_probs)

    # 5. XGBoost v1.0 (Baseline features)
    res_xgb1, _, _ = train_eval_xgb(train_df[v1_cols].values, y_tr, val_df[v1_cols].values, y_va)

    # 6. XGBoost v2.0 (Expanded features & tuned params)
    res_xgb2, _, _ = train_eval_xgb(train_df[v2_cols].values, y_tr, val_df[v2_cols].values, y_va, params={"n_estimators": 120, "max_depth": 3, "learning_rate": 0.02, "subsample": 0.8, "colsample_bytree": 0.8, "reg_alpha": 0.1, "reg_lambda": 1.0})

    return {
        "MajorityBaseline": res_maj,
        "PreviousDirection": res_prev,
        "LogisticRegression": res_lr,
        "RandomForest": res_rf,
        "XGBoost_v1.0": res_xgb1,
        "XGBoost_v2.0": res_xgb2
    }

def run_phase12_master_study():
    print("==================================================")
    print("STOCKSENSE AI — PHASE 12 ADVANCED ML STUDY")
    print("==================================================")

    db = SessionLocal()
    master_results = {}
    final_out_of_sample_summary = {}

    try:
        # Save baseline verification file
        with open(os.path.join(RESEARCH_DIR, "baseline_results.json"), "w", encoding="utf-8") as f:
            json.dump(PHASE11_BASELINE, f, indent=2)

        ablation_summary = {}
        target_horizon_summary = {}
        walk_forward_summary = {}
        confidence_summary = {}
        model_comp_summary = {}

        for sym in TARGET_ASSETS:
            print(f"Processing ML Study for Asset: {sym:10s}...")
            df_raw = ensure_historical_data_in_db(sym, db=db)
            if df_raw.empty or len(df_raw) < 100:
                continue

            df_feat = compute_features_and_target(df_raw)
            cols_v2 = [c for c in FEATURE_COLUMNS_V2 if c in df_feat.columns]
            df_trainable = df_feat.dropna(subset=["target"] + cols_v2).sort_values("date").reset_index(drop=True)

            # 1. Feature Ablation
            ablation_summary[sym] = run_feature_ablation_study(df_trainable)

            # 2. Target / Horizon Comparison
            target_horizon_summary[sym] = run_target_horizon_study(df_raw)

            # 3. Walk-Forward Cross-Validation
            walk_forward_summary[sym] = run_walk_forward_study(df_trainable)

            # 4. Confidence & Selective Coverage Analysis
            confidence_summary[sym] = run_confidence_selective_study(df_trainable)

            # 5. Model Comparison
            model_comp_summary[sym] = run_model_comparison_study(df_trainable)

            # 6. Final Unseen Out-of-Sample Holdout Evaluation
            train_df, val_df, test_df = chronological_split(df_trainable, 0.70, 0.15, 0.15)
            y_tr = train_df["target"].values.astype(int)
            y_va = val_df["target"].values.astype(int)
            y_te = test_df["target"].values.astype(int)

            # Train XGBoost v2.0 pipeline on Train + Val, evaluate ONCE on unseen Test set
            X_tr_val = pd.concat([train_df[cols_v2], val_df[cols_v2]]).values
            y_tr_val = np.concatenate([y_tr, y_va])
            X_test = test_df[cols_v2].values

            pipe_v2 = ModelPipeline("XGBoost", sym)
            # Train pipeline on train_df, validate on val_df to compute internal metrics
            pipe_v2.train(train_df, val_df)
            
            # Predict on final unseen holdout test set
            test_preds_v2, test_probs_v2 = pipe_v2.predict(test_df)
            test_metrics_v2 = evaluate_predictions(y_te, test_preds_v2, test_probs_v2)

            # Apply selective thresholding to unseen holdout test set
            low_t, high_t = 0.47, 0.53
            sel_mask = (test_probs_v2 > high_t) | (test_probs_v2 < low_t)
            sel_acc = float(accuracy_score(y_te[sel_mask], test_preds_v2[sel_mask])) if np.sum(sel_mask) > 0 else test_metrics_v2["accuracy"]
            coverage_pct = float(np.mean(sel_mask)) * 100.0

            # Save XGBoost v2.0 model artifact & metadata
            extra_meta_v2 = {
                "model_version": "XGBoost v2.0.0",
                "features_used": cols_v2,
                "walk_forward_metrics": walk_forward_summary[sym]["summary"],
                "test_out_of_sample_metrics": test_metrics_v2,
                "selective_confidence": {
                    "threshold_bounds": [low_t, high_t],
                    "selective_accuracy": sel_acc,
                    "coverage_pct": coverage_pct
                }
            }
            pipe_v2.save_model(extra_meta=extra_meta_v2)

            v1_acc = PHASE11_BASELINE.get(sym, {}).get("accuracy", 0.50)
            v2_acc = test_metrics_v2["accuracy"]
            chg = round((v2_acc - v1_acc) * 100.0, 2)

            final_out_of_sample_summary[sym] = {
                "phase11_baseline_accuracy": v1_acc,
                "phase12_xgb_v2_accuracy": v2_acc,
                "accuracy_change_percentage_points": chg,
                "phase12_selective_accuracy": sel_acc,
                "phase12_coverage_pct": coverage_pct,
                "metrics_full": test_metrics_v2
            }
            print(f"  -> {sym:10s}: Phase11={v1_acc*100:.2f}% | Phase12 v2.0={v2_acc*100:.2f}% (Change: {chg:+.2f}%) | Selective={sel_acc*100:.2f}% (Coverage: {coverage_pct:.1f}%)")

        # Save all structured JSON research files
        with open(os.path.join(RESEARCH_DIR, "feature_ablation.json"), "w", encoding="utf-8") as f:
            json.dump(ablation_summary, f, indent=2)

        with open(os.path.join(RESEARCH_DIR, "target_horizon.json"), "w", encoding="utf-8") as f:
            json.dump(target_horizon_summary, f, indent=2)

        with open(os.path.join(RESEARCH_DIR, "walk_forward.json"), "w", encoding="utf-8") as f:
            json.dump(walk_forward_summary, f, indent=2)

        with open(os.path.join(RESEARCH_DIR, "confidence_analysis.json"), "w", encoding="utf-8") as f:
            json.dump(confidence_summary, f, indent=2)

        with open(os.path.join(RESEARCH_DIR, "model_comparison.json"), "w", encoding="utf-8") as f:
            json.dump(model_comp_summary, f, indent=2)

        with open(os.path.join(RESEARCH_DIR, "final_results.json"), "w", encoding="utf-8") as f:
            json.dump(final_out_of_sample_summary, f, indent=2)

        print("\nPhase 12 ML Scientific Study Complete! Research artifacts written to backend/research/phase12/")
        return final_out_of_sample_summary

    finally:
        db.close()

if __name__ == "__main__":
    run_phase12_master_study()
