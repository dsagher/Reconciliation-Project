import pattern_match as pm
from processing import convert_floats2ints
from file_io import get_input, output

import os
import pandas as pd
from tqdm import tqdm

def main(invoice_data: pd.DataFrame, qbo: pd.DataFrame, customer_dct: dict ) -> pd.DataFrame:  # fmt: skip

    print("Pre-Processing")

    # Pre-process
    convert_floats2ints(invoice_data)
    convert_floats2ints(qbo)
    for df in customer_dct.values():
        convert_floats2ints(df)

    print("Comparing FedEx Invoice to QBO")

    # Compare FedEx invoice to QBO
    # qbo_found, qbo_not_found = pm.compare_qbo(qbo, invoice_data)
    qbo_pattern_match = pm.PatternMatch()

    qbo_found, qbo_not_found = qbo_pattern_match.compare_qbo(
        qbo=qbo, invoice_data=invoice_data
    )

    # Create Pattern Column
    qbo_not_found["Pattern"] = qbo_not_found["Reference"].apply(
        qbo_pattern_match.reg_tokenizer
    )

    print("Searching through Extensiv tables for reference and receiver info matches")

    reference_matches = list()
    receiver_matches = list()

    # Loop through Extensiv tables and find matches
    for customer, dataframe in tqdm(customer_dct.items(), smoothing=0.1):

        customer_pattern_match = pm.PatternMatch(name=customer)

        # find_value_match() outputs list of dicts of matches in Extensiv Table
        reference_matches.extend(
            customer_pattern_match.find_value_match(
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
    final_df = customer_pattern_match.make_final_df(
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
    # pass
