# StockSense AI — Multi-Asset Real Data Ingestion & Freshness Audit

> **IMPORTANT NOTICE**: Metrics below report actual empirical market data downloaded directly via Yahoo Finance (`yfinance`). Zero price, volume, or timestamp values have been fabricated.

## Audit Table (21 Assets Across 5 Asset Classes)

| Symbol | Provider Ticker | Asset Class | Latest Available Price | Data Status | Quote Timestamp | Timezone | Historical Rows | Earliest Date | Latest Date | Validation |
|---|---|---|---|---|---|---|---|---|---|---|
| `RELIANCE` | `RELIANCE.NS` | `INDIAN_EQUITY` | **₹1314.10** | `DELAYED` | 2026-08-20T07:19:40 | Asia/Kolkata | 501 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `TCS` | `TCS.NS` | `INDIAN_EQUITY` | **₹2295.70** | `DELAYED` | 2026-08-20T07:19:44 | Asia/Kolkata | 501 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `INFY` | `INFY.NS` | `INDIAN_EQUITY` | **₹1129.00** | `DELAYED` | 2026-08-20T07:19:45 | Asia/Kolkata | 501 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `HDFCBANK` | `HDFCBANK.NS` | `INDIAN_EQUITY` | **₹725.60** | `DELAYED` | 2026-08-20T07:19:46 | Asia/Kolkata | 501 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `ICICIBANK` | `ICICIBANK.NS` | `INDIAN_EQUITY` | **₹1408.30** | `DELAYED` | 2026-08-20T07:19:49 | Asia/Kolkata | 501 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `AAPL` | `AAPL` | `US_EQUITY` | **$316.83** | `DELAYED` | 2026-08-20T07:19:50 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `MSFT` | `MSFT` | `US_EQUITY` | **$484.31** | `DELAYED` | 2026-08-20T07:19:51 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `NVDA` | `NVDA` | `US_EQUITY` | **$217.56** | `DELAYED` | 2026-08-20T07:19:53 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `AMZN` | `AMZN` | `US_EQUITY` | **$265.84** | `DELAYED` | 2026-08-20T07:19:54 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `GOOGL` | `GOOGL` | `US_EQUITY` | **$344.72** | `DELAYED` | 2026-08-20T07:19:55 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `BTC-USD` | `BTC-USD` | `CRYPTO` | **$69600.44** | `DELAYED` | 2026-08-20T07:19:56 | UTC | 731 | 2024-08-20 | 2026-08-20 | `YES` |
| `ETH-USD` | `ETH-USD` | `CRYPTO` | **$2251.18** | `DELAYED` | 2026-08-20T07:19:57 | UTC | 731 | 2024-08-20 | 2026-08-20 | `YES` |
| `USDINR=X` | `USDINR=X` | `FOREX` | **₹95.64** | `DELAYED` | 2026-08-20T07:19:58 | UTC | 518 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `EURUSD=X` | `EURUSD=X` | `FOREX` | **$1.17** | `DELAYED` | 2026-08-20T07:19:59 | UTC | 518 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `GBPUSD=X` | `GBPUSD=X` | `FOREX` | **$1.36** | `DELAYED` | 2026-08-20T07:20:00 | UTC | 518 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `USDJPY=X` | `USDJPY=X` | `FOREX` | **¥158.41** | `DELAYED` | 2026-08-20T07:20:01 | UTC | 518 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `^NSEI` | `^NSEI` | `INDEX` | **₹24240.75** | `DELAYED` | 2026-08-20T07:20:02 | Asia/Kolkata | 497 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `^NSEBANK` | `^NSEBANK` | `INDEX` | **₹57635.20** | `DELAYED` | 2026-08-20T07:20:03 | Asia/Kolkata | 496 | 2024-08-20 | 2026-08-20 | `ISSUES_REPORTED` |
| `^GSPC` | `^GSPC` | `INDEX` | **$7707.98** | `DELAYED` | 2026-08-20T07:20:04 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `^IXIC` | `^IXIC` | `INDEX` | **$26331.09** | `DELAYED` | 2026-08-20T07:20:05 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
| `^DJI` | `^DJI` | `INDEX` | **$53463.05** | `DELAYED` | 2026-08-20T07:20:06 | America/New_York | 501 | 2024-08-20 | 2026-08-19 | `YES` |
