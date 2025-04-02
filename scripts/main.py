"""==========================================================================================

    Title:       Nautical_Reconciliation
    File:        main.py
    Author:      Dan Sagher
    Date:        12/25/24
    Description:
        This tool reconciles invoice data from FedEx with QuickBooks Online (QBO) data and customer 
        information stored in Extensiv tables. It simplifies the comparison and matching process to 
        identify discrepancies and generate a consolidated output file.

    Workflow:
        1. Input: Accepts Excel or CSV files from a user-defined path.
        2. QuickBooks Comparison: Compares invoice values against QBO to validate Customer PO #s.
        3. Extensiv Lookup (Part 1): Searches for unmatched records in Extensiv using fields 
           from the FedEx invoice (e.g., [Reference], [Reference 2]).
        4. Extensiv Lookup (Part 2): If still unmatched, searches using receiver details 
           from FedEx (e.g., [Receiver Name], [Receiver Address], [Receiver Company]).
        5. Reconciliation: Updates the [Customer PO #] with the corresponding customer name.
        6. Output: Exports a reconciled Excel file with the matched values.

    Dependencies:
        External:
            - pandas
            - tqdm
            - functools
        Internal:
            - pattern_match
            - processing
            - file_io

#=========================================================================================="""

from pandas import DataFrame
from tqdm import tqdm
from functools import partial

from pattern_match import FindCustomerPO, FindPatternMatches, make_final_df
from processing import convert_floats2ints
from file_io import FileIO

def main(fedex_invoice: DataFrame, qbo: DataFrame, customer_dct: dict[str,DataFrame] ) -> DataFrame: 
    """
    Calls input, preprocessing, pattern matching, and output classes, methods, and functions.

    Parameters:
        - fedex_invoice: Pandas DataFrame of FedEx invoice
        - qbo: Pandas DataFrame of Quickbooks customer information
        - customer_dct: Dictionary containing {customer_name: Pandas DataFrame}

    Returns:
        - final_df: New FedEx invoice DataFrame containing replaced [Customer PO #] with customer_name
        - qbo_found: New FedEx invoice DataFrame containing only records with [Customer PO #] found in Quickbooks.
    """

    print("Pre-Processing")

    convert_floats2ints(fedex_invoice)
    convert_floats2ints(qbo)
    for df in customer_dct.values():
        convert_floats2ints(df)

    print("Comparing FedEx Invoice to QBO")

    FEDEX_KEY: str = "Customer PO #"
    REFERENCE_LST: list = ["Reference", "Reference 2"]
    QBO_KEY_LST: list = ["Fully_Qualified_Name", "Display_Name"]

    qbo_pattern_match = FindCustomerPO(qbo, fedex_invoice)
    qbo_found, qbo_not_found = qbo_pattern_match.compare_qbo(QBO_KEY_LST, FEDEX_KEY)

    print("Searching through Extensiv tables for reference and receiver info matches")

    reference_matches = list()
    receiver_matches = list()

    # Loop through customer Extensiv tables
    for customer, dataframe in tqdm(customer_dct.items(), smoothing=0.5):

        PartialFindPatternMatches = partial(FindPatternMatches, fedex_invoice=qbo_not_found)

        customer_pattern_match = PartialFindPatternMatches(customer, dataframe)

        reference_matches.extend(customer_pattern_match.compare_references(REFERENCE_LST))

        receiver_matches.extend(customer_pattern_match.compare_receiver_info())

        print(customer_pattern_match)

    final_df = make_final_df(reference_matches, receiver_matches, qbo_not_found)

    return final_df, qbo_found


if __name__ == "__main__":

    path = input("File Path (or press Enter for current directory): ")
    io = FileIO(path)
    fedex_invoice, qbo, customer_dct = io.get_input()
    final_df, qbo_found = main(fedex_invoice, qbo, customer_dct)
    io.output(final_df, qbo_found)
    print("Finished")
