import pandas as pd
import pytest

from iris_project.data import load_iris_frame
from iris_project.exporters.save_results import save_results
from iris_project.transformers.evaluate_model import evaluate_model
from iris_project.transformers.prepare_data import transform
from iris_project.transformers.train_model import train_model
from iris_project.transformers.validate_data import validate_iris_data


def test_validate_iris_data_accepts_iris_and_rejects_missing_values():
    df = load_iris_frame()
    assert validate_iris_data(df) is df

    invalid = df.copy()
    invalid.loc[0, invalid.columns[0]] = float("nan")
    with pytest.raises(ValueError, match="missing values"):
        validate_iris_data(invalid)


def test_validate_iris_data_requires_three_classes():
    df = load_iris_frame()
    invalid = df[df["target"] != 2]
    with pytest.raises(ValueError, match="exactly three"):
        validate_iris_data(invalid)


def test_train_evaluate_and_save_results(tmp_path):
    df = transform(load_iris_frame())
    training = train_model(df, max_depth=3)
    evaluation = evaluate_model(training)

    assert len(training["y_true"]) == 30
    assert len(training["y_pred"]) == 30
    assert 0.0 <= training["test_accuracy"] <= 1.0
    assert sum(sum(row) for row in evaluation["confusion_matrix"]) == 30
    assert set(evaluation["metrics"]) == {
        "accuracy",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
    }

    output_path = save_results(training, tmp_path / "iris_predictions.csv")
    predictions = pd.read_csv(output_path)
    assert len(predictions) == 30
    assert list(predictions.columns) == ["actual", "predicted"]


def test_train_model_rejects_invalid_max_depth():
    df = transform(load_iris_frame())
    with pytest.raises(ValueError, match="positive integer"):
        train_model(df, max_depth=0)

