"""Framework-independent training logic for the Iris pipeline."""

from typing import Any, Dict

import pandas as pd
from sklearn.tree import DecisionTreeClassifier


def train_model(df: pd.DataFrame, max_depth: int = 3) -> Dict[str, Any]:
    """Fit a deterministic decision tree and return test predictions."""
    if not isinstance(max_depth, int) or max_depth < 1:
        raise ValueError("max_depth must be a positive integer")
    if "split" not in df.columns or "target" not in df.columns:
        raise ValueError("DataFrame must contain 'split' and 'target' columns")

    feature_columns = [column for column in df.columns if column not in {"split", "target"}]
    if not feature_columns:
        raise ValueError("DataFrame must contain at least one feature column")

    train_mask = df["split"] == "train"
    test_mask = df["split"] == "test"
    if not train_mask.any() or not test_mask.any():
        raise ValueError("DataFrame must contain both train and test rows")

    model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    model.fit(df.loc[train_mask, feature_columns], df.loc[train_mask, "target"])
    y_true = df.loc[test_mask, "target"].reset_index(drop=True)
    y_pred = pd.Series(
        model.predict(df.loc[test_mask, feature_columns]),
        name="prediction",
    )
    accuracy = float((y_true.to_numpy() == y_pred.to_numpy()).mean())

    return {
        "model": model,
        "feature_columns": feature_columns,
        "y_true": y_true,
        "y_pred": y_pred,
        "test_accuracy": accuracy,
        "max_depth": max_depth,
    }
