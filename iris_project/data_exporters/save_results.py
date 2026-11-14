from pathlib import Path

if 'data_exporter' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(func):
            return func
if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@data_exporter
def save_results(training_result, **kwargs):
    output_path = Path("iris_predictions.csv")

    import pandas as pd

    predictions = pd.DataFrame({
        "actual": training_result["y_true"],
        "predicted": training_result["y_pred"],
    })

    predictions.to_csv(output_path, index=False)
    return str(output_path.resolve())


@test
def test_output(output):
    assert output is not None
    assert Path(output).exists()
