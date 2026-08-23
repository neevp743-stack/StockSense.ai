"""
StockSense AI — Phase 19 Regime & Asset Analysis Engine
Evaluates Champion vs Challenger model performance broken down by:
1. Individual symbols (all 109+ supported assets in ALL_SYMBOLS)
2. Asset groups (INDIA, USA, CRYPTO, ALL-ASSETS)
3. Phase 13 Market Regimes (BULL, BEAR, SIDEWAYS, HIGH_VOLATILITY, LOW_VOLATILITY)
"""

from typing import Dict, Any, List, Optional
from backend.research.phase19.services.rolling_metrics import calculate_metrics_for_records
from backend.data.universe import ALL_SYMBOLS


def get_symbol_region(symbol: str) -> str:
    """Helper classifying asset region based on symbol suffix/format."""
    sym = symbol.upper().strip()
    if sym.endswith(".NS") or sym.endswith(".BO") or sym in ["RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LTIM"]:
        return "INDIA"
    elif "-USD" in sym or "USD" in sym or sym in ["BTC-USD", "ETH-USD", "SOL-USD"]:
        return "CRYPTO"
    else:
        return "USA"


class RegimeAndAssetAnalysisEngine:
    """Performs per-symbol, asset group, and market regime performance breakdowns."""

    def compute_per_symbol_results(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates Champion vs Challenger performance for every symbol in ALL_SYMBOLS."""
        # Index records by symbol
        symbol_map: Dict[str, List[Dict[str, Any]]] = {}
        for r in paired_records:
            sym = r["symbol"].upper()
            symbol_map.setdefault(sym, []).append(r)

        per_symbol_results = {}
        total_eval_symbols = 0

        for sym in sorted(ALL_SYMBOLS):
            sym_clean = sym.upper()
            recs = symbol_map.get(sym_clean, [])
            n = len(recs)

            champ_m = calculate_metrics_for_records(recs, "champion")
            chall_m = calculate_metrics_for_records(recs, "challenger")

            acc_diff = (chall_m["accuracy"] - champ_m["accuracy"]) if (chall_m["accuracy"] is not None and champ_m["accuracy"] is not None) else None
            brier_diff = (chall_m["brier_score"] - champ_m["brier_score"]) if (chall_m["brier_score"] is not None and champ_m["brier_score"] is not None) else None
            auc_diff = (chall_m["roc_auc"] - champ_m["roc_auc"]) if (chall_m["roc_auc"] is not None and champ_m["roc_auc"] is not None) else None

            if n >= 10 and acc_diff is not None:
                status = "CHALLENGER_SUPERIOR" if acc_diff > 0 else ("CHALLENGER_INFERIOR" if acc_diff < 0 else "EQUAL")
            else:
                status = "INSUFFICIENT_FORWARD_DATA"

            per_symbol_results[sym_clean] = {
                "symbol": sym_clean,
                "asset_region": get_symbol_region(sym_clean),
                "sample_size": n,
                "champion_accuracy": champ_m["accuracy"],
                "challenger_accuracy": chall_m["accuracy"],
                "accuracy_difference": acc_diff,
                "champion_brier": champ_m["brier_score"],
                "challenger_brier": chall_m["brier_score"],
                "brier_difference": brier_diff,
                "champion_roc_auc": champ_m["roc_auc"],
                "challenger_roc_auc": chall_m["roc_auc"],
                "roc_auc_difference": auc_diff,
                "status": status
            }

        return {
            "total_universe_symbols": len(ALL_SYMBOLS),
            "symbols_evaluated": per_symbol_results
        }

    def compute_asset_group_results(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Breaks down performance by INDIA, USA, CRYPTO, and ALL-ASSETS."""
        groups: Dict[str, List[Dict[str, Any]]] = {
            "INDIA": [],
            "USA": [],
            "CRYPTO": [],
            "ALL-ASSETS": list(paired_records)
        }

        for r in paired_records:
            region = get_symbol_region(r["symbol"])
            if region in groups:
                groups[region].append(r)

        group_results = {}
        for g_name, recs in groups.items():
            champ_m = calculate_metrics_for_records(recs, "champion")
            chall_m = calculate_metrics_for_records(recs, "challenger")

            acc_diff = (chall_m["accuracy"] - champ_m["accuracy"]) if (chall_m["accuracy"] is not None and champ_m["accuracy"] is not None) else None
            brier_diff = (chall_m["brier_score"] - champ_m["brier_score"]) if (chall_m["brier_score"] is not None and champ_m["brier_score"] is not None) else None
            auc_diff = (chall_m["roc_auc"] - champ_m["roc_auc"]) if (chall_m["roc_auc"] is not None and champ_m["roc_auc"] is not None) else None

            if len(recs) >= 10 and acc_diff is not None:
                status = "CHALLENGER_SUPERIOR" if acc_diff > 0 else ("CHALLENGER_INFERIOR" if acc_diff < 0 else "EQUAL")
            else:
                status = "INSUFFICIENT_FORWARD_DATA"

            group_results[g_name] = {
                "group_name": g_name,
                "sample_size": len(recs),
                "champion": champ_m,
                "challenger": chall_m,
                "comparison": {
                    "accuracy_delta": acc_diff,
                    "brier_delta": brier_diff,
                    "roc_auc_delta": auc_diff,
                    "status": status
                }
            }

        return group_results

    def compute_regime_results(
        self,
        paired_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluates model performance across Phase 13 market regimes."""
        regimes: Dict[str, List[Dict[str, Any]]] = {
            "BULL": [],
            "BEAR": [],
            "SIDEWAYS": [],
            "HIGH_VOLATILITY": [],
            "LOW_VOLATILITY": []
        }

        for r in paired_records:
            t_reg = r.get("trend_regime", "UNKNOWN").upper()
            v_reg = r.get("volatility_regime", "UNKNOWN").upper()

            if t_reg in regimes:
                regimes[t_reg].append(r)
            if v_reg in regimes:
                regimes[v_reg].append(r)

        regime_results = {}
        for reg_name, recs in regimes.items():
            champ_m = calculate_metrics_for_records(recs, "champion")
            chall_m = calculate_metrics_for_records(recs, "challenger")

            acc_diff = (chall_m["accuracy"] - champ_m["accuracy"]) if (chall_m["accuracy"] is not None and champ_m["accuracy"] is not None) else None
            brier_diff = (chall_m["brier_score"] - champ_m["brier_score"]) if (chall_m["brier_score"] is not None and champ_m["brier_score"] is not None) else None
            auc_diff = (chall_m["roc_auc"] - champ_m["roc_auc"]) if (chall_m["roc_auc"] is not None and champ_m["roc_auc"] is not None) else None

            if len(recs) >= 10 and acc_diff is not None:
                status = "CHALLENGER_SUPERIOR" if acc_diff > 0 else ("CHALLENGER_INFERIOR" if acc_diff < 0 else "EQUAL")
            else:
                status = "INSUFFICIENT_FORWARD_DATA"

            regime_results[reg_name] = {
                "regime": reg_name,
                "sample_size": len(recs),
                "champion": champ_m,
                "challenger": chall_m,
                "comparison": {
                    "accuracy_delta": acc_diff,
                    "brier_delta": brier_diff,
                    "roc_auc_delta": auc_diff,
                    "status": status
                }
            }

        return regime_results


regime_and_asset_engine = RegimeAndAssetAnalysisEngine()
