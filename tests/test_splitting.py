import pytest
import pandas as pd
from backend.models.splitter import chronological_split, WalkForwardSplitter

def test_chronological_split_ratios():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "val": range(100)})
    
    train_df, val_df, test_df = chronological_split(df, 0.70, 0.15, 0.15)
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Check chronological ordering
    assert train_df["date"].max() < val_df["date"].min()
    assert val_df["date"].max() < test_df["date"].min()

def test_walk_forward_splitter():
    dates = pd.date_range("2024-01-01", periods=350, freq="D")
    df = pd.DataFrame({"date": dates, "val": range(350)})
    
    wf = WalkForwardSplitter(min_train_size=200, val_size=50, step_size=50)
    folds = wf.split(df)
    assert len(folds) >= 2

    for train_fold, val_fold in folds:
        assert train_fold["date"].max() < val_fold["date"].min()
