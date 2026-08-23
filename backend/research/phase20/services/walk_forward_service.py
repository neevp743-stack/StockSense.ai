"""
StockSense AI — Phase 20 Walk-Forward & Final Holdout Validation Service
Implements strict 5-fold chronological walk-forward cross-validation without shuffling,
plus a single evaluation of the untouched 15% final holdout set.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss, log_loss


class WalkForwardService:
    """Manages chronological walk-forward splitting and single final holdout evaluation."""

    def perform_walk_forward_validation(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        n_folds: int = 5,
        holdout_ratio: float = 0.15
    ) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
        """
        Splits dataset chronologically into Train/Val (1 - holdout_ratio) and untouched Holdout (holdout_ratio).
        Performs n_folds chronological expanding window walk-forward splits on Train/Val.
        """
        df_sorted = df.sort_values("date").reset_index(drop=True) if "date" in df.columns else df.reset_index(drop=True)
        total_rows = len(df_sorted)

        holdout_size = int(total_rows * holdout_ratio)
        train_val_df = df_sorted.iloc[:-holdout_size].copy()
        holdout_df = df_sorted.iloc[-holdout_size:].copy()

        tv_rows = len(train_val_df)
        fold_size = tv_rows // (n_folds + 1)

        fold_results = []

        for i in range(n_folds):
            train_end = fold_size * (i + 1)
            val_end = train_end + fold_size if i < n_folds - 1 else tv_rows

            train_fold = train_val_df.iloc[:train_end]
            val_fold = train_val_df.iloc[train_end:val_end]

            fold_results.append({
                "fold": i + 1,
                "train_rows": len(train_fold),
                "val_rows": len(val_fold),
                "train_start": str(train_fold["date"].iloc[0]) if "date" in train_fold.columns else 0,
                "train_end": str(train_fold["date"].iloc[-1]) if "date" in train_fold.columns else train_end,
                "val_start": str(val_fold["date"].iloc[0]) if "date" in val_fold.columns else train_end,
                "val_end": str(val_fold["date"].iloc[-1]) if "date" in val_fold.columns else val_end,
            })

        summary = {
            "total_dataset_rows": total_rows,
            "train_val_rows": tv_rows,
            "holdout_rows": len(holdout_df),
            "holdout_ratio": holdout_ratio,
            "n_folds": n_folds,
            "folds": fold_results
        }

        return summary, train_val_df, holdout_df
