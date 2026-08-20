import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding='utf-8')

from backend.assets.asset_registry import ASSET_REGISTRY
from backend.data.provider import YFinanceProvider
from backend.data.data_validator import validate_market_data

def run_real_data_ingestion_audit():
    print("=" * 100)
    print("REAL MULTI-ASSET MARKET DATA INGESTION & DATA FRESHNESS AUDIT — 21 ASSETS")
    print("=" * 100)

    provider = YFinanceProvider()
    results = []

    for sym, info in ASSET_REGISTRY.items():
        prov_sym = info["provider_symbol"]
        aclass = info["asset_class"]
        tz = info["timezone"]

        print(f"Fetching real data for [{aclass}] {sym} ({prov_sym})...")
        
        # 1. Latest Quote
        quote = provider.get_latest_quote(sym)
        latest_price = quote.get("price")
        data_status = quote.get("data_status", "UNAVAILABLE")
        quote_ts = quote.get("timestamp", "N/A")

        # 2. Historical Data
        df_hist = provider.get_historical_data(sym, period="2y")
        
        if not df_hist.empty:
            hist_rows = len(df_hist)
            earliest_d = str(df_hist["date"].min())
            latest_d = str(df_hist["date"].max())
            val_report = validate_market_data(df_hist, sym)
            is_valid = val_report["is_valid"]
        else:
            hist_rows = 0
            earliest_d = "UNAVAILABLE"
            latest_d = "UNAVAILABLE"
            is_valid = False

        results.append({
            "symbol": sym,
            "provider_symbol": prov_sym,
            "asset_class": aclass,
            "latest_price": f"{info['currency_symbol']}{latest_price:.2f}" if latest_price else "UNAVAILABLE",
            "timestamp": quote_ts,
            "timezone": tz,
            "data_status": data_status,
            "historical_rows": hist_rows,
            "earliest_date": earliest_d,
            "latest_historical_date": latest_d,
            "data_valid": "YES" if is_valid else "ISSUES_REPORTED"
        })

    res_df = pd.DataFrame(results)
    print("\n" + "=" * 100)
    print("REAL DATA INGESTION AUDIT TABLE")
    print("=" * 100)
    print(res_df.to_string(index=False))

    # Write results to docs/multi_asset_data_audit.md
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs"))
    os.makedirs(docs_dir, exist_ok=True)
    report_path = os.path.join(docs_dir, "multi_asset_data_audit.md")

    md = "# StockSense AI — Multi-Asset Real Data Ingestion & Freshness Audit\n\n"
    md += "> **IMPORTANT NOTICE**: Metrics below report actual empirical market data downloaded directly via Yahoo Finance (`yfinance`). Zero price, volume, or timestamp values have been fabricated.\n\n"
    md += "## Audit Table (21 Assets Across 5 Asset Classes)\n\n"
    md += "| Symbol | Provider Ticker | Asset Class | Latest Available Price | Data Status | Quote Timestamp | Timezone | Historical Rows | Earliest Date | Latest Date | Validation |\n"
    md += "|---|---|---|---|---|---|---|---|---|---|---|\n"

    for r in results:
        md += f"| `{r['symbol']}` | `{r['provider_symbol']}` | `{r['asset_class']}` | **{r['latest_price']}** | `{r['data_status']}` | {r['timestamp'][:19]} | {r['timezone']} | {r['historical_rows']} | {r['earliest_date']} | {r['latest_historical_date']} | `{r['data_valid']}` |\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nAudit complete. Written to {report_path}")

if __name__ == "__main__":
    run_real_data_ingestion_audit()
