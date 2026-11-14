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


def validate_iris_data(df):
    """Validate the Iris dataset."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    if df.isnull().any().any():
        raise ValueError("Iris dataset contains missing values")
    if "target" not in df.columns:
        raise ValueError("Missing target column")
    if df["target"].nunique() != 3:
        raise ValueError("Expected exactly three target classes")
    return df


@transformer
def validate_data(df, **kwargs):
    return validate_iris_data(df)


@test
def test_output(df):
    assert len(df) == 150
    assert "target" in df.columns
    assert df["target"].nunique() == 3
    assert not df.isnull().any().any()
