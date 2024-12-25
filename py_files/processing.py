import pandas as pd
import numpy as np

pd.set_option("display.max_columns", 500)


itemized = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/invoice_data.xlsx",
    header=2,
    sheet_name=0,
)
invoice_data = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/invoice_data.xlsx",
    sheet_name=1,
)
qbo = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/QBO_customers.xlsx"
)
amt = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/Exensiv.xlsx",
    sheet_name="AMT",
)
gp_acoustics = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/Exensiv.xlsx",
    sheet_name="GPAcoustics",
)
whill = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel_files/Exensiv.xlsx",
    sheet_name="Whill",
)


# Read CSV from Windows Comp


def read_windows():

    itemized = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/Invoice_data.xlsx",
        header=2,
        sheet_name=0,
    )
    invoice_data = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/Invoice_data.xlsx",
        sheet_name=1,
    )
    qbo = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/QBO_customers(1).xlsx"
    )
    amt = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/Exensiv.xlsx",
        sheet_name="AMT",
    )
    gp_acoustics = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/Exensiv.xlsx",
        sheet_name="GPAcoustics",
    )
    whill = pd.read_excel(
        "C:/Users/danie/OneDrive/Projects/fedex_reconciliation/Excel/Exensiv.xlsx",
        sheet_name="Whill",
    )

    return itemized, invoice_data, qbo, amt, gp_acoustics, whill


# itemized, invoice_data, qbo, amt, gp_acoustics, whill = read_windows()


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


# convert_floats2ints(invoice_data)
# convert_floats2ints(gp_acoustics)
# convert_floats2ints(whill)
# convert_floats2ints(amt)
# convert_floats2ints(qbo)
