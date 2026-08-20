# StockSense AI — Model Evaluation & Performance Report

> **IMPORTANT**: Metrics reported below are strictly empirical evaluations on the held-out 15% test set. Higher model accuracy on historical data does not guarantee future financial returns.

## Stock: RELIANCE

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 46.37% | 46.37% | 100.00% | 0.6336 | 0.5000 | 0.5363 |
| **LogisticRegression** | 50.28% | 42.86% | 21.69% | 0.2880 | 0.4372 | 0.2509 |
| **RandomForest** | 47.49% | 46.15% | 79.52% | 0.5841 | 0.4868 | 0.2536 |
| **XGBoost** | 44.69% | 44.94% | 85.54% | 0.5892 | 0.4893 | 0.2514 |
| **LSTM** | 50.59% | 46.34% | 48.72% | 0.4750 | 0.5339 | 0.2613 |
| **Ensemble** | 46.37% | 46.37% | 100.00% | 0.6336 | 0.5035 | 0.2681 |

## Stock: TCS

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 54.19% | 0.00% | 0.00% | 0.0000 | 0.5000 | 0.4581 |
| **LogisticRegression** | 45.81% | 42.27% | 50.00% | 0.4581 | 0.4637 | 0.2508 |
| **RandomForest** | 54.19% | 50.00% | 8.54% | 0.1458 | 0.5391 | 0.2472 |
| **XGBoost** | 50.84% | 44.64% | 30.49% | 0.3623 | 0.4425 | 0.2520 |
| **LSTM** | 47.06% | 43.56% | 57.14% | 0.4944 | 0.4794 | 0.2987 |
| **Ensemble** | 54.19% | 0.00% | 0.00% | 0.0000 | 0.4605 | 0.2556 |

## Stock: INFY

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 42.46% | 42.46% | 100.00% | 0.5961 | 0.5000 | 0.5754 |
| **LogisticRegression** | 46.93% | 35.82% | 31.58% | 0.3357 | 0.4757 | 0.2501 |
| **RandomForest** | 54.75% | 42.86% | 19.74% | 0.2703 | 0.5395 | 0.2474 |
| **XGBoost** | 54.75% | 46.03% | 38.16% | 0.4173 | 0.5218 | 0.2498 |
| **LSTM** | 42.35% | 39.02% | 67.61% | 0.4948 | 0.4618 | 0.2736 |
| **Ensemble** | 42.46% | 42.46% | 100.00% | 0.5961 | 0.4571 | 0.2773 |

## Stock: HDFCBANK

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 37.43% | 37.43% | 100.00% | 0.5447 | 0.5000 | 0.6257 |
| **LogisticRegression** | 44.13% | 38.46% | 82.09% | 0.5238 | 0.5629 | 0.2516 |
| **RandomForest** | 45.25% | 39.74% | 89.55% | 0.5505 | 0.5316 | 0.2539 |
| **XGBoost** | 44.69% | 37.30% | 70.15% | 0.4870 | 0.5028 | 0.2539 |
| **LSTM** | 61.18% | 47.83% | 34.38% | 0.4000 | 0.5637 | 0.2430 |
| **Ensemble** | 37.43% | 37.43% | 100.00% | 0.5447 | 0.5481 | 0.2840 |

## Stock: ICICIBANK

| Model Name | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Brier Score |
|---|---|---|---|---|---|---|
| **MajorityBaseline** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.5000 | 0.5196 |
| **LogisticRegression** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.5205 | 0.2518 |
| **RandomForest** | 45.81% | 46.86% | 95.35% | 0.6284 | 0.4652 | 0.2586 |
| **XGBoost** | 48.04% | 47.90% | 93.02% | 0.6324 | 0.5016 | 0.2539 |
| **LSTM** | 52.94% | 53.49% | 27.71% | 0.3651 | 0.4812 | 0.2539 |
| **Ensemble** | 48.04% | 48.04% | 100.00% | 0.6491 | 0.4949 | 0.2696 |

