# StockSense AI — Data Provenance & Licensing Documentation

## Data Provenance Matrix

| Data Type | Primary Source | Provider Symbol Format | Point-in-Time Support | Timestamp Meaning | Licensing Limitations |
|---|---|---|---|---|---|
| **Market Prices (OHLCV)** | Yahoo Finance | Exchange Tickers (`RELIANCE.NS`, `AAPL`, `BTC-USD`) | Yes (Daily Bars) | Close of Trading Session | Non-commercial educational research feed |
| **Point-in-Time Fundamentals** | SEC EDGAR / Exchange Filings | Corporate CIK / Symbol | `UNAVAILABLE` (Free API) | Official Public Availability Date | Historical filing dates require institutional SEC feed |
| **Timestamped News** | Global News Feeds | Ticker Tags | `UNAVAILABLE` (Free API) | Article Publication Timestamp | 2-year news archive requires RavenPack/FinNHit feed |

## Unavailable Periods & System Limitations
- **Historical Fundamental Filing Dates**: Yahoo Finance free tier returns current fundamental ratios without historical SEC filing availability timestamps ($T_{pub}$).
- **Historical News Archive**: Yahoo Finance free tier returns only latest ~10 news items, insufficient for a 2-year out-of-sample backtest.
