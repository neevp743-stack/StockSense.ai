import os
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, Any, Tuple, Optional

from sklearn.preprocessing import StandardScaler
from backend.config import PROJECT_ROOT, LSTM_SEQUENCE_LENGTH
from backend.features.feature_engine import FEATURE_COLUMNS
from backend.models.baseline_models import evaluate_predictions, MODELS_DIR

class SequenceDataset(Dataset):
    """
    Constructs chronological time-series sequences of length `seq_len`.
    Features for sequence ending at index t predict target at t.
    Zero cross-contamination between train/test splits.
    """
    def __init__(self, X: np.ndarray, y: np.ndarray, seq_len: int = LSTM_SEQUENCE_LENGTH):
        self.seq_len = seq_len
        self.X_seq = []
        self.y_seq = []

        if len(X) >= seq_len:
            for i in range(len(X) - seq_len + 1):
                self.X_seq.append(X[i : i + seq_len])
                self.y_seq.append(y[i + seq_len - 1])

        self.X_seq = torch.tensor(np.array(self.X_seq), dtype=torch.float32) if len(self.X_seq) > 0 else torch.empty((0, seq_len, X.shape[1]))
        self.y_seq = torch.tensor(np.array(self.y_seq), dtype=torch.float32) if len(self.y_seq) > 0 else torch.empty((0,))

    def __len__(self):
        return len(self.X_seq)

    def __getitem__(self, idx):
        return self.X_seq[idx], self.y_seq[idx]

class PyTorchLSTM(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 2, dropout: float = 0.2):
        super(PyTorchLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]
        prob = self.fc(last_step)
        return prob.squeeze(-1)

class LSTMPipeline:
    def __init__(self, symbol: str, seq_len: int = LSTM_SEQUENCE_LENGTH):
        self.symbol = symbol
        self.seq_len = seq_len
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        self.metrics = {}

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame, epochs: int = 30, lr: float = 0.001) -> Dict[str, Any]:
        """Trains PyTorch LSTM on chronological sequences."""
        X_train_raw = train_df[FEATURE_COLUMNS].values
        y_train_raw = train_df["target"].values.astype(float)

        X_val_raw = val_df[FEATURE_COLUMNS].values
        y_val_raw = val_df["target"].values.astype(float)

        # Fit scaler on train set ONLY
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_val_scaled = self.scaler.transform(X_val_raw)

        train_ds = SequenceDataset(X_train_scaled, y_train_raw, self.seq_len)
        val_ds = SequenceDataset(X_val_scaled, y_val_raw, self.seq_len)

        if len(train_ds) == 0 or len(val_ds) == 0:
            raise ValueError(f"Insufficient data to build LSTM sequences of length {self.seq_len}.")

        train_loader = DataLoader(train_ds, batch_size=32, shuffle=False)

        input_dim = len(FEATURE_COLUMNS)
        self.model = PyTorchLSTM(input_dim=input_dim)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)

        self.model.train()
        for epoch in range(epochs):
            for X_b, y_b in train_loader:
                optimizer.zero_grad()
                preds = self.model(X_b)
                loss = criterion(preds, y_b)
                loss.backward()
                optimizer.step()

        # Validation evaluation
        self.model.eval()
        with torch.no_grad():
            X_val_tensor = val_ds.X_seq
            y_val_actual = val_ds.y_seq.numpy().astype(int)
            val_probs = self.model(X_val_tensor).numpy()
            val_preds = (val_probs >= 0.5).astype(int)

        self.metrics = evaluate_predictions(y_val_actual, val_preds, val_probs)
        self.is_trained = True
        self.save_model()
        return self.metrics

    def predict(self, df_features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Generates sequence predictions for feature DataFrame."""
        if not self.is_trained or self.model is None:
            raise RuntimeError(f"LSTM model for '{self.symbol}' is not trained.")

        X_raw = df_features[FEATURE_COLUMNS].values
        X_scaled = self.scaler.transform(X_raw)

        if len(X_scaled) < self.seq_len:
            # Pad early rows if needed
            pad_len = self.seq_len - len(X_scaled)
            pad_matrix = np.tile(X_scaled[0], (pad_len, 1))
            X_scaled = np.vstack([pad_matrix, X_scaled])

        ds = SequenceDataset(X_scaled, np.zeros(len(X_scaled)), self.seq_len)
        self.model.eval()
        with torch.no_grad():
            probs = self.model(ds.X_seq).numpy()
            preds = (probs >= 0.5).astype(int)

        return preds, probs

    def save_model(self):
        filepath = os.path.join(MODELS_DIR, f"{self.symbol}_LSTM.pt")
        meta_path = os.path.join(MODELS_DIR, f"{self.symbol}_LSTM.joblib")
        torch.save(self.model.state_dict(), filepath)
        meta = {
            "symbol": self.symbol,
            "seq_len": self.seq_len,
            "scaler": self.scaler,
            "metrics": self.metrics,
            "is_trained": self.is_trained
        }
        joblib.dump(meta, meta_path)

    @classmethod
    def load_model(cls, symbol: str) -> Optional["LSTMPipeline"]:
        filepath = os.path.join(MODELS_DIR, f"{symbol}_LSTM.pt")
        meta_path = os.path.join(MODELS_DIR, f"{symbol}_LSTM.joblib")
        if not os.path.exists(filepath) or not os.path.exists(meta_path):
            return None

        meta = joblib.load(meta_path)
        pipe = cls(symbol=symbol, seq_len=meta["seq_len"])
        pipe.scaler = meta["scaler"]
        pipe.metrics = meta["metrics"]
        pipe.is_trained = meta["is_trained"]

        input_dim = len(FEATURE_COLUMNS)
        pipe.model = PyTorchLSTM(input_dim=input_dim)
        pipe.model.load_state_dict(torch.load(filepath))
        pipe.model.eval()
        return pipe
