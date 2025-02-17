"""==========================================================================================
    File:       processing.py
    Author:     Dan Sagher
    Date:       12/25/24
    Description:
        Contains data preprocessing functions for converting floating point numbers to integers
        when appropriate. Used to standardize numeric data types across different input sources.

    Dependencies:
        External:
            - numpy
            - pandas
        Internal:
            - None
=========================================================================================="""

import numpy as np
import pandas as pd


def convert_floats2ints(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts float columns to integers where all non-null values are whole numbers.

    Parameters:
        - df: Input DataFrame containing columns to be processed

    Returns:
        - df: DataFrame with appropriate float columns converted to integers
    """
    df = df.copy()

    float_cols = df.select_dtypes(include="float64")

    if float_cols.empty:
        return df

    convertible_cols = []
    for col in float_cols.columns:
        non_null_values = df[col].dropna()
        if non_null_values.empty:
            continue
        if np.all(non_null_values == non_null_values.astype(int)):
            convertible_cols.append(col)

    if convertible_cols:
        df[convertible_cols] = df[convertible_cols].apply(
            lambda x: x.astype("Int64") if not x.isna().all() else x
        )

    return df
