# StockSense AI — Market Intelligence & Telemetry Specification

**Feature:** Market Intelligence & Telemetry Specification  
**Architecture:** Real-time WebSocket + REST Provider Router  
**Primary Providers:** Coinbase WS (Crypto), Twelve Data REST (Equities & Forex), Finnhub (Secondary Equities)  

---

## 1. Overview & Provider Architecture

StockSense AI delivers real-time quotes, technical candles, and market intelligence for Indian Equities (`RELIANCE`), Cryptocurrencies (`BTC-USD`, `SOL-USD`), and Forex/Commodities (`XAUUSD`).

```
Clients (Web App / Mobile)
        │
        ▼
Provider Router (`provider_router.py`)
        │
        ├── Coinbase WS Stream Manager (Zero latency crypto stream)
        ├── Twelve Data REST API (Equities & Precious Metals)
        └── Bounded Cache Layer (Quote & Candle TTL)
```

---

## 2. Telemetry & Latency Specifications

- **Coinbase WebSocket Stream:** 
  - Tracks live ticks for `BTC-USD` and `SOL-USD`.
  - Reconnect cycles automatically managed without thread deadlock.
  - P50 Stream Latency: `< 5 ms`.
- **Twelve Data REST Provider:**
  - Standardized REST queries for `XAUUSD` and equities.
  - Internal rate limit protection with exponential backoff on HTTP 429.
  - Server compute latency: `< 1.0 ms`.
- **Cache TTL:**
  - Real-time quote cache: 5-second bounded TTL.
  - Candle data cache: 60-second bounded TTL.

---

## 3. Data Integrity & Resilience

1. **Provider Degradation Isolation:** If a third-party market data provider experiences transient rate limits or outages, StockSense AI falls back cleanly to cached telemetry or secondary providers.
2. **Zero Backend Failure Rule:** Provider degradation does NOT trigger a complete backend offline status unless the `/health` endpoint itself reports process failure.
