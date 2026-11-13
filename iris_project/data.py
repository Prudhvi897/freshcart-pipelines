"""Dataset loading helpers for the Iris example."""

from sklearn.datasets import load_iris
import pandas as pd


def load_iris_frame() -> pd.DataFrame:
    """Return the Iris dataset as a pandas DataFrame, including its target."""
    return load_iris(as_frame=True).frame.copy()
