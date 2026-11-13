from __future__ import annotations

import numpy as np
import pandas as pd


def transform(df: pd.DataFrame, test_size: float = 0.2) -> pd.DataFrame:
    """Split the iris dataset into deterministic 80/20 train/test partitions."""
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    out = df.copy()
    rng = np.random.RandomState(42)
    train_count = int(len(out) * (1 - test_size))
    indices = rng.permutation(len(out))
    train_idx = set(indices[:train_count].tolist())
    out["split"] = ["train" if i in train_idx else "test" for i in range(len(out))]
    return out
