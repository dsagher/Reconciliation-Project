import pandas as pd
import re as re

# * Invoice_Data <-> QBO

##* Compare invoice_data['Customer PO #'] to qbo['Display_Name']


def compare_qbo(qbo: pd.DataFrame, invoice_data: pd.DataFrame) -> pd.DataFrame:
    """
    Function: Compares FedEx invoice with QuickBooks via keys 'Customer PO #' and 'Display_Name'
    Input: Original QuickBooks and FedEx Invoice file
    Output: Pandas DataFrame with values not found in QuickBooks
    """

    # ? is 'Display_Name' the only key to compare against?

    qbo_found = pd.merge(
        qbo, invoice_data, right_on="Customer PO #", left_on="Display_Name", how="inner"
    )

    lst = set()
    for i in invoice_data["Customer PO #"]:
        if i not in list(qbo_found["Display_Name"].unique()):
            lst.add(i)

    not_found = pd.DataFrame()
    not_found["Customer PO #"] = pd.DataFrame(lst)
    not_found = not_found.merge(
        invoice_data[
            [
                "Customer PO #",
                "Reference",
                "Reference 2",
                "Total Charges",
                "Receiver Name",
                "Receiver Company",
                "Receiver Address",
                "Tracking #",
            ]
        ],
        on="Customer PO #",
        how="left",
    )
    return not_found


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

                if re.fullmatch(ref_pattern, str(value)):

                    col_lst.add(col)
                    break

                else:
                    break

        if len(col_lst) != 0:
            return col_lst
        else:
            return None

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
                else:
                    continue

    if not match_lst:
        print(f"No Matches")

    else:
        return match_lst


def create_invoice_data_receiver_info(invoice_data: pd.DataFrame, reference_matches: list) -> dict:  # fmt: skip

    found_reference_lst = list()

    for i in reference_matches:
        found_reference_lst.append(i["Reference"])

    #! Taking out this conditional to test
    invoice_data_null = invoice_data[
        (invoice_data["Customer PO #"].isna())
        & ~(invoice_data["Reference"].isin(found_reference_lst))
    ]

    invoice_data_dct = {}

    for i, row in invoice_data.iterrows():

        invoice_data_dct[i] = {
            "Receiver Address": row["Receiver Address"],
            "Receiver Company": row["Receiver Company"],
            "Receiver Name": row["Receiver Name"],
            "Tracking #": row["Tracking #"],
        }

    return invoice_data_dct


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

    if match_lst:
        return match_lst
    else:
        print("No Match")


if __name__ == "__main__":
    pass

    # not_found = compare_qbo(qbo, invoice_data)
    # not_found_patterns = add_pattern_column(not_found)
    # gp_reference_matches = find_extensiv_reference_columns(
    #     gp_acoustics, not_found_patterns
    # )
    # gp_found_values = find_value_match(gp_acoustics, gp_reference_matches)
    # invoice_data_receiver_info = create_invoice_data_receiver_info(
    #     not_found_patterns, gp_found_values
    # )
    # gp_receiver_info = create_extensiv_receiver_info(gp_acoustics)
    # print(compare_receiver_info(invoice_data_receiver_info, gp_receiver_info))
