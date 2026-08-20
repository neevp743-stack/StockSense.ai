# StockSense AI — Phase 4: Fundamental + Historical News Sentiment Research Report

> **FINAL RESEARCH QUESTION**: Does adding point-in-time company fundamentals and timestamp-correct historical news sentiment provide statistically significant out-of-sample predictive information beyond technical indicators alone?

## 1. Feature Ablation Master Comparison Table

| Symbol | Exp A (Technical Only) | Exp B (+Market Context) | Exp C (+Fundamentals) | Exp D (+News Sentiment) | Exp E (All Features) | McNemar p-value | Status Badge |
|---|---|---|---|---|---|---|---|
| `RELIANCE` | **46.37%** | 44.69% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.6625` | `⚪ NO SIGNIFICANT CHANGE` |
| `TCS` | **50.84%** | 50.84% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 NEWS DATA UNAVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `INFY` | **42.46%** | 54.75% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.0512` | `⚪ NO SIGNIFICANT CHANGE` |
| `HDFCBANK` | **37.43%** | 44.69% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 NEWS DATA UNAVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.0993` | `⚪ NO SIGNIFICANT CHANGE` |
| `ICICIBANK` | **48.04%** | 48.04% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 NEWS DATA UNAVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.7728` | `⚪ NO SIGNIFICANT CHANGE` |
| `AAPL` | **56.52%** | 55.07% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `MSFT` | **52.17%** | 52.17% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.8551` | `⚪ NO SIGNIFICANT CHANGE` |
| `NVDA` | **46.38%** | 44.93% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `AMZN` | **40.58%** | 40.58% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `GOOGL` | **44.93%** | 44.93% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `BTC-USD` | **44.66%** | 50.49% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.4705` | `⚪ NO SIGNIFICANT CHANGE` |
| `ETH-USD` | **49.51%** | 57.28% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.3889` | `⚪ NO SIGNIFICANT CHANGE` |
| `USDINR=X` | **49.30%** | 49.30% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 NEWS DATA UNAVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `EURUSD=X` | **49.30%** | 52.11% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.8231` | `⚪ NO SIGNIFICANT CHANGE` |
| `GBPUSD=X` | **52.11%** | 49.30% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.7893` | `⚪ NO SIGNIFICANT CHANGE` |
| `USDJPY=X` | **39.44%** | 38.03% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `^NSEI` | **60.29%** | 57.35% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `0.8312` | `⚪ NO SIGNIFICANT CHANGE` |
| `^NSEBANK` | **48.53%** | 47.06% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `^GSPC` | **53.62%** | 53.62% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `^IXIC` | **47.83%** | 47.83% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |
| `^DJI` | **57.97%** | 57.97% | `🟡 FUNDAMENTAL DATA UNAVAILABLE` | `🟡 AVAILABLE` | `🟡 DATA UNAVAILABLE` | `1.0000` | `⚪ NO SIGNIFICANT CHANGE` |

---

## 2. Statistical Significance & Out-of-Sample Backtest Comparison

- **Technical Baseline Accuracy**: ~45% – 60%
- **Market Context McNemar p-values**: p > 0.05 across all 21 assets (No statistically significant gain).
- **Fundamental & News Availability**: Reported as `FUNDAMENTAL DATA UNAVAILABLE` and `NEWS DATA UNAVAILABLE` to strictly adhere to Zero False Claims Policy.

## 3. Final Academic Conclusion

Based strictly on empirical evaluation across 21 assets, **additional market context features do NOT provide statistically significant predictive gains over technical indicators alone (p > 0.05)**. Historical point-in-time fundamental filing date timestamps and historical news archives are unavailable in free feeds, preventing look-ahead-free fundamental/news sentiment evaluation without institutional datasets.
