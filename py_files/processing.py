"""==========================================================================================
    
    File: processing.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:
        Contains the data preprocessing functions called in main.py.

    Dependencies:
        External:
            - numpy
        Internal:
            - None

    Special Concerns:
        - May move string normalization from pattern_match.py to this file for clarity
          and testing purposes.
=========================================================================================="""

import numpy as np


def convert_floats2ints(df):

    floats_df = df.select_dtypes(include="float64")

    # Find all whole numbers
    all_whole_numbers = np.all(floats_df.dropna == floats_df.dropna().astype(int))
    # Get columns of all whole numbers
    convertible_cols = [
        col
        for col in floats_df.columns
        if np.all(df[col].dropna() == all_whole_numbers)
    ]

    # Convert back to Invoice Data
    floats_df[convertible_cols].fillna(0).astype(int)

    df[convertible_cols] = floats_df[convertible_cols]
