"""Framework-independent data checks for the Iris pipeline."""

import pandas as pd


def validate_iris_data(df: pd.DataFrame) -> pd.DataFrame:
    """Check that the dataset has no missing values and exactly three classes."""
    if df.isnull().any().any():
        raise ValueError("Iris input contains missing values")
    if "target" not in df.columns:
        raise ValueError("Iris input must contain a 'target' column")
    if df["target"].nunique() != 3:
        raise ValueError("Iris input must contain exactly three target classes")
    return df
