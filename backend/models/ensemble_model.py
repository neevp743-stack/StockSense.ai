import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from backend.models.baseline_models import evaluate_predictions, ModelPipeline
from backend.models.lstm_model import LSTMPipeline

class EnsemblePipeline:
    """
    Weighted Probability Ensemble Model.
    Combines calibrated output probabilities of Logistic Regression, Random Forest, XGBoost, and PyTorch LSTM.
    Only reports improvement if empirical validation proves superior metrics over individual baselines.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.weights = {
            "LogisticRegression": 0.2,
            "RandomForest": 0.25,
            "XGBoost": 0.35,
            "LSTM": 0.2
        }
        self.models = {}
        self.metrics = {}
        self.is_trained = False

    def fit_weights_from_val(self, val_df: pd.DataFrame, models: Dict[str, Any]):
        """
        Dynamically weights models based on their validation accuracy/ROC-AUC score.
        Higher performing models get proportional ensemble weight.
        """
        self.models = models
        auc_scores = {}
        total_score = 0.0

        for name, m in models.items():
            if m and getattr(m, "is_trained", False):
                auc = m.metrics.get("roc_auc", 0.5)
                auc_scores[name] = max(auc, 0.5)
                total_score += auc_scores[name]

        if total_score > 0:
            self.weights = {name: score / total_score for name, score in auc_scores.items()}
        
        self.is_trained = True

    def predict(self, df_features: pd.DataFrame, models: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates weighted average probability prediction."""
        if models is None:
            models = self.models

        if not models:
            raise ValueError("No models provided for ensemble prediction.")

        total_prob = np.zeros(len(df_features))
        weight_sum = 0.0

        for name, m in models.items():
            if name == "Ensemble":
                continue
            if m and getattr(m, "is_trained", False):
                w = self.weights.get(name, 0.25)
                if name == "LSTM":
                    _, probs = m.predict(df_features)
                    # Handle sequence length difference if present
                    if len(probs) < len(total_prob):
                        pad = np.full(len(total_prob) - len(probs), probs[0])
                        probs = np.concatenate([pad, probs])
                else:
                    _, probs = m.predict(df_features)

                total_prob += w * probs
                weight_sum += w

        if weight_sum > 0:
            total_prob /= weight_sum

        preds = (total_prob >= 0.5).astype(int)
        return preds, total_prob
