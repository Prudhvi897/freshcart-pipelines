"""Framework-independent evaluation logic for the Iris pipeline."""

from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def evaluate_model(training_result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a confusion matrix and a compact classification metrics table."""
    y_true = training_result["y_true"]
    y_pred = training_result["y_pred"]
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
    }
    return {
        "labels": labels,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels),
        "metrics": metrics,
    }
