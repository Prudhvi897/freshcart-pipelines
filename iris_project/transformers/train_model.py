from typing import Any, Dict

import pandas as pd
from sklearn.tree import DecisionTreeClassifier

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


def train_model_impl(df: pd.DataFrame, max_depth: int = 3) -> Dict[str, Any]:
    if not isinstance(max_depth, int) or max_depth < 1:
        raise ValueError("max_depth must be a positive integer")

    if "split" not in df.columns or "target" not in df.columns:
        raise ValueError("DataFrame must contain split and target columns")

    feature_columns = [
        c for c in df.columns if c not in {"split", "target"}
    ]

    train_df = df[df["split"] == "train"]
    test_df = df[df["split"] == "test"]

    if train_df.empty or test_df.empty:
        raise ValueError("Both train and test sets must contain rows")

    model = DecisionTreeClassifier(
        max_depth=max_depth,
        random_state=42
    )
    model.fit(train_df[feature_columns], train_df["target"])

    y_true = test_df["target"].to_numpy()
    y_pred = model.predict(test_df[feature_columns])
    accuracy = float((y_true == y_pred).mean())

    return {
        "model": model,
        "feature_columns": feature_columns,
        "y_true": y_true.tolist(),
        "y_pred": y_pred.tolist(),
        "test_accuracy": accuracy,
        "max_depth": max_depth,
    }


@transformer
def train_model(df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    runtime_vars = kwargs.get("runtime_vars", {}) or {}
    max_depth = int(runtime_vars.get("max_depth", 3))
    return train_model_impl(df, max_depth=max_depth)


@test
def test_output(result):
    assert isinstance(result, dict)
    assert 0.0 <= result["test_accuracy"] <= 1.0
    assert len(result["y_true"]) == len(result["y_pred"])
    assert result["max_depth"] in range(1, 6)


