import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, confusion_matrix
)

from backend.config import PROJECT_ROOT
from backend.features.feature_engine import FEATURE_COLUMNS
from backend.cache import model_cache

MODELS_DIR = os.path.join(PROJECT_ROOT, "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """Calculates comprehensive classification metrics & Brier calibration score."""
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.5

    brier = float(brier_score_loss(y_true, y_prob))
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "brier_score": brier,
        "confusion_matrix": cm
    }

class MajorityClassBaseline:
    """Baseline classifier predicting the most frequent class in training set."""
    def __init__(self):
        self.majority_class = 1

    def fit(self, X: np.ndarray, y: np.ndarray):
        counts = np.bincount(y.astype(int))
        self.majority_class = int(np.argmax(counts))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.majority_class)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        prob = np.zeros((len(X), 2))
        prob[:, self.majority_class] = 1.0
        return prob

class ModelPipeline:
    def __init__(self, model_name: str, symbol: str):
        self.model_name = model_name
        self.symbol = symbol
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        self.metrics = {}
        self.features_used = FEATURE_COLUMNS

    def _init_raw_model(self):
        if self.model_name == "LogisticRegression":
            base = LogisticRegression(max_iter=1000, random_state=42)
            return CalibratedClassifierCV(estimator=base, cv=3)
        elif self.model_name == "RandomForest":
            base = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42, class_weight="balanced")
            return CalibratedClassifierCV(estimator=base, cv=3)
        elif self.model_name == "XGBoost":
            base = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
            return CalibratedClassifierCV(estimator=base, cv=3)
        elif self.model_name == "MajorityBaseline":
            return MajorityClassBaseline()
        else:
            raise ValueError(f"Unknown model_name: {self.model_name}")

    def fit_custom(self, train_df: pd.DataFrame, feature_names: List[str]):
        """Fits model on arbitrary feature subset."""
        self.features_used = feature_names
        X_tr = train_df[feature_names].values
        y_tr = train_df["target"].values.astype(int)

        if self.model_name == "LogisticRegression":
            X_tr = self.scaler.fit_transform(X_tr)

        self.model = self._init_raw_model()
        self.model.fit(X_tr, y_tr)
        self.is_trained = True

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> Dict[str, Any]:
        """Trains model on chronological train_df, evaluates on val_df."""
        X_train = train_df[FEATURE_COLUMNS].values
        y_train = train_df["target"].values.astype(int)

        X_val = val_df[FEATURE_COLUMNS].values
        y_val = val_df["target"].values.astype(int)

        if self.model_name == "LogisticRegression":
            X_train = self.scaler.fit_transform(X_train)
            X_val = self.scaler.transform(X_val)

        self.model = self._init_raw_model()
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Validation evaluation
        val_probs = self.model.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= 0.5).astype(int)

        self.metrics = evaluate_predictions(y_val, val_preds, val_probs)
        self.save_model()

        return self.metrics


    def predict(self, df_features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (predicted_labels, proba_up)."""
        if not self.is_trained or self.model is None:
            raise RuntimeError(f"Model '{self.model_name}' for '{self.symbol}' is not trained.")

        cols = self.features_used if hasattr(self, "features_used") and self.features_used else FEATURE_COLUMNS
        X = df_features[cols].values
        if self.model_name == "LogisticRegression":
            X = self.scaler.transform(X)

        probs = self.model.predict_proba(X)[:, 1]
        preds = (probs >= 0.5).astype(int)
        return preds, probs

    def save_model(self, extra_meta: Optional[Dict[str, Any]] = None, custom_dir: Optional[str] = None):
        import json
        from datetime import datetime

        target_base = custom_dir if custom_dir else MODELS_DIR
        clean_symbol = self.symbol.upper().strip()
        asset_dir = os.path.join(target_base, clean_symbol)
        os.makedirs(asset_dir, exist_ok=True)

        filepath_flat = os.path.join(target_base, f"{clean_symbol}_{self.model_name}.joblib")
        filepath_nested = os.path.join(asset_dir, f"{self.model_name}.joblib")


        data = {
            "model_name": self.model_name,
            "symbol": clean_symbol,
            "model": self.model,
            "scaler": self.scaler,
            "metrics": self.metrics,
            "is_trained": self.is_trained,
            "features_used": self.features_used
        }
        joblib.dump(data, filepath_flat)
        joblib.dump(data, filepath_nested)

        meta_payload = {
            "symbol": clean_symbol,
            "model_name": self.model_name,
            "version": "1.0.0",
            "trained_at": datetime.utcnow().isoformat() + "Z",
            "features_used": self.features_used,
            "metrics": self.metrics,
            "disclaimer": "Educational & Research Purposes Only. Past performance does not guarantee future results."
        }
        if extra_meta:
            meta_payload.update(extra_meta)

        meta_path = os.path.join(asset_dir, f"{self.model_name}_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2)

        cache_key = f"model_{clean_symbol}_{self.model_name}"
        model_cache.set(cache_key, self)

    @classmethod
    def load_model(cls, symbol: str, model_name: str) -> Optional["ModelPipeline"]:
        clean_symbol = symbol.upper().strip()
        cache_key = f"model_{clean_symbol}_{model_name}"
        cached_model = model_cache.get(cache_key)


        if cached_model is not None:
            return cached_model

        filepath_flat = os.path.join(MODELS_DIR, f"{clean_symbol}_{model_name}.joblib")
        filepath_nested = os.path.join(MODELS_DIR, clean_symbol, f"{model_name}.joblib")

        filepath = None
        if os.path.exists(filepath_flat):
            filepath = filepath_flat
        elif os.path.exists(filepath_nested):
            filepath = filepath_nested

        if not filepath:
            return None

        try:
            data = joblib.load(filepath)
            pipe = cls(model_name=data["model_name"], symbol=data["symbol"])
            pipe.model = data["model"]
            pipe.scaler = data["scaler"]
            pipe.metrics = data["metrics"]
            pipe.is_trained = data["is_trained"]
            pipe.features_used = data["features_used"]
            model_cache.set(cache_key, pipe)
            return pipe
        except Exception as e:
            print(f"Error loading model from {filepath}: {e}")
            return None

