import pandas as pd
import re as re

# Take in Excel (MAC)
itemized = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/Nautical 11-2024.xlsx",
    header=2,
    sheet_name=0,
)
invoice_data = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/Nautical 11-2024.xlsx",
    sheet_name=1,
)
qbo = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/QBO_customers.xlsx"
)
amt = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/Exensiv.xlsx",
    sheet_name="AMT",
)
gp_acoustics = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/Exensiv.xlsx",
    sheet_name="GPAcoustics",
)
whill = pd.read_excel(
    "/Users/danielsagher/Dropbox/Documents/projects/nautical_reconciliation/excel/Exensiv.xlsx",
    sheet_name="Whill",
)


invoice_data["Source"] = "Invoice Data"
qbo["Source"] = "QBO"
amt["Source"] = "AMT"
gp_acoustics["Source"] = "GP Acoustics"
whill["Source"] = "Whill"

df = pd.concat(objs=[invoice_data, qbo, amt, whill, gp_acoustics], join="outer")

# * Begin PowerBI

amt = df[df["CustomerIdentifier.Name"] == "AMT"].dropna(axis=1, how="all")
gp_acoustics = df[df["CustomerIdentifier.Name"] == "GP Acoustics"].dropna(
    axis=1, how="all"
)
qbo = df[df["Source"] == "QBO"].dropna(axis=1, how="all")
invoice_data = df[df["Source"] == "Invoice Data"].dropna(axis=1, how="all")
whill = df[df["Source"] == "Whill"].dropna(axis=1, how="all")


def compare_qbo(qbo: pd.DataFrame, invoice_data: pd.DataFrame) -> pd.DataFrame:
    """
    Function: Compares FedEx invoice with QuickBooks via keys 'Customer PO #' and 'Display_Name'
    Input: Original QuickBooks and FedEx Invoice file
    Output: Pandas DataFrame with values not found in QuickBooks
    """

    # ? is 'Display_Name' the only key to compare against?

    qbo_found = pd.merge(
        qbo,
        invoice_data,
        right_on="Customer PO #",
        left_on="Display_Name",
        how="inner",
        suffixes=["_qbo", "_invoice_data"],
    )

    lst = set()
    for i in invoice_data["Customer PO #"]:
        if i not in list(qbo_found["Display_Name"].unique()):
            lst.add(i)

    qbo_not_found = pd.DataFrame()
    qbo_not_found["Customer PO #"] = pd.DataFrame(lst)
    qbo_not_found = qbo_not_found.merge(
        invoice_data,
        on="Customer PO #",
        how="left",
    )
    return qbo_found, qbo_not_found


def add_pattern_column(invoice_data: pd.DataFrame) -> pd.DataFrame:
    """
    Function: Adds a column to the FedEx Invoice DataFrame with the RegEx pattern symbolizing 'Customer PO #'
    Input: FedEx Invoice DataFrame
    Output: DataFrame with added 'Pattern' column
    """

    def reg_tokenizer(value):

        with_letters = re.sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers = re.sub(r"\d+", r"\\d+", with_letters)
        with_spaces = re.sub(r"\s+", r"\\s+", with_numbers)

        final = re.compile(with_spaces)

        return final

    token_lst = []

    for i in invoice_data["Reference"]:
        token_lst.append(reg_tokenizer(i))

    invoice_data["Pattern"] = token_lst

    return invoice_data


def find_extensiv_reference_columns(extensiv_table: pd.DataFrame, invoice_data_w_patterns: pd.DataFrame) -> dict:  # fmt: skip
    """
    Function: Finds all of the columns in the Extensiv table that match each 'Reference' in FedEx Invoice not in QBO
    Input: Extensiv DataFrame, FedEx Invoice DataFrame w/ added 'Pattern' column
    Ouput: Dictionary {'match_lst': list of Extensiv columns that match 'Reference' pattern,
                       'Total Charges': Charges associated with that 'Reference' in FedEx Invoice,
                       'Tracking #': Tracking number associated with that 'Reference' in FedEx Invoice}
    Notes: May not need Total Charges and Tracking # in the end
    """

    def find_col_match(extensiv_table: pd.DataFrame, ref_pattern: pd.Series) -> list:
        """
        Function: Subfunction to iterate through each of the patterns in FedEx Invoice
        Input: Extensiv DataFrame, FedEx Reference patterns as a Series in a for loop
        Ouput: List of columns that match given Reference pattern
        """
        col_lst = set()

        for col in extensiv_table.columns:

            for value in extensiv_table[col]:

                if isinstance(value, float) and value.is_integer():

                    value = int(value)

                if re.fullmatch(ref_pattern, str(value)):

                    col_lst.add(col)
                    break

                else:
                    break

        if len(col_lst) != 0:
            return col_lst

    match_dct = dict()
    suffix = 0

    for i, v in enumerate(invoice_data_w_patterns["Reference"]):

        if i != 0 and v == invoice_data_w_patterns["Reference"][i - 1]:

            suffix += 1
            v = f"{v}-s{suffix}"

        elif i != 0 and v != invoice_data_w_patterns["Reference"][i - 1]:
            suffix = 0
        else:
            continue

        match_lst = find_col_match(
            extensiv_table, invoice_data_w_patterns["Pattern"][i]
        )

        if match_lst is not None and not pd.isna(v):

            match_dct[v] = {
                "match_lst": match_lst,
                "Total Charges": invoice_data_w_patterns["Total Charges"][i],
                "Tracking #": invoice_data_w_patterns["Tracking #"][i],
            }

    return match_dct


def find_value_match(extensiv_table: pd.DataFrame, reference_matches: dict) -> list:

    match_lst = list()

    for reference in reference_matches:

        matches = reference_matches[reference]["match_lst"]
        total_charges = reference_matches[reference]["Total Charges"]
        tracking_number = reference_matches[reference]["Tracking #"]

        for col in extensiv_table[list(matches)]:

            for i, val in enumerate(extensiv_table[col]):

                base_reference = re.sub(r"-s\d+$", "", str(reference))

                if val == reference or val == base_reference:

                    match_entry = {
                        "Reference": base_reference,
                        "Name": extensiv_table["CustomerIdentifier.Name"][i],
                        "Column": col,
                        "Total Charges": total_charges,
                        "Tracking #": tracking_number,
                    }

                    if match_entry not in match_lst:
                        match_lst.append(match_entry)

    return match_lst


def create_extensiv_receiver_info(extensiv_table: pd.DataFrame) -> dict:

    extensiv_receiver_info = extensiv_table[
        [
            "ShipTo.CompanyName",
            "ShipTo.Name",
            "ShipTo.Address1",
            "CustomerIdentifier.Name",
        ]
    ]

    extensiv_receiver_info_nd = extensiv_receiver_info.drop_duplicates(
        [
            "ShipTo.CompanyName",
            "ShipTo.Name",
            "ShipTo.Address1",
            "CustomerIdentifier.Name",
        ]
    )

    extensiv_receiver_dct = dict()

    for i, row in extensiv_receiver_info_nd.iterrows():

        extensiv_receiver_dct[i] = {
            "Receiver Address": row["ShipTo.Address1"],
            "Receiver Company": row["ShipTo.CompanyName"],
            "Receiver Name": row["ShipTo.Name"],
            "Customer Identifier": row["CustomerIdentifier.Name"],
        }

    return extensiv_receiver_dct


def create_invoice_data_receiver_info(invoice_data: pd.DataFrame) -> dict:  # fmt: skip

    invoice_data_dct = {}

    for i, row in invoice_data.iterrows():

        invoice_data_dct[i] = {
            "Receiver Address": row["Receiver Address"],
            "Receiver Company": row["Receiver Company"],
            "Receiver Name": row["Receiver Name"],
            "Tracking #": row["Tracking #"],
        }

    return invoice_data_dct

def compare_receiver_info(invoice_data_receiver_info: dict, extensiv_receiver_info: dict) -> list:  # fmt: skip

    match_entry = dict()
    match_lst = list()

    for i in invoice_data_receiver_info:

        for e in extensiv_receiver_info:

            if (
                invoice_data_receiver_info[i]["Receiver Address"]
                == extensiv_receiver_info[e]["Receiver Address"]
                or invoice_data_receiver_info[i]["Receiver Name"]
                == extensiv_receiver_info[e]["Receiver Name"]
                or invoice_data_receiver_info[i]["Receiver Company"]
                == extensiv_receiver_info[e]["Receiver Company"]
            ):

                match_entry = {
                    "Address": invoice_data_receiver_info[i]["Receiver Address"],
                    "Name": invoice_data_receiver_info[i]["Receiver Name"],
                    "Company": invoice_data_receiver_info[i]["Receiver Company"],
                    "Customer": extensiv_receiver_info[e]["Customer Identifier"],
                }

                if match_entry not in match_lst:
                    match_lst.append(match_entry)

    return match_lst


def make_final_df(reference_matches, receiver_matches, invoice_data_not_qbo):

    try:

        final_matches_lst = []
        final_matches_lst.extend(reference_matches)
        final_matches_lst.extend(receiver_matches)

        for i, row in invoice_data_not_qbo.iterrows():

            for dct in final_matches_lst:

                if "Reference" in dct and dct["Reference"] == row["Reference"]:
                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Name"]
                elif "Address" in dct and dct["Address"] == row["Receiver Address"]:
                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                elif "Name" in dct and dct["Name"] == row["Receiver Name"]:
                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                elif "Company" in dct and dct["Company"] == row["Receiver Company"]:
                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                elif "Reference" in dct:
                    try:
                        dct["Reference"] = int(dct["Reference"])
                    except ValueError:
                        pass
    except TypeError:
        pass

    return invoice_data_not_qbo


qbo_found, invoice_data_not_qbo = compare_qbo(qbo, invoice_data)
invoice_data_not_qbo = add_pattern_column(invoice_data)
gp_reference_columns = find_extensiv_reference_columns(
    gp_acoustics, invoice_data_not_qbo
)
amt_reference_columns = find_extensiv_reference_columns(amt, invoice_data_not_qbo)
whill_reference_columns = find_extensiv_reference_columns(whill, invoice_data_not_qbo)
gp_reference_matches = find_value_match(gp_acoustics, gp_reference_columns)
amt_reference_matches = find_value_match(amt, amt_reference_columns)
whill_reference_matches = find_value_match(whill, whill_reference_columns)
gp_receiver_info = create_extensiv_receiver_info(gp_acoustics)
amt_receiver_info = create_extensiv_receiver_info(amt)
whill_receiver_info = create_extensiv_receiver_info(whill)
invoice_data_receiver_info = create_invoice_data_receiver_info(invoice_data)
gp_receiver_matches = compare_receiver_info(
    invoice_data_receiver_info, gp_receiver_info
)
amt_receiver_matches = compare_receiver_info(
    invoice_data_receiver_info, amt_receiver_info
)
whill_receiver_matches = compare_receiver_info(
    invoice_data_receiver_info, whill_receiver_info
)
final_df = make_final_df(
    gp_reference_matches, gp_receiver_matches, invoice_data_not_qbo
)
final_df = make_final_df(
    amt_reference_matches, amt_receiver_matches, invoice_data_not_qbo
)
final_df = make_final_df(
    whill_reference_matches, whill_receiver_matches, invoice_data_not_qbo
)

del final_df["Pattern"]

print(final_df)
