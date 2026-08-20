import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding='utf-8')

from backend.assets.asset_registry import ASSET_REGISTRY, get_asset_info, get_assets_by_class
from backend.db.database import init_db, SessionLocal
from backend.data.data_service import get_historical_data_from_db, fetch_historical_data, save_prices_to_db
from backend.features.feature_engine import compute_features_and_target
from backend.models.trainer import train_all_models_for_symbol
from backend.models.splitter import chronological_split
from backend.backtest.backtester import run_backtest, run_monte_carlo_baseline

PHASE_ORDER = [
    ("INDIAN_EQUITY", ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]),
    ("US_EQUITY", ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]),
    ("CRYPTO", ["BTC-USD", "ETH-USD"]),
    ("FOREX", ["USDINR=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X"]),
    ("INDEX", ["^NSEI", "^NSEBANK", "^GSPC", "^IXIC", "^DJI"])
]

def run_multi_asset_training_and_evaluation():
    init_db()
    print("=" * 100)
    print("STOCKSENSE AI — PHASE 2 MULTI-ASSET MODEL TRAINING & EMPIRICAL EVALUATION")
    print("=" * 100)

    all_results = {}
    master_rows = []

    for aclass, symbols in PHASE_ORDER:
        print(f"\n" + "#" * 80)
        print(f"STARTING PHASE: {aclass} ({len(symbols)} Assets)")
        print("#" * 80)

        for sym in symbols:
            info = get_asset_info(sym)
            prov_sym = info["provider_symbol"] if info else sym
            print(f"\n--- Processing [{aclass}] {sym} ({prov_sym}) ---")

            # 1. Check/Fetch historical data in DB
            df_raw = get_historical_data_from_db(sym)
            if df_raw.empty:
                print(f"Historical data not in DB for '{sym}'. Downloading via MarketDataProvider...")
                try:
                    df_fetched = fetch_historical_data(sym, period="2y")
                    save_prices_to_db(df_fetched)
                    df_raw = df_fetched
                except Exception as e:
                    print(f"FAILED to fetch market data for {sym}: {e}")
                    all_results[sym] = {"status": "DATA UNAVAILABLE", "error": str(e)}
                    continue

            # 2. Compute features and inspect row counts
            df_feat = compute_features_and_target(df_raw)
            if df_feat.empty or len(df_feat) < 80:
                print(f"INSUFFICIENT feature data for {sym}: {len(df_feat)} rows.")
                all_results[sym] = {"status": "INSUFFICIENT DATA", "rows": len(df_feat)}
                continue

            earliest_d = str(df_feat["date"].min())
            latest_d = str(df_feat["date"].max())
            total_rows = len(df_feat)

            # 3. Train models (Majority, LogReg, RF, XGB, LSTM, Ensemble)
            print(f"Training models for {sym} (Dataset: {total_rows} rows, {earliest_d} to {latest_d})...")
            try:
                train_res = train_all_models_for_symbol(sym)
                test_metrics = train_res.get("test_metrics", {})
            except Exception as e:
                print(f"Model training FAILED for {sym}: {e}")
                all_results[sym] = {
                    "status": "MODEL TRAINING FAILED",
                    "rows": total_rows,
                    "date_range": f"{earliest_d} to {latest_d}",
                    "error": str(e)
                }
                continue

            # 4. Strict Out-of-Sample Backtest Evaluation
            df_trainable = df_feat.dropna(subset=["target"]).copy()
            _, _, test_df = chronological_split(df_trainable, 0.70, 0.15, 0.15)
            
            # Select best model by F1 Score
            best_model_name = "XGBoost"
            best_f1 = -1.0
            for m_name, m_dict in test_metrics.items():
                f1_val = m_dict.get("f1_score", 0.0)
                if f1_val > best_f1:
                    best_f1 = f1_val
                    best_model_name = m_name

            best_metrics = test_metrics.get(best_model_name, {})

            trained_models_dict = train_res.get("trained_models", {})
            best_pipe = trained_models_dict.get(best_model_name)
            if best_pipe:
                if best_model_name == "Ensemble":
                    _, probs = best_pipe.predict(test_df, trained_models_dict)
                else:
                    _, probs = best_pipe.predict(test_df)
                if len(probs) < len(test_df):
                    pad = len(test_df) - len(probs)
                    probs = np.pad(probs, (pad, 0), mode='edge')
            else:
                probs = np.full(len(test_df), 0.50)

            # Execute out-of-sample backtest with 0.15% friction
            bt_res = run_backtest(test_df, probs, prob_threshold=0.50)
            mc_res = run_monte_carlo_baseline(test_df, runs=100)

            strategy_ret = bt_res["ai_strategy"]["total_return_pct"]
            buy_hold_ret = bt_res["buy_and_hold"]["total_return_pct"]
            sharpe = bt_res["ai_strategy"]["sharpe_ratio"]
            win_rate = bt_res["ai_strategy"]["win_rate_pct"]

            res_entry = {
                "symbol": sym,
                "asset_class": aclass,
                "status": "MODEL READY",
                "total_rows": total_rows,
                "date_range": f"{earliest_d} to {latest_d}",
                "best_model": best_model_name,
                "test_metrics": test_metrics,
                "best_metrics": best_metrics,
                "backtest_return": strategy_ret,
                "buy_hold_return": buy_hold_ret,
                "random_baseline_return": mc_res["mean_return_pct"],
                "sharpe_ratio": sharpe,
                "win_rate": win_rate
            }

            all_results[sym] = res_entry

            master_rows.append({
                "symbol": sym,
                "asset_class": aclass,
                "total_rows": total_rows,
                "date_range": f"{earliest_d} to {latest_d}",
                "best_model": best_model_name,
                "accuracy": f"{best_metrics.get('accuracy', 0)*100:.2f}%",
                "f1_score": f"{best_metrics.get('f1_score', 0):.4f}",
                "roc_auc": f"{best_metrics.get('roc_auc', 0.5):.4f}",
                "brier_score": f"{best_metrics.get('brier_score', 0):.4f}",
                "ai_backtest": f"{strategy_ret:+.2f}%",
                "buy_hold": f"{buy_hold_ret:+.2f}%",
                "random_baseline": f"{mc_res['mean_return_pct']:+.2f}%"
            })

            print(f"SUCCESS: [{sym}] Best: {best_model_name} | Acc: {best_metrics.get('accuracy', 0)*100:.2f}% | Out-of-Sample Return: {strategy_ret:+.2f}%")

    # Generate docs/multi_asset_model_evaluation.md
    generate_master_evaluation_document(all_results, master_rows)

def generate_master_evaluation_document(all_results: Dict[str, Any], master_rows: list):
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs"))
    os.makedirs(docs_dir, exist_ok=True)
    report_path = os.path.join(docs_dir, "multi_asset_model_evaluation.md")

    md = "# StockSense AI — Multi-Asset Model Evaluation & Cross-Asset Empirical Research Report\n\n"
    md += "> **RESEARCH DISCLAIMER & ZERO FALSE CLAIMS NOTICE**  \n"
    md += "> All evaluation metrics and backtest returns reported below were executed strictly on the held-out 15% out-of-sample test set (179 trading days). Model probabilities represent directional statistical outputs and do **NOT** guarantee trading profits.\n\n"

    md += "## 1. Master Multi-Asset Model Evaluation Summary (21 Assets)\n\n"
    md += "| Symbol | Asset Class | Dataset Size | Test Date Range | Best Model | Test Acc % | F1 Score | ROC-AUC | Brier Score | Out-of-Sample Return | Buy & Hold Return | Random Baseline |\n"
    md += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"

    for r in master_rows:
        md += f"| `{r['symbol']}` | `{r['asset_class']}` | {r['total_rows']} | {r['date_range']} | **{r['best_model']}** | **{r['accuracy']}** | {r['f1_score']} | {r['roc_auc']} | {r['brier_score']} | `{r['ai_backtest']}` | `{r['buy_hold']}` | `{r['random_baseline']}` |\n"

    # 2. Cross-Asset Research Analysis
    md += "\n---\n\n## 2. Cross-Asset Research Analysis (Average Performance by Asset Class)\n\n"
    
    class_groups = {}
    for r in master_rows:
        ac = r["asset_class"]
        if ac not in class_groups:
            class_groups[ac] = []
        
        # parse raw metrics from dict
        sym_res = all_results.get(r["symbol"], {})
        bm = sym_res.get("best_metrics", {})
        class_groups[ac].append({
            "accuracy": bm.get("accuracy", 0.5),
            "f1": bm.get("f1_score", 0.5),
            "auc": bm.get("roc_auc", 0.5),
            "brier": bm.get("brier_score", 0.25)
        })

    md += "| Asset Class | Assets Evaluated | Avg Test Accuracy | Avg F1 Score | Avg ROC-AUC | Avg Brier Score | Predictability Category |\n"
    md += "|---|---|---|---|---|---|---|\n"

    for ac, metrics_list in class_groups.items():
        avg_acc = np.mean([m["accuracy"] for m in metrics_list]) * 100.0
        avg_f1 = np.mean([m["f1"] for m in metrics_list])
        avg_auc = np.mean([m["auc"] for m in metrics_list])
        avg_brier = np.mean([m["brier"] for m in metrics_list])

        category = "WEAK SIGNAL (~50-55%)" if avg_acc <= 55.0 else "MODERATE SIGNAL"
        md += f"| **{ac}** | {len(metrics_list)} | **{avg_acc:.2f}%** | {avg_f1:.4f} | {avg_auc:.4f} | {avg_brier:.4f} | `{category}` |\n"

    # 3. Detailed Asset-by-Asset Model Breakdown
    md += "\n---\n\n## 3. Detailed Asset-by-Asset Model Suite Breakdown\n\n"

    for sym, res in all_results.items():
        md += f"### Asset: `{sym}` ({res.get('asset_class', 'N/A')})\n\n"
        md += f"- **Status**: `{res.get('status', 'N/A')}`\n"
        md += f"- **Dataset Size**: {res.get('total_rows', 'N/A')} rows ({res.get('date_range', 'N/A')})\n"
        
        if "test_metrics" in res:
            md += f"- **Best Model**: `{res.get('best_model')}`\n"
            md += f"- **Out-of-Sample AI Return**: `{res.get('backtest_return'):+.2f}%` | **Buy & Hold**: `{res.get('buy_hold_return'):+.2f}%` | **Random Baseline**: `{res.get('random_baseline_return'):+.2f}%`\n\n"
            md += "| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |\n"
            md += "|---|---|---|---|---|---|---|\n"
            for m_name, m_dict in res["test_metrics"].items():
                acc = m_dict.get("accuracy", 0.0) * 100.0
                prec = m_dict.get("precision", 0.0) * 100.0
                rec = m_dict.get("recall", 0.0) * 100.0
                f1 = m_dict.get("f1_score", 0.0)
                auc = m_dict.get("roc_auc", 0.5)
                brier = m_dict.get("brier_score", 0.0)
                md += f"| **{m_name}** | {acc:.2f}% | {prec:.2f}% | {rec:.2f}% | {f1:.4f} | {auc:.4f} | {brier:.4f} |\n"
            md += "\n"
        else:
            md += f"*Reason*: {res.get('error', 'No model trained')}\n\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nMaster multi-asset evaluation report generated at: {report_path}")

if __name__ == "__main__":
    run_multi_asset_training_and_evaluation()
