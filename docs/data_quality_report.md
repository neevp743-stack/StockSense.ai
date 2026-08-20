# StockSense AI — Data Quality & Audit Report

> **Notice**: This report is generated strictly from real historical market data retrieved via Yahoo Finance (`yfinance`). Zero synthetic prices or fake datasets were generated.

## Executive Summary

| Stock Symbol | Yahoo Ticker | Status | Earliest Date | Latest Date | Total Rows | Missing Cells | Duplicates | Invalid Prices | Zero Volume Rows | Suspicious Gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| **RELIANCE** | `RELIANCE.NS` | ✅ Success | 2021-08-20 | 2026-08-20 | 1240 | 0 | 0 | 0 | 5 | 16 |
| **TCS** | `TCS.NS` | ✅ Success | 2021-08-20 | 2026-08-20 | 1240 | 0 | 0 | 0 | 5 | 16 |
| **INFY** | `INFY.NS` | ✅ Success | 2021-08-20 | 2026-08-20 | 1240 | 0 | 0 | 0 | 5 | 16 |
| **HDFCBANK** | `HDFCBANK.NS` | ✅ Success | 2021-08-20 | 2026-08-20 | 1240 | 0 | 0 | 0 | 5 | 16 |
| **ICICIBANK** | `ICICIBANK.NS` | ✅ Success | 2021-08-20 | 2026-08-20 | 1240 | 0 | 0 | 0 | 5 | 16 |

---

## Detailed Data Quality Breakdown per Stock

### RELIANCE (`RELIANCE.NS`)
- **Date Range**: 2021-08-20 to 2026-08-20
- **Total Daily Bar Count**: 1240 trading days
- **Data Integrity Status**: ISSUES FOUND
- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:
  - From `2021-09-09` to `2021-09-13` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-10-14` to `2021-10-18` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-04` to `2021-11-08` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-18` to `2021-11-22` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-03-17` to `2022-03-21` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-04-13` to `2022-04-18` (5 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-06` to `2023-04-10` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-13` to `2023-04-17` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-01-25` to `2024-01-29` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-03-07` to `2024-03-11` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
- **Feature Matrix Rows (post 50-day warm-up drop)**: 1191
- **Feature Columns Generated**: 21 indicators

### TCS (`TCS.NS`)
- **Date Range**: 2021-08-20 to 2026-08-20
- **Total Daily Bar Count**: 1240 trading days
- **Data Integrity Status**: ISSUES FOUND
- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:
  - From `2021-09-09` to `2021-09-13` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-10-14` to `2021-10-18` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-04` to `2021-11-08` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-18` to `2021-11-22` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-03-17` to `2022-03-21` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-04-13` to `2022-04-18` (5 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-06` to `2023-04-10` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-13` to `2023-04-17` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-01-25` to `2024-01-29` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-03-07` to `2024-03-11` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
- **Feature Matrix Rows (post 50-day warm-up drop)**: 1191
- **Feature Columns Generated**: 21 indicators

### INFY (`INFY.NS`)
- **Date Range**: 2021-08-20 to 2026-08-20
- **Total Daily Bar Count**: 1240 trading days
- **Data Integrity Status**: ISSUES FOUND
- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:
  - From `2021-09-09` to `2021-09-13` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-10-14` to `2021-10-18` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-04` to `2021-11-08` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-18` to `2021-11-22` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-03-17` to `2022-03-21` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-04-13` to `2022-04-18` (5 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-06` to `2023-04-10` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-13` to `2023-04-17` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-01-25` to `2024-01-29` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-03-07` to `2024-03-11` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
- **Feature Matrix Rows (post 50-day warm-up drop)**: 1191
- **Feature Columns Generated**: 21 indicators

### HDFCBANK (`HDFCBANK.NS`)
- **Date Range**: 2021-08-20 to 2026-08-20
- **Total Daily Bar Count**: 1240 trading days
- **Data Integrity Status**: ISSUES FOUND
- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:
  - From `2021-09-09` to `2021-09-13` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-10-14` to `2021-10-18` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-04` to `2021-11-08` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-18` to `2021-11-22` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-03-17` to `2022-03-21` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-04-13` to `2022-04-18` (5 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-06` to `2023-04-10` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-13` to `2023-04-17` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-01-25` to `2024-01-29` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-03-07` to `2024-03-11` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
- **Feature Matrix Rows (post 50-day warm-up drop)**: 1191
- **Feature Columns Generated**: 21 indicators

### ICICIBANK (`ICICIBANK.NS`)
- **Date Range**: 2021-08-20 to 2026-08-20
- **Total Daily Bar Count**: 1240 trading days
- **Data Integrity Status**: ISSUES FOUND
- **Suspicious Trading Gaps (>4 calendar days or unexpected mid-week gap)**:
  - From `2021-09-09` to `2021-09-13` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-10-14` to `2021-10-18` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-04` to `2021-11-08` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2021-11-18` to `2021-11-22` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-03-17` to `2022-03-21` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2022-04-13` to `2022-04-18` (5 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-06` to `2023-04-10` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2023-04-13` to `2023-04-17` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-01-25` to `2024-01-29` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
  - From `2024-03-07` to `2024-03-11` (4 calendar days) — *Unexpected mid-week multi-day trading gap*
- **Feature Matrix Rows (post 50-day warm-up drop)**: 1191
- **Feature Columns Generated**: 21 indicators

## Verification of Non-Trading Day Handling
- Weekends (Saturday/Sunday) and official NSE holidays (e.g. Diwali, Independence Day, Republic Day) are correctly treated as standard non-trading intervals.
- No artificial zero-filling or synthetic interpolation was applied across non-trading days.
