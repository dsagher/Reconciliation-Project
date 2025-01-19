"""==========================================================================================

    Title:       <Nautical_Reconciliation>
    File: 
    Author:      <Dan Sagher>
    Date:        <12/25/24>
    Description:

    <This tool reconciles missing or incorrect [Customer PO #] values from a FedEx invoice>

    1. Values are first compared against Quickbooks to determine which Customer PO #'s 
    are correct.
    2. Remaining values are searched through columns of individual Extensiv tables 
    via the FedEx invoice [Reference].
    3. Remaining values are searched via Receiver information - [Receiver Name],
    [Receiver Address],[Receiver Company].
    4. Found values have their [Customer PO #] replaced with the name of the customer. 

    Dependencies:
    External:
        - pandas
        - tqdm
        - os
    Internal:
        - pattern_match (for pattern matching logic)
        - processing (for data preprocessing)
        - file_io (for input and output handling)

    Special Concerns: 
    - References are matched based on strict equalities, case insensitve.
    This may result in missed values. Receiver matches are matched based on normalized strings.
    - Fuzzy matching will be implemented to account for user input error (i.e. Main st vs. Main Street)
    - Functionality will be added to search through [Reference 2]
    - PatternMatch class will be broken up into smaller subclasses to avoid confusion.

#=========================================================================================="""

import pattern_match as pm
from processing import convert_floats2ints
from file_io import get_input, output

import os
import pandas as pd
from tqdm import tqdm

def main(invoice_data: pd.DataFrame, qbo: pd.DataFrame, customer_dct: dict[str,pd.DataFrame] ) -> pd.DataFrame:  # fmt: skip
    """
    main() function calls the preprocessing and pattern matching logic classes and methods.

    :param invoice_data: Pandas DataFrame of FedEx invoice
    :param qbo: Pandas DataFrame of Quickbooks customer information
    :param customer_dct: Dictionary containing {customer_name: Pandas DataFrame}
    :return final_df: New FedEx invoice DataFrame containing replaced [Customer PO #] with customer_name
    :return qbo_found: New FedEx invoice DataFrame containing only records with [Customer PO #] found in Quickbooks.
    """

    print("Pre-Processing")

    # Pre-process
    convert_floats2ints(invoice_data)
    convert_floats2ints(qbo)
    for df in customer_dct.values():
        convert_floats2ints(df)

    print("Comparing FedEx Invoice to QBO")

    # Compare FedEx invoice to QBO
    qbo_pattern_match = pm.PatternMatch()

    qbo_found, qbo_not_found = qbo_pattern_match.compare_qbo(
        qbo=qbo, invoice_data=invoice_data
    )

    print("Searching through Extensiv tables for reference and receiver info matches")

    # Compare FedEx invoice to Extensiv

    reference_matches = list()
    receiver_matches = list()

    # Loop through Extensiv tables and find matches
    for customer, dataframe in tqdm(customer_dct.items(), smoothing=0.1):

        customer_pattern_match = pm.PatternMatch(name=customer)

        # find_value_match() outputs list of dicts of matches in Extensiv Table
        reference_matches.extend(
            customer_pattern_match.compare_references(
                extensiv_table=dataframe, invoice_data=qbo_not_found
            )
        )

        # Adds matches of receiver info list
        receiver_matches.extend(
            customer_pattern_match.compare_receiver_info(
                extensiv_table=dataframe, invoice_data=qbo_not_found
            )
        )

        print(customer_pattern_match)

    # Replaces Customer PO # with Customer Name if match is found
    final_matches = pm.PatternMatch()
    final_df = final_matches.make_final_df(
        reference_matches, receiver_matches, qbo_not_found
    )

    return final_df, qbo_found


if __name__ == "__main__":

    invoice_data, qbo, customer_dct = get_input(
        path=input("File Path (or press Enter for current directory): ") or os.getcwd()
    )
    final_df, qbo_found = main(invoice_data, qbo, customer_dct)
    output(final_df, qbo_found)
    print("All done")
