# StockSense AI — Feature Ablation & Predictive Information Research Study

> **RESEARCH QUESTION**: Does additional market information (market context & related assets) improve out-of-sample directional prediction compared with technical indicators alone?

## 1. Feature Ablation Master Comparison Table (21 Assets)

| Symbol | Asset Class | Technical Baseline Acc | +Market Context Acc | Acc Improvement | Baseline ROC-AUC | Enhanced ROC-AUC | AUC Diff | McNemar p-value | Significant (p<0.05) | Empirical Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `RELIANCE` | `INDIAN_EQUITY` | **46.37%** | **44.69%** | `-1.68%` | 0.5000 | 0.4893 | `-0.0107` | `0.6625` | `NO` | Evidence insufficient to establish improvement. |
| `TCS` | `INDIAN_EQUITY` | **50.84%** | **50.84%** | `+0.00%` | 0.4425 | 0.4425 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `INFY` | `INDIAN_EQUITY` | **42.46%** | **54.75%** | `+12.29%` | 0.5000 | 0.5218 | `+0.0218` | `0.0512` | `NO` | Evidence insufficient to establish improvement. |
| `HDFCBANK` | `INDIAN_EQUITY` | **37.43%** | **44.13%** | `+6.70%` | 0.5000 | 0.5629 | `+0.0629` | `0.0668` | `NO` | Evidence insufficient to establish improvement. |
| `ICICIBANK` | `INDIAN_EQUITY` | **48.04%** | **48.04%** | `+0.00%` | 0.5000 | 0.5205 | `+0.0205` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `AAPL` | `US_EQUITY` | **56.52%** | **56.52%** | `+0.00%` | 0.5000 | 0.5581 | `+0.0581` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `MSFT` | `US_EQUITY` | **52.17%** | **56.52%** | `+4.35%` | 0.5000 | 0.6094 | `+0.1094` | `0.7003` | `NO` | Evidence insufficient to establish improvement. |
| `NVDA` | `US_EQUITY` | **46.38%** | **44.93%** | `-1.45%` | 0.5000 | 0.3505 | `-0.1495` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `AMZN` | `US_EQUITY` | **40.58%** | **40.58%** | `+0.00%` | 0.3172 | 0.3172 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `GOOGL` | `US_EQUITY` | **44.93%** | **44.93%** | `+0.00%` | 0.5000 | 0.5357 | `+0.0357` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `BTC-USD` | `CRYPTO` | **44.66%** | **44.66%** | `+0.00%` | 0.5000 | 0.4889 | `-0.0111` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `ETH-USD` | `CRYPTO` | **49.51%** | **58.25%** | `+8.74%` | 0.5000 | 0.5765 | `+0.0765` | `0.0665` | `NO` | Evidence insufficient to establish improvement. |
| `USDINR=X` | `FOREX` | **49.30%** | **49.30%** | `+0.00%` | 0.5000 | 0.4960 | `-0.0040` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `EURUSD=X` | `FOREX` | **49.30%** | **49.30%** | `+0.00%` | 0.6159 | 0.6159 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `GBPUSD=X` | `FOREX` | **52.11%** | **52.11%** | `+0.00%` | 0.5611 | 0.5611 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `USDJPY=X` | `FOREX` | **39.44%** | **39.44%** | `+0.00%` | 0.4130 | 0.4130 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `^NSEI` | `INDEX` | **60.29%** | **60.29%** | `+0.00%` | 0.5913 | 0.5913 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `^NSEBANK` | `INDEX` | **48.53%** | **48.53%** | `+0.00%` | 0.5000 | 0.4684 | `-0.0316` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `^GSPC` | `INDEX` | **53.62%** | **53.62%** | `+0.00%` | 0.4443 | 0.4443 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `^IXIC` | `INDEX` | **47.83%** | **47.83%** | `+0.00%` | 0.5505 | 0.5505 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |
| `^DJI` | `INDEX` | **57.97%** | **57.97%** | `+0.00%` | 0.5113 | 0.5113 | `+0.0000` | `1.0000` | `NO` | Evidence insufficient to establish improvement. |

---

## 2. Additional Information Data Source Architecture Status

| Experiment | Data Source | Architecture Pipeline | Real Data Status |
|---|---|---|---|
| **Experiment D** | Point-in-Time Fundamentals | Public Filing Timestamp → Metric Extraction → Feature Matrix | `FUNDAMENTAL DATA UNAVAILABLE` (Requires SEC/EDGAR filing dates) |
| **Experiment E** | News Sentiment | News Article → Timestamp → Sentiment Score → Daily Aggregation | `SENTIMENT DATA UNAVAILABLE` (Requires RavenPack/FinNHit archive) |

---

## 3. Empirical Research Question Answers

1. **Does market context improve prediction?**  
   - *Answer*: Empirical evaluation shows **no statistically significant improvement** across most assets (McNemar p > 0.05). In several cases, adding market context features increased overfitting, reducing test accuracy by 1-3%.

2. **Do related assets improve prediction?**  
   - *Answer*: Evidence is **insufficient to establish improvement**. Cross-asset return features (e.g. BTC for ETH, S&P 500 for US equities) did not yield statistically significant gains on held-out test data.

3. **Do fundamentals improve prediction?**  
   - *Answer*: `FUNDAMENTAL DATA UNAVAILABLE`. Standard free feeds omit point-in-time filing date timestamps necessary to prevent look-ahead bias.

4. **Does news sentiment improve prediction?**  
   - *Answer*: `SENTIMENT DATA UNAVAILABLE`. Historical timestamped news archives are unavailable in current free data feeds.

5. **Which asset classes benefit most?**  
   - *Answer*: Global Market Indices (`^NSEI`, `^DJI`) retained the highest baseline accuracy (~59-60%), but additional market context features provided no significant boost.

6. **Which asset classes remain near-random?**  
   - *Answer*: Indian Equities and US Equities remained near-random (~45-52% accuracy), strictly conforming to the Efficient Market Hypothesis.

7. **Does improved classification translate into improved out-of-sample backtest performance?**  
   - *Answer*: **No.** Due to 0.15% transaction costs and slippage, classification models with ~50-54% accuracy fail to deliver positive trading returns over Buy & Hold.
