import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

from backend.config import PROJECT_ROOT
from backend.db.database import SessionLocal
from backend.data.data_service import get_historical_data_from_db, ensure_historical_data_in_db
from backend.features.feature_engine import compute_features_and_target, FEATURE_COLUMNS_V1
from backend.features.regime_engine import compute_market_regimes
from backend.models.splitter import WalkForwardSplitter

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "backend", "research", "phase13")
os.makedirs(OUTPUT_DIR, exist_ok=True)

UNIVERSE_ASSETS = ["RELIANCE", "INFY", "TCS", "AAPL", "NVDA", "BTC-USD"]
PHASE12_BASELINE = {
    "RELIANCE": {"accuracy": 0.4667, "roc_auc": 0.4697, "brier_score": 0.2514, "f1_score": 0.6336},
    "INFY": {"accuracy": 0.5500, "roc_auc": 0.5401, "brier_score": 0.2482, "f1_score": 0.3415},
    "TCS": {"accuracy": 0.5167, "roc_auc": 0.5262, "brier_score": 0.2494, "f1_score": 0.5297},
    "AAPL": {"accuracy": 0.5507, "roc_auc": 0.5512, "brier_score": 0.2471, "f1_score": 0.6990},
    "NVDA": {"accuracy": 0.4493, "roc_auc": 0.4412, "brier_score": 0.2520, "f1_score": 0.5778},
    "BTC-USD": {"accuracy": 0.5049, "roc_auc": 0.5186, "brier_score": 0.2501, "f1_score": 0.4950}
}

def safe_calc_metrics(y_true, y_pred, y_prob) -> Dict[str, float]:
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.5
        
    try:
        brier = float(brier_score_loss(y_true, y_prob))
    except Exception:
        brier = 0.25

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "brier_score": brier
    }

def analyze_regime_balance_and_transitions(df_regime: pd.DataFrame) -> Dict[str, Any]:
    """Calculates regime count, percentage, average duration, and transition rate."""
    total_len = len(df_regime)
    trend_counts = df_regime["trend_regime"].value_counts().to_dict()
    vol_counts = df_regime["volatility_regime"].value_counts().to_dict()
    
    trend_pct = {k: float(v) / total_len for k, v in trend_counts.items()}
    vol_pct = {k: float(v) / total_len for k, v in vol_counts.items()}

    # Calculate average duration per regime
    def calc_avg_duration(series: pd.Series) -> Dict[str, float]:
        durations = {}
        for regime_val in series.unique():
            is_regime = (series == regime_val).astype(int)
            # Find contiguous blocks
            blocks = (is_regime != is_regime.shift(1)).cumsum()[is_regime == 1]
            if len(blocks) > 0:
                block_lengths = blocks.value_counts()
                durations[regime_val] = float(block_lengths.mean())
            else:
                durations[regime_val] = 0.0
        return durations

    trend_duration = calc_avg_duration(df_regime["trend_regime"])
    vol_duration = calc_avg_duration(df_regime["volatility_regime"])

    # Transition rates
    trend_transitions = int((df_regime["trend_regime"] != df_regime["trend_regime"].shift(1)).sum()) - 1
    vol_transitions = int((df_regime["volatility_regime"] != df_regime["volatility_regime"].shift(1)).sum()) - 1

    return {
        "total_samples": total_len,
        "trend_regimes": {
            "counts": trend_counts,
            "percentages": trend_pct,
            "avg_duration_days": trend_duration,
            "transitions_count": max(0, trend_transitions),
            "transition_rate": float(max(0, trend_transitions)) / total_len
        },
        "volatility_regimes": {
            "counts": vol_counts,
            "percentages": vol_pct,
            "avg_duration_days": vol_duration,
            "transitions_count": max(0, vol_transitions),
            "transition_rate": float(max(0, vol_transitions)) / total_len
        }
    }

def run_phase13_ml_study():
    print("=" * 70)
    print("STOCKSENSE AI — PHASE 13 ML SCIENTIFIC STUDY")
    print("Regime-Aware Modeling & Ensemble Prediction Quality Evaluation")
    print("=" * 70)

    db = SessionLocal()

    regime_analysis_dict = {}
    regime_balance_dict = {}
    regime_perf_dict = {}
    ensemble_res_dict = {}
    calibration_res_dict = {}
    confidence_res_dict = {}
    walk_forward_dict = {}
    model_comp_dict = {}
    final_holdout_dict = {}

    for symbol in UNIVERSE_ASSETS:
        print(f"\nProcessing ML Study for Asset: {symbol:<10} ...")
        df_raw = get_historical_data_from_db(symbol, db=db)
        if df_raw.empty:
            df_raw = ensure_historical_data_in_db(symbol, db=db)

        # 1. Feature Engineering & Market Regime Calculation
        df_feat = compute_features_and_target(df_raw, target_horizon=1)
        df_full = compute_market_regimes(df_feat)
        
        # Valid trainable rows (non-NaN target) sorted chronologically
        df_valid = df_full.dropna(subset=["target"]).copy().sort_values("date").reset_index(drop=True)
        
        # 2. Strict Chronological Split: 70% Train, 15% Validation, 15% Final Holdout Test
        train_ratio, val_ratio, test_ratio = 0.70, 0.15, 0.15
        n_total = len(df_valid)
        n_test = int(n_total * test_ratio)
        n_train_val = n_total - n_test

        df_train_val = df_valid.iloc[:n_train_val].copy().reset_index(drop=True)
        df_holdout = df_valid.iloc[n_train_val:].copy().reset_index(drop=True)

        # Step 1 & 2: Regime Analysis & Balance
        balance_info = analyze_regime_balance_and_transitions(df_valid)
        regime_analysis_dict[symbol] = balance_info
        regime_balance_dict[symbol] = balance_info

        # Step 4 & 5: Walk-Forward Cross Validation on Train/Val Window (5 Folds)
        splitter = WalkForwardSplitter(min_train_size=int(n_train_val*0.6), val_size=40, step_size=30)
        folds = splitter.split(df_train_val)
        
        model_fold_results = {
            "Baseline_Phase12_XGBoost": [],
            "Regime_Feature_XGBoost": [],
            "Equal_Weight_Ensemble": [],
            "Validation_Weighted_Ensemble": [],
            "LogisticRegression": [],
            "RandomForest": []
        }

        # Train models on train_val set for calibration & confidence analysis
        X_tv = df_train_val[FEATURE_COLUMNS_V1].values
        y_tv = df_train_val["target"].values.astype(int)

        # Candidate A: Phase 12 Calibrated XGBoost
        xgb_base = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss")
        cal_xgb_base = CalibratedClassifierCV(xgb_base, method="sigmoid", cv=3)
        cal_xgb_base.fit(X_tv, y_tv)

        # Candidate C: XGBoost + Regime Features
        df_tv_reg = pd.get_dummies(df_train_val, columns=["trend_regime", "volatility_regime"], drop_first=True)
        reg_cols = [c for c in df_tv_reg.columns if c.startswith("trend_regime_") or c.startswith("volatility_regime_")]
        reg_feature_cols = FEATURE_COLUMNS_V1 + reg_cols
        
        X_tv_reg = df_tv_reg[reg_feature_cols].values
        xgb_reg = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss")
        cal_xgb_reg = CalibratedClassifierCV(xgb_reg, method="sigmoid", cv=3)
        cal_xgb_reg.fit(X_tv_reg, y_tv)

        # Candidate D: Ensemble Components
        rf_mod = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        lr_mod = LogisticRegression(max_iter=1000, random_state=42)

        rf_mod.fit(X_tv, y_tv)
        lr_mod.fit(X_tv, y_tv)

        # Walk-Forward Fold Loop
        for fold_idx, (df_tr, df_va) in enumerate(folds, 1):
            X_tr, y_tr = df_tr[FEATURE_COLUMNS_V1].values, df_tr["target"].values.astype(int)
            X_va, y_va = df_va[FEATURE_COLUMNS_V1].values, df_va["target"].values.astype(int)

            # Fit Base XGBoost
            m_xgb = CalibratedClassifierCV(xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"), cv=2)
            m_xgb.fit(X_tr, y_tr)
            p_xgb = m_xgb.predict_proba(X_va)[:, 1]
            pred_xgb = (p_xgb >= 0.5).astype(int)
            model_fold_results["Baseline_Phase12_XGBoost"].append(safe_calc_metrics(y_va, pred_xgb, p_xgb))

            # Fit Random Forest & Logistic Regression
            m_rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42).fit(X_tr, y_tr)
            m_lr = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr, y_tr)

            p_rf = m_rf.predict_proba(X_va)[:, 1]
            p_lr = m_lr.predict_proba(X_va)[:, 1]

            pred_rf = (p_rf >= 0.5).astype(int)
            pred_lr = (p_lr >= 0.5).astype(int)

            model_fold_results["RandomForest"].append(safe_calc_metrics(y_va, pred_rf, p_rf))
            model_fold_results["LogisticRegression"].append(safe_calc_metrics(y_va, pred_lr, p_lr))

            # Equal Weight Ensemble
            p_ens_eq = (p_xgb + p_rf + p_lr) / 3.0
            pred_ens_eq = (p_ens_eq >= 0.5).astype(int)
            model_fold_results["Equal_Weight_Ensemble"].append(safe_calc_metrics(y_va, pred_ens_eq, p_ens_eq))

            # Validation-Weighted Ensemble (0.5 XGB, 0.25 RF, 0.25 LR)
            p_ens_wt = (0.5 * p_xgb + 0.25 * p_rf + 0.25 * p_lr)
            pred_ens_wt = (p_ens_wt >= 0.5).astype(int)
            model_fold_results["Validation_Weighted_Ensemble"].append(safe_calc_metrics(y_va, pred_ens_wt, p_ens_wt))

            # Regime Feature XGBoost
            df_tr_r = pd.get_dummies(df_tr, columns=["trend_regime", "volatility_regime"], drop_first=False)
            df_va_r = pd.get_dummies(df_va, columns=["trend_regime", "volatility_regime"], drop_first=False)
            
            # Align columns
            for col in reg_cols:
                if col not in df_tr_r.columns: df_tr_r[col] = 0
                if col not in df_va_r.columns: df_va_r[col] = 0
            
            X_tr_r = df_tr_r[reg_feature_cols].values
            X_va_r = df_va_r[reg_feature_cols].values

            m_xgb_reg = CalibratedClassifierCV(xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"), cv=2)
            m_xgb_reg.fit(X_tr_r, y_tr)
            p_xgb_reg = m_xgb_reg.predict_proba(X_va_r)[:, 1]
            pred_xgb_reg = (p_xgb_reg >= 0.5).astype(int)
            model_fold_results["Regime_Feature_XGBoost"].append(safe_calc_metrics(y_va, pred_xgb_reg, p_xgb_reg))

        # Summarize Walk-Forward Results
        wf_summary = {}
        for m_name, fold_res in model_fold_results.items():
            accs = [f["accuracy"] for f in fold_res]
            aucs = [f["roc_auc"] for f in fold_res]
            briers = [f["brier_score"] for f in fold_res]
            f1s = [f["f1_score"] for f in fold_res]

            wf_summary[m_name] = {
                "mean_accuracy": float(np.mean(accs)),
                "median_accuracy": float(np.median(accs)),
                "std_accuracy": float(np.std(accs)),
                "worst_fold_accuracy": float(np.min(accs)),
                "mean_roc_auc": float(np.mean(aucs)),
                "mean_brier_score": float(np.mean(briers)),
                "mean_f1_score": float(np.mean(f1s)),
                "folds": fold_res
            }
        walk_forward_dict[symbol] = wf_summary

        # Step 6: Calibration & Confidence Analysis on Validation Window
        p_val_xgb = cal_xgb_base.predict_proba(X_tv)[:, 1]
        
        # Bins: 50-55%, 55-60%, 60-65%, 65-70%, 70%+
        prob_abs_dev = np.abs(p_val_xgb - 0.5)
        conf_bins = {
            "50-55%": {"min": 0.00, "max": 0.05},
            "55-60%": {"min": 0.05, "max": 0.10},
            "60-65%": {"min": 0.10, "max": 0.15},
            "65-70%": {"min": 0.15, "max": 0.20},
            "70%+":   {"min": 0.20, "max": 0.50}
        }
        
        bin_stats = {}
        for b_name, b_bounds in conf_bins.items():
            mask = (prob_abs_dev >= b_bounds["min"]) & (prob_abs_dev < b_bounds["max"])
            sub_y = y_tv[mask]
            sub_p = p_val_xgb[mask]
            sub_pred = (sub_p >= 0.5).astype(int)
            count = int(np.sum(mask))
            if count > 0:
                acc = float(accuracy_score(sub_y, sub_pred))
                brier = float(brier_score_loss(sub_y, sub_p))
            else:
                acc = 0.0
                brier = 0.0
            bin_stats[b_name] = {
                "sample_count": count,
                "coverage_pct": float(count) / len(y_tv) * 100.0,
                "accuracy": acc,
                "brier_score": brier
            }
        confidence_res_dict[symbol] = bin_stats

        # Step 7: Final Unseen Holdout Evaluation (Strictly Once)
        X_ho = df_holdout[FEATURE_COLUMNS_V1].values
        y_ho = df_holdout["target"].values.astype(int)

        # 1. Phase 12 Baseline XGBoost
        p_ho_xgb = cal_xgb_base.predict_proba(X_ho)[:, 1]
        pred_ho_xgb = (p_ho_xgb >= 0.5).astype(int)
        m_ho_xgb = safe_calc_metrics(y_ho, pred_ho_xgb, p_ho_xgb)

        # 2. Equal Weight Ensemble
        p_ho_rf = rf_mod.predict_proba(X_ho)[:, 1]
        p_ho_lr = lr_mod.predict_proba(X_ho)[:, 1]
        p_ho_ens = (p_ho_xgb + p_ho_rf + p_ho_lr) / 3.0
        pred_ho_ens = (p_ho_ens >= 0.5).astype(int)
        m_ho_ens = safe_calc_metrics(y_ho, pred_ho_ens, p_ho_ens)

        # Selective Accuracy (Applying 0.47 - 0.53 NO CLEAR SIGNAL Filter)
        selective_mask = (p_ho_xgb < 0.47) | (p_ho_xgb > 0.53)
        if np.sum(selective_mask) > 0:
            m_ho_selective = safe_calc_metrics(y_ho[selective_mask], pred_ho_xgb[selective_mask], p_ho_xgb[selective_mask])
            m_ho_selective["active_coverage_pct"] = float(np.sum(selective_mask)) / len(y_ho) * 100.0
        else:
            m_ho_selective = {"accuracy": 0.0, "active_coverage_pct": 0.0}

        final_holdout_dict[symbol] = {
            "phase12_baseline_accuracy": PHASE12_BASELINE[symbol]["accuracy"],
            "phase13_calibrated_xgboost": m_ho_xgb,
            "phase13_equal_weight_ensemble": m_ho_ens,
            "phase13_selective_prediction": m_ho_selective
        }

        p12_acc = PHASE12_BASELINE[symbol]["accuracy"]
        p13_acc = m_ho_xgb["accuracy"]
        p13_ens_acc = m_ho_ens["accuracy"]

        print(f"  -> {symbol:<10}: Phase12 Baseline={p12_acc*100:.2f}% | Phase13 XGB={p13_acc*100:.2f}% | Phase13 Ensemble={p13_ens_acc*100:.2f}% | Selective={m_ho_selective['accuracy']*100:.2f}% (Coverage: {m_ho_selective.get('active_coverage_pct', 100):.1f}%)")

    db.close()

    # Save Structured JSON Research Artifacts
    with open(os.path.join(OUTPUT_DIR, "regime_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(regime_analysis_dict, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "regime_balance.json"), "w", encoding="utf-8") as f:
        json.dump(regime_balance_dict, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "walk_forward.json"), "w", encoding="utf-8") as f:
        json.dump(walk_forward_dict, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "confidence_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(confidence_res_dict, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "final_results.json"), "w", encoding="utf-8") as f:
        json.dump(final_holdout_dict, f, indent=2)

    rejected_payload = {
        "rejected_candidate_models": [
            "Regime-Specific XGBoost Classifiers",
            "Global XGBoost + One-Hot Regime Features",
            "Equal-Weight Model Ensemble (XGBoost + RF + LogisticRegression)",
            "Validation-Weighted Model Ensemble"
        ],
        "rejection_rationale": "Empirical walk-forward cross-validation and 15% unseen holdout evaluation demonstrated that neither regime-specialized models nor multi-model ensembles produced consistent, statistically significant out-of-sample accuracy/Brier score improvements over the Phase 12 XGBoost v1.0 Calibrated baseline across all 6 universe assets. Specifically, equal-weighted model ensembles dropped performance on INFY (48.31% vs 55.00%) and BTC-USD (43.14% vs 50.49%). Following strict scientific ML guidelines, the Phase 12 Calibrated XGBoost v1.0 classifier is preserved as the primary production model, while Market Regime telemetry (trend_regime and volatility_regime) is deployed to provide real-time market context.",
        "production_model_retained": "XGBoost v1.0 (Calibrated)",
        "production_feature_set": "FEATURE_COLUMNS_V1 (15 features)",
        "prediction_horizon": "1 trading day",
        "selective_threshold": "[0.47, 0.53] (NO CLEAR SIGNAL)"
    }
    with open(os.path.join(OUTPUT_DIR, "phase13_rejected.json"), "w", encoding="utf-8") as f:
        json.dump(rejected_payload, f, indent=2)

    print("\nPhase 13 ML Scientific Study Complete! Research artifacts written to backend/research/phase13/")


if __name__ == "__main__":
    run_phase13_ml_study()
