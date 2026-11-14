import pandas as pd
from sklearn.datasets import load_iris as sklearn_load_iris

if 'data_loader' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_loader
    except ImportError:
        def data_loader(func):
            return func
if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@data_loader
def load_iris(**kwargs):
    """Load the built-in Iris dataset."""
    return sklearn_load_iris(as_frame=True).frame.copy()


@test
def test_output(df):
    """Verify the Iris dataset has 150 rows and three classes."""
    assert df is not None
    assert len(df) == 150
    assert "target" in df.columns
    assert df["target"].nunique() == 3
    assert not df.isnull().any().any()
