# StockSense AI — Multi-Asset Model Evaluation & Cross-Asset Empirical Research Report

> **RESEARCH DISCLAIMER & ZERO FALSE CLAIMS NOTICE**  
> All evaluation metrics and backtest returns reported below were executed strictly on the held-out 15% out-of-sample test set (179 trading days). Model probabilities represent directional statistical outputs and do **NOT** guarantee trading profits.

## 1. Master Multi-Asset Model Evaluation Summary (21 Assets)

| Symbol | Asset Class | Dataset Size | Test Date Range | Best Model | Test Acc % | F1 Score | ROC-AUC | Brier Score | Out-of-Sample Return | Buy & Hold Return | Random Baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `RELIANCE` | `INDIAN_EQUITY` | 1191 | 2021-11-01 to 2026-08-20 | **MajorityBaseline** | **46.37%** | 0.6336 | 0.5000 | 0.5363 | `-14.93%` | `-14.80%` | `-16.67%` |
| `TCS` | `INDIAN_EQUITY` | 1191 | 2021-11-01 to 2026-08-20 | **LSTM** | **49.41%** | 0.5275 | 0.4916 | 0.2760 | `-21.61%` | `-28.02%` | `-25.34%` |
| `INFY` | `INDIAN_EQUITY` | 1191 | 2021-11-01 to 2026-08-20 | **MajorityBaseline** | **42.46%** | 0.5961 | 0.5000 | 0.5754 | `-29.17%` | `-29.07%` | `-25.65%` |
| `HDFCBANK` | `INDIAN_EQUITY` | 1191 | 2021-11-01 to 2026-08-20 | **RandomForest** | **45.25%** | 0.5505 | 0.5316 | 0.2539 | `-21.07%` | `-28.04%` | `-25.57%` |
| `ICICIBANK` | `INDIAN_EQUITY` | 1191 | 2021-11-01 to 2026-08-20 | **MajorityBaseline** | **48.04%** | 0.6491 | 0.5000 | 0.5196 | `+0.60%` | `+0.75%` | `-12.88%` |
| `AAPL` | `US_EQUITY` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **56.52%** | 0.7222 | 0.5000 | 0.4348 | `+5.86%` | `+6.02%` | `-1.51%` |
| `MSFT` | `US_EQUITY` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **52.17%** | 0.6857 | 0.5000 | 0.4783 | `+16.79%` | `+16.97%` | `+3.38%` |
| `NVDA` | `US_EQUITY` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **46.38%** | 0.6337 | 0.5000 | 0.5362 | `+0.10%` | `+0.25%` | `-4.63%` |
| `AMZN` | `US_EQUITY` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **42.03%** | 0.5918 | 0.5000 | 0.5797 | `-3.69%` | `-3.55%` | `-6.42%` |
| `GOOGL` | `US_EQUITY` | 452 | 2024-10-29 to 2026-08-19 | **LogisticRegression** | **56.52%** | 0.6429 | 0.6545 | 0.2461 | `-4.83%` | `-11.38%` | `-10.42%` |
| `BTC-USD` | `CRYPTO` | 682 | 2024-10-08 to 2026-08-20 | **LSTM** | **46.81%** | 0.6377 | 0.4618 | 0.3085 | `-14.26%` | `-14.13%` | `-13.85%` |
| `ETH-USD` | `CRYPTO` | 682 | 2024-10-08 to 2026-08-20 | **LogisticRegression** | **58.25%** | 0.6815 | 0.5765 | 0.2483 | `+36.51%` | `-3.23%` | `-7.66%` |
| `USDINR=X` | `FOREX` | 469 | 2024-10-28 to 2026-08-20 | **MajorityBaseline** | **49.30%** | 0.6604 | 0.5000 | 0.5070 | `+0.04%` | `+0.19%` | `-4.85%` |
| `EURUSD=X` | `FOREX` | 469 | 2024-10-28 to 2026-08-20 | **RandomForest** | **56.34%** | 0.6173 | 0.5508 | 0.2475 | `-1.73%` | `-1.33%` | `-5.74%` |
| `GBPUSD=X` | `FOREX` | 469 | 2024-10-28 to 2026-08-20 | **LogisticRegression** | **52.11%** | 0.6731 | 0.5611 | 0.2495 | `-0.10%` | `-0.00%` | `-5.19%` |
| `USDJPY=X` | `FOREX` | 469 | 2024-10-28 to 2026-08-20 | **LSTM** | **53.23%** | 0.6667 | 0.5463 | 0.2463 | `-1.07%` | `+1.19%` | `-4.54%` |
| `^NSEI` | `INDEX` | 448 | 2024-10-29 to 2026-08-20 | **LogisticRegression** | **60.29%** | 0.5091 | 0.5913 | 0.2480 | `-2.63%` | `+1.64%` | `-4.66%` |
| `^NSEBANK` | `INDEX` | 447 | 2024-10-29 to 2026-08-20 | **MajorityBaseline** | **48.53%** | 0.6535 | 0.5000 | 0.5147 | `+5.59%` | `+5.75%` | `-2.94%` |
| `^GSPC` | `INDEX` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **53.62%** | 0.6981 | 0.5000 | 0.4638 | `+3.61%` | `+3.76%` | `-2.96%` |
| `^IXIC` | `INDEX` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **47.83%** | 0.6471 | 0.5000 | 0.5217 | `-0.09%` | `+0.06%` | `-4.59%` |
| `^DJI` | `INDEX` | 452 | 2024-10-29 to 2026-08-19 | **MajorityBaseline** | **59.42%** | 0.7455 | 0.5000 | 0.4058 | `+7.16%` | `+7.32%` | `-1.17%` |

---

## 2. Cross-Asset Research Analysis (Average Performance by Asset Class)

| Asset Class | Assets Evaluated | Avg Test Accuracy | Avg F1 Score | Avg ROC-AUC | Avg Brier Score | Predictability Category |
|---|---|---|---|---|---|---|
| **INDIAN_EQUITY** | 5 | **46.31%** | 0.5913 | 0.5046 | 0.4322 | `WEAK SIGNAL (~50-55%)` |
| **US_EQUITY** | 5 | **50.72%** | 0.6553 | 0.5309 | 0.4550 | `WEAK SIGNAL (~50-55%)` |
| **CRYPTO** | 2 | **52.53%** | 0.6596 | 0.5192 | 0.2784 | `WEAK SIGNAL (~50-55%)` |
| **FOREX** | 4 | **52.74%** | 0.6544 | 0.5395 | 0.3126 | `WEAK SIGNAL (~50-55%)` |
| **INDEX** | 5 | **53.94%** | 0.6506 | 0.5183 | 0.4308 | `WEAK SIGNAL (~50-55%)` |

---

## 3. Detailed Asset-by-Asset Model Suite Breakdown

### Asset: `RELIANCE` (INDIAN_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 1191 rows (2021-11-01 to 2026-08-20)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `-14.93%` | **Buy & Hold**: `-14.80%` | **Random Baseline**: `-16.67%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 46.37% | 46.37% | 100.00% | 0.6336 | 0.5000 | 0.5363 |
| **LogisticRegression** | 50.28% | 42.86% | 21.69% | 0.2880 | 0.4372 | 0.2509 |
| **RandomForest** | 47.49% | 46.15% | 79.52% | 0.5841 | 0.4868 | 0.2536 |
| **XGBoost** | 44.69% | 44.94% | 85.54% | 0.5892 | 0.4893 | 0.2514 |
| **LSTM** | 50.59% | 46.88% | 57.69% | 0.5172 | 0.5247 | 0.2666 |
| **Ensemble** | 46.37% | 46.37% | 100.00% | 0.6336 | 0.5064 | 0.2696 |

### Asset: `TCS` (INDIAN_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 1191 rows (2021-11-01 to 2026-08-20)
- **Best Model**: `LSTM`
- **Out-of-Sample AI Return**: `-21.61%` | **Buy & Hold**: `-28.02%` | **Random Baseline**: `-25.34%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 54.19% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.4581 |
| **LogisticRegression** | 45.81% | 42.27% | 50.00% | 0.4581 | 0.4637 | 0.2508 |
| **RandomForest** | 54.19% | 50.00% | 8.54% | 0.1458 | 0.5391 | 0.2472 |
| **XGBoost** | 50.84% | 44.64% | 30.49% | 0.3623 | 0.4425 | 0.2520 |
| **LSTM** | 49.41% | 45.71% | 62.34% | 0.5275 | 0.4916 | 0.2760 |
| **Ensemble** | 54.19% | 0.00% | 0.00% | 0.0000 | 0.4732 | 0.2529 |

### Asset: `INFY` (INDIAN_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 1191 rows (2021-11-01 to 2026-08-20)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `-29.17%` | **Buy & Hold**: `-29.07%` | **Random Baseline**: `-25.65%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 42.46% | 42.46% | 100.00% | 0.5961 | 0.5000 | 0.5754 |
| **LogisticRegression** | 46.93% | 35.82% | 31.58% | 0.3357 | 0.4757 | 0.2501 |
| **RandomForest** | 54.75% | 42.86% | 19.74% | 0.2703 | 0.5395 | 0.2474 |
| **XGBoost** | 54.75% | 46.03% | 38.16% | 0.4173 | 0.5218 | 0.2498 |
| **LSTM** | 45.29% | 41.54% | 76.06% | 0.5373 | 0.4782 | 0.2673 |
| **Ensemble** | 42.46% | 42.46% | 100.00% | 0.5961 | 0.4920 | 0.2752 |

### Asset: `HDFCBANK` (INDIAN_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 1191 rows (2021-11-01 to 2026-08-20)
- **Best Model**: `RandomForest`
- **Out-of-Sample AI Return**: `-21.07%` | **Buy & Hold**: `-28.04%` | **Random Baseline**: `-25.57%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 37.43% | 37.43% | 100.00% | 0.5447 | 0.5000 | 0.6257 |
| **LogisticRegression** | 44.13% | 38.46% | 82.09% | 0.5238 | 0.5629 | 0.2516 |
| **RandomForest** | 45.25% | 39.74% | 89.55% | 0.5505 | 0.5316 | 0.2539 |
| **XGBoost** | 44.69% | 37.30% | 70.15% | 0.4870 | 0.5028 | 0.2539 |
| **LSTM** | 50.00% | 35.21% | 39.06% | 0.3704 | 0.4601 | 0.2640 |
| **Ensemble** | 37.43% | 37.43% | 100.00% | 0.5447 | 0.4851 | 0.2816 |

### Asset: `ICICIBANK` (INDIAN_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 1191 rows (2021-11-01 to 2026-08-20)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+0.60%` | **Buy & Hold**: `+0.75%` | **Random Baseline**: `-12.88%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.5000 | 0.5196 |
| **LogisticRegression** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.5205 | 0.2518 |
| **RandomForest** | 45.81% | 46.86% | 95.35% | 0.6284 | 0.4652 | 0.2586 |
| **XGBoost** | 48.04% | 47.90% | 93.02% | 0.6324 | 0.5016 | 0.2539 |
| **LSTM** | 51.76% | 50.62% | 49.40% | 0.5000 | 0.5082 | 0.2757 |
| **Ensemble** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.5196 | 0.2734 |

### Asset: `AAPL` (US_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+5.86%` | **Buy & Hold**: `+6.02%` | **Random Baseline**: `-1.51%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 56.52% | 56.52% | 100.00% | 0.7222 | 0.5000 | 0.4348 |
| **LogisticRegression** | 43.48% | 50.00% | 23.08% | 0.3158 | 0.4983 | 0.2540 |
| **RandomForest** | 56.52% | 56.52% | 100.00% | 0.7222 | 0.5581 | 0.2449 |
| **XGBoost** | 55.07% | 56.25% | 92.31% | 0.6990 | 0.5077 | 0.2468 |
| **LSTM** | 46.67% | 0.00% | 0.00% | 0.0000 | 0.4754 | 0.2599 |
| **Ensemble** | 56.52% | 56.52% | 100.00% | 0.7222 | 0.5085 | 0.2471 |

### Asset: `MSFT` (US_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+16.79%` | **Buy & Hold**: `+16.97%` | **Random Baseline**: `+3.38%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 52.17% | 52.17% | 100.00% | 0.6857 | 0.5000 | 0.4783 |
| **LogisticRegression** | 49.28% | 60.00% | 8.33% | 0.1463 | 0.5269 | 0.2614 |
| **RandomForest** | 56.52% | 57.14% | 66.67% | 0.6154 | 0.6094 | 0.2444 |
| **XGBoost** | 52.17% | 53.85% | 58.33% | 0.5600 | 0.4865 | 0.2559 |
| **LSTM** | 43.33% | 47.73% | 65.62% | 0.5526 | 0.4342 | 0.3028 |
| **Ensemble** | 52.17% | 52.17% | 100.00% | 0.6857 | 0.4806 | 0.2616 |

### Asset: `NVDA` (US_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+0.10%` | **Buy & Hold**: `+0.25%` | **Random Baseline**: `-4.63%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 46.38% | 46.38% | 100.00% | 0.6337 | 0.5000 | 0.5362 |
| **LogisticRegression** | 52.17% | 45.45% | 15.62% | 0.2326 | 0.4696 | 0.2542 |
| **RandomForest** | 44.93% | 45.59% | 96.88% | 0.6200 | 0.3505 | 0.2686 |
| **XGBoost** | 44.93% | 44.83% | 81.25% | 0.5778 | 0.4231 | 0.2631 |
| **LSTM** | 65.00% | 76.92% | 35.71% | 0.4878 | 0.6663 | 0.2290 |
| **Ensemble** | 46.38% | 46.38% | 100.00% | 0.6337 | 0.5177 | 0.2668 |

### Asset: `AMZN` (US_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `-3.69%` | **Buy & Hold**: `-3.55%` | **Random Baseline**: `-6.42%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 42.03% | 42.03% | 100.00% | 0.5918 | 0.5000 | 0.5797 |
| **LogisticRegression** | 42.03% | 42.03% | 100.00% | 0.5918 | 0.4983 | 0.2608 |
| **RandomForest** | 42.03% | 42.03% | 100.00% | 0.5918 | 0.3793 | 0.2735 |
| **XGBoost** | 40.58% | 41.18% | 96.55% | 0.5773 | 0.3172 | 0.2754 |
| **LSTM** | 58.33% | 50.00% | 16.00% | 0.2424 | 0.6263 | 0.2415 |
| **Ensemble** | 42.03% | 42.03% | 100.00% | 0.5918 | 0.3526 | 0.2873 |

### Asset: `GOOGL` (US_EQUITY)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `LogisticRegression`
- **Out-of-Sample AI Return**: `-4.83%` | **Buy & Hold**: `-11.38%` | **Random Baseline**: `-10.42%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 44.93% | 44.93% | 100.00% | 0.6200 | 0.5000 | 0.5507 |
| **LogisticRegression** | 56.52% | 50.94% | 87.10% | 0.6429 | 0.6545 | 0.2461 |
| **RandomForest** | 43.48% | 43.55% | 87.10% | 0.5806 | 0.4898 | 0.2585 |
| **XGBoost** | 44.93% | 44.93% | 100.00% | 0.6200 | 0.5357 | 0.2555 |
| **LSTM** | 46.67% | 46.43% | 92.86% | 0.6190 | 0.6127 | 0.2646 |
| **Ensemble** | 44.93% | 44.93% | 100.00% | 0.6200 | 0.6121 | 0.2777 |

### Asset: `BTC-USD` (CRYPTO)

- **Status**: `MODEL READY`
- **Dataset Size**: 682 rows (2024-10-08 to 2026-08-20)
- **Best Model**: `LSTM`
- **Out-of-Sample AI Return**: `-14.26%` | **Buy & Hold**: `-14.13%` | **Random Baseline**: `-13.85%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 44.66% | 44.66% | 100.00% | 0.6174 | 0.5000 | 0.5534 |
| **LogisticRegression** | 44.66% | 44.66% | 100.00% | 0.6174 | 0.5057 | 0.2524 |
| **RandomForest** | 44.66% | 44.66% | 100.00% | 0.6174 | 0.4889 | 0.2519 |
| **XGBoost** | 50.49% | 45.45% | 54.35% | 0.4950 | 0.5282 | 0.2494 |
| **LSTM** | 46.81% | 46.81% | 100.00% | 0.6377 | 0.4618 | 0.3085 |
| **Ensemble** | 44.66% | 44.66% | 100.00% | 0.6174 | 0.5202 | 0.2885 |

### Asset: `ETH-USD` (CRYPTO)

- **Status**: `MODEL READY`
- **Dataset Size**: 682 rows (2024-10-08 to 2026-08-20)
- **Best Model**: `LogisticRegression`
- **Out-of-Sample AI Return**: `+36.51%` | **Buy & Hold**: `-3.23%` | **Random Baseline**: `-7.66%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 49.51% | 49.51% | 100.00% | 0.6623 | 0.5000 | 0.5049 |
| **LogisticRegression** | 58.25% | 54.76% | 90.20% | 0.6815 | 0.5765 | 0.2483 |
| **RandomForest** | 50.49% | 50.00% | 5.88% | 0.1053 | 0.5260 | 0.2502 |
| **XGBoost** | 57.28% | 59.46% | 43.14% | 0.5000 | 0.5814 | 0.2477 |
| **LSTM** | 46.81% | 47.62% | 41.67% | 0.4444 | 0.4534 | 0.2512 |
| **Ensemble** | 49.51% | 49.51% | 100.00% | 0.6623 | 0.5554 | 0.2591 |

### Asset: `USDINR=X` (FOREX)

- **Status**: `MODEL READY`
- **Dataset Size**: 469 rows (2024-10-28 to 2026-08-20)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+0.04%` | **Buy & Hold**: `+0.19%` | **Random Baseline**: `-4.85%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.5000 | 0.5070 |
| **LogisticRegression** | 47.89% | 48.00% | 68.57% | 0.5647 | 0.4690 | 0.2573 |
| **RandomForest** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.4960 | 0.2544 |
| **XGBoost** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.4575 | 0.2550 |
| **LSTM** | 46.77% | 47.54% | 96.67% | 0.6374 | 0.5115 | 0.3300 |
| **Ensemble** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.4754 | 0.2841 |

### Asset: `EURUSD=X` (FOREX)

- **Status**: `MODEL READY`
- **Dataset Size**: 469 rows (2024-10-28 to 2026-08-20)
- **Best Model**: `RandomForest`
- **Out-of-Sample AI Return**: `-1.73%` | **Buy & Hold**: `-1.33%` | **Random Baseline**: `-5.74%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 50.70% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.4930 |
| **LogisticRegression** | 49.30% | 49.06% | 74.29% | 0.5909 | 0.6159 | 0.2484 |
| **RandomForest** | 56.34% | 54.35% | 71.43% | 0.6173 | 0.5508 | 0.2475 |
| **XGBoost** | 52.11% | 51.28% | 57.14% | 0.5405 | 0.5357 | 0.2495 |
| **LSTM** | 53.23% | 53.85% | 65.62% | 0.5915 | 0.5833 | 0.2515 |
| **Ensemble** | 50.70% | 0.00% | 0.00% | 0.0000 | 0.5524 | 0.2537 |

### Asset: `GBPUSD=X` (FOREX)

- **Status**: `MODEL READY`
- **Dataset Size**: 469 rows (2024-10-28 to 2026-08-20)
- **Best Model**: `LogisticRegression`
- **Out-of-Sample AI Return**: `-0.10%` | **Buy & Hold**: `-0.00%` | **Random Baseline**: `-5.19%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.5000 | 0.5070 |
| **LogisticRegression** | 52.11% | 50.72% | 100.00% | 0.6731 | 0.5611 | 0.2495 |
| **RandomForest** | 50.70% | 50.00% | 65.71% | 0.5679 | 0.4492 | 0.2520 |
| **XGBoost** | 49.30% | 49.15% | 82.86% | 0.6170 | 0.4119 | 0.2531 |
| **LSTM** | 53.23% | 57.14% | 25.81% | 0.3556 | 0.4735 | 0.2788 |
| **Ensemble** | 49.30% | 49.30% | 100.00% | 0.6604 | 0.4643 | 0.2648 |

### Asset: `USDJPY=X` (FOREX)

- **Status**: `MODEL READY`
- **Dataset Size**: 469 rows (2024-10-28 to 2026-08-20)
- **Best Model**: `LSTM`
- **Out-of-Sample AI Return**: `-1.07%` | **Buy & Hold**: `+1.19%` | **Random Baseline**: `-4.54%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 35.21% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.6479 |
| **LogisticRegression** | 39.44% | 61.54% | 17.39% | 0.2712 | 0.4130 | 0.2771 |
| **RandomForest** | 35.21% | 50.00% | 10.87% | 0.1786 | 0.4400 | 0.2649 |
| **XGBoost** | 38.03% | 75.00% | 6.52% | 0.1200 | 0.4543 | 0.2774 |
| **LSTM** | 53.23% | 60.42% | 74.36% | 0.6667 | 0.5463 | 0.2463 |
| **Ensemble** | 35.21% | 0.00% | 0.00% | 0.0000 | 0.4052 | 0.3043 |

### Asset: `^NSEI` (INDEX)

- **Status**: `MODEL READY`
- **Dataset Size**: 448 rows (2024-10-29 to 2026-08-20)
- **Best Model**: `LogisticRegression`
- **Out-of-Sample AI Return**: `-2.63%` | **Buy & Hold**: `+1.64%` | **Random Baseline**: `-4.66%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 51.47% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.4853 |
| **LogisticRegression** | 60.29% | 63.64% | 42.42% | 0.5091 | 0.5913 | 0.2480 |
| **RandomForest** | 57.35% | 60.00% | 36.36% | 0.4528 | 0.5307 | 0.2489 |
| **XGBoost** | 57.35% | 58.33% | 42.42% | 0.4912 | 0.5732 | 0.2464 |
| **LSTM** | 49.15% | 0.00% | 0.00% | 0.0000 | 0.4713 | 0.3748 |
| **Ensemble** | 51.47% | 0.00% | 0.00% | 0.0000 | 0.5541 | 0.2697 |

### Asset: `^NSEBANK` (INDEX)

- **Status**: `MODEL READY`
- **Dataset Size**: 447 rows (2024-10-29 to 2026-08-20)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+5.59%` | **Buy & Hold**: `+5.75%` | **Random Baseline**: `-2.94%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 48.53% | 48.53% | 100.00% | 0.6535 | 0.5000 | 0.5147 |
| **LogisticRegression** | 48.53% | 48.53% | 100.00% | 0.6535 | 0.4684 | 0.2538 |
| **RandomForest** | 50.00% | 49.09% | 81.82% | 0.6136 | 0.4771 | 0.2565 |
| **XGBoost** | 47.06% | 46.51% | 60.61% | 0.5263 | 0.4286 | 0.2588 |
| **LSTM** | 49.15% | 50.00% | 80.00% | 0.6154 | 0.5517 | 0.2539 |
| **Ensemble** | 48.53% | 48.53% | 100.00% | 0.6535 | 0.4407 | 0.2740 |

### Asset: `^GSPC` (INDEX)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+3.61%` | **Buy & Hold**: `+3.76%` | **Random Baseline**: `-2.96%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 53.62% | 53.62% | 100.00% | 0.6981 | 0.5000 | 0.4638 |
| **LogisticRegression** | 53.62% | 53.62% | 100.00% | 0.6981 | 0.5186 | 0.2494 |
| **RandomForest** | 53.62% | 53.62% | 100.00% | 0.6981 | 0.4443 | 0.2594 |
| **XGBoost** | 53.62% | 53.62% | 100.00% | 0.6981 | 0.5203 | 0.2519 |
| **LSTM** | 55.00% | 56.41% | 68.75% | 0.6197 | 0.5904 | 0.2449 |
| **Ensemble** | 53.62% | 53.62% | 100.00% | 0.6981 | 0.5591 | 0.2633 |

### Asset: `^IXIC` (INDEX)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `-0.09%` | **Buy & Hold**: `+0.06%` | **Random Baseline**: `-4.59%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 47.83% | 47.83% | 100.00% | 0.6471 | 0.5000 | 0.5217 |
| **LogisticRegression** | 47.83% | 47.76% | 96.97% | 0.6400 | 0.4503 | 0.2609 |
| **RandomForest** | 47.83% | 47.83% | 100.00% | 0.6471 | 0.5244 | 0.2733 |
| **XGBoost** | 47.83% | 47.37% | 81.82% | 0.6000 | 0.5505 | 0.2608 |
| **LSTM** | 50.00% | 45.00% | 32.14% | 0.3750 | 0.4766 | 0.2505 |
| **Ensemble** | 47.83% | 47.83% | 100.00% | 0.6471 | 0.5202 | 0.2777 |

### Asset: `^DJI` (INDEX)

- **Status**: `MODEL READY`
- **Dataset Size**: 452 rows (2024-10-29 to 2026-08-19)
- **Best Model**: `MajorityBaseline`
- **Out-of-Sample AI Return**: `+7.16%` | **Buy & Hold**: `+7.32%` | **Random Baseline**: `-1.17%`

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 59.42% | 59.42% | 100.00% | 0.7455 | 0.5000 | 0.4058 |
| **LogisticRegression** | 39.13% | 33.33% | 2.44% | 0.0455 | 0.3258 | 0.2564 |
| **RandomForest** | 60.87% | 62.50% | 85.37% | 0.7216 | 0.5836 | 0.2453 |
| **XGBoost** | 57.97% | 61.11% | 80.49% | 0.6947 | 0.5113 | 0.2476 |
| **LSTM** | 61.67% | 75.00% | 51.43% | 0.6102 | 0.6377 | 0.2392 |
| **Ensemble** | 59.42% | 59.42% | 100.00% | 0.7455 | 0.6272 | 0.2372 |

