from __future__ import annotations

import numpy as np
import pandas as pd

if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func
if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


def transform(df: pd.DataFrame, test_size: float = 0.2) -> pd.DataFrame:
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    out = df.copy()
    rng = np.random.RandomState(42)
    train_count = int(len(out) * (1 - test_size))
    indices = rng.permutation(len(out))
    train_idx = set(indices[:train_count].tolist())

    out["split"] = [
        "train" if i in train_idx else "test"
        for i in range(len(out))
    ]
    return out


@transformer
def prepare_data(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    return transform(df, test_size=0.2)


@test
def test_output(df):
    assert len(df) == 150
    assert "split" in df.columns
    assert (df["split"] == "train").sum() == 120
    assert (df["split"] == "test").sum() == 30
