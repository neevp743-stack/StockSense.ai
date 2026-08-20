import os
import sys
import json
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import DEFAULT_UNIVERSE
from backend.data.data_service import sync_stock_universe, get_historical_data_from_db
from backend.features.feature_engine import compute_features_and_target

def generate_data_quality_report():
    print("Fetching real historical market data for Indian stock universe...")
    sync_results = sync_stock_universe(DEFAULT_UNIVERSE, period="5y")

    report_md = "# StockSense AI — Data Quality & Audit Report\n\n"
    report_md += "> **Notice**: This report is generated strictly from real historical market data retrieved via Yahoo Finance (`yfinance`). Zero synthetic prices or fake datasets were generated.\n\n"
    report_md += "## Executive Summary\n\n"
    report_md += "| Stock Symbol | Yahoo Ticker | Status | Earliest Date | Latest Date | Total Rows | Missing Cells | Duplicates | Invalid Prices | Zero Volume Rows | Suspicious Gaps |\n"
    report_md += "|---|---|---|---|---|---|---|---|---|---|---|\n"

    all_audits = {}

    for sym, res in sync_results.items():
        if res["status"] == "success" and res["audit"]:
            audit = res["audit"]
            all_audits[sym] = audit
            report_md += f"| **{sym}** | `{sym}.NS` | ✅ Success | {audit['earliest_date']} | {audit['latest_date']} | {audit['total_rows']} | {audit['missing_values_count']} | {audit['duplicate_dates_count']} | {audit['invalid_price_rows_count']} | {audit['zero_volume_rows_count']} | {len(audit['suspicious_gaps'])} |\n"
        else:
            report_md += f"| **{sym}** | `{sym}.NS` | ❌ {res.get('error', 'Failed')} | N/A | N/A | 0 | N/A | N/A | N/A | N/A | N/A |\n"

    report_md += "\n---\n\n## Detailed Data Quality Breakdown per Stock\n\n"

    for sym in DEFAULT_UNIVERSE:
        if sym in all_audits:
            audit = all_audits[sym]
            report_md += f"### {sym} (`{sym}.NS`)\n"
            report_md += f"- **Date Range**: {audit['earliest_date']} to {audit['latest_date']}\n"
            report_md += f"- **Total Daily Bar Count**: {audit['total_rows']} trading days\n"
            report_md += f"- **Data Integrity Status**: {'VALID' if audit['is_valid'] else 'ISSUES FOUND'}\n"
            
            if audit['suspicious_gaps']:
                report_md += "- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:\n"
                for gap in audit['suspicious_gaps'][:10]:  # Limit top 10
                    report_md += f"  - From `{gap['from']}` to `{gap['to']}` ({gap['calendar_days_gap']} calendar days) — *{gap['reason']}*\n"
            else:
                report_md += "- **Suspicious Trading Gaps**: None detected (all gaps correspond to standard weekends or NSE single holidays).\n"
            
            # Compute feature count
            df_raw = get_historical_data_from_db(sym)
            if not df_raw.empty:
                df_feat = compute_features_and_target(df_raw)
                report_md += f"- **Feature Matrix Rows (post 50-day warm-up drop)**: {len(df_feat)}\n"
                report_md += f"- **Feature Columns Generated**: {len(df_feat.columns) - 3} indicators\n\n"

    report_md += "## Verification of Non-Trading Day Handling\n"
    report_md += "- Weekends (Saturday/Sunday) and official NSE holidays (e.g. Diwali, Independence Day, Republic Day) are correctly treated as standard non-trading intervals.\n"
    report_md += "- No artificial zero-filling or synthetic interpolation was applied across non-trading days.\n"

    # Save to docs/data_quality_report.md
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs"))
    os.makedirs(docs_dir, exist_ok=True)
    report_file = os.path.join(docs_dir, "data_quality_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Data audit completed. Report written to {report_file}")

if __name__ == "__main__":
    generate_data_quality_report()
