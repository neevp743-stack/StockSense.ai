import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from backend.config import TRAIN_RATIO, VAL_RATIO, TEST_RATIO

def chronological_split(
    df: pd.DataFrame, 
    train_ratio: float = TRAIN_RATIO, 
    val_ratio: float = VAL_RATIO, 
    test_ratio: float = TEST_RATIO
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame strictly chronologically without random shuffling.
    70% Train, 15% Validation, 15% Test.
    """
    if df is None or df.empty:
        raise ValueError("Cannot split empty DataFrame.")

    df_sorted = df.sort_values("date").reset_index(drop=True)
    n = len(df_sorted)

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_df = df_sorted.iloc[:n_train].copy()
    val_df = df_sorted.iloc[n_train : n_train + n_val].copy()
    test_df = df_sorted.iloc[n_train + n_val :].copy()

    return train_df, val_df, test_df

class WalkForwardSplitter:
    """
    Walk-forward (expanding window) time-series cross-validator.
    Ensures zero future data leakage across validation folds.
    """
    def __init__(self, min_train_size: int = 250, val_size: int = 50, step_size: int = 50):
        self.min_train_size = min_train_size
        self.val_size = val_size
        self.step_size = step_size

    def split(self, df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        folds = []
        n = len(df)
        df_sorted = df.sort_values("date").reset_index(drop=True)

        current_idx = self.min_train_size
        while current_idx + self.val_size <= n:
            train_fold = df_sorted.iloc[:current_idx].copy()
            val_fold = df_sorted.iloc[current_idx : current_idx + self.val_size].copy()
            folds.append((train_fold, val_fold))
            current_idx += self.step_size

        return folds
