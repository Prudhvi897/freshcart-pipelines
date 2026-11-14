import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

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


def evaluate_model_impl(training_result):
    y_true = training_result["y_true"]
    y_pred = training_result["y_pred"]

    labels = sorted(set(y_true) | set(y_pred))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    return {
        "labels": labels,
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=labels
        ).tolist(),
        "metrics": {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_weighted": float(precision),
            "recall_weighted": float(recall),
            "f1_weighted": float(f1),
        },
    }


@transformer
def evaluate_model(training_result, **kwargs):
    return evaluate_model_impl(training_result)


@test
def test_output(result):
    assert len(result["confusion_matrix"]) == 3
    assert len(result["confusion_matrix"][0]) == 3
    assert all(
        0.0 <= value <= 1.0
        for value in result["metrics"].values()
    )


