"""Framework-independent prediction export logic for the Iris pipeline."""

from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd


def save_results(
    training_result: Dict[str, Any],
    output_path: Union[str, Path] = "iris_predictions.csv",
) -> Path:
    """Write actual and predicted labels to CSV and return its path."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    predictions = pd.DataFrame(
        {
            "actual": training_result["y_true"].to_numpy(),
            "predicted": training_result["y_pred"].to_numpy(),
        }
    )
    predictions.to_csv(output, index=False)
    return output
