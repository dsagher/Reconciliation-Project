import os
import pandas as pd
from tqdm import tqdm
import pattern_match as pm
from processing import convert_floats2ints
from file_io import inp, out


def main(invoice_data: pd.DataFrame, qbo: pd.DataFrame, customer_dct: dict ) -> pd.DataFrame:  # fmt: skip

    print("Pre-Processing")

    # Pre-process
    convert_floats2ints(invoice_data)
    convert_floats2ints(qbo)
    for df in customer_dct.values():
        convert_floats2ints(df)

    print("Comparing FedEx Invoice to QBO")

    # Compare FedEx invoice to QBO
    qbo_found, qbo_not_found = pm.compare_qbo(qbo, invoice_data)

    # Create Pattern Column
    qbo_not_found["Pattern"] = qbo_not_found["Reference"].apply(pm.reg_tokenizer)

    # Extract receiver info from qbo_not_found into dicts
    invoice_data_receiver_info = pm.create_invoice_data_receiver_info(qbo_not_found)

    print("Searching through Extensiv tables for reference and receiver info matches")
    reference_matches = list()
    receiver_matches = list()

    # Loop through Extensiv tables and find matches
    for customer, dataframe in tqdm(customer_dct.items(), smoothing=0.1):

        # Outputs dict of dicts
        reference_columns = pm.find_extensiv_reference_columns(
            dataframe, qbo_not_found, customer
        )
        # find_value_match() outputs list of dicts of matches in Extensiv Table
        reference_matches.extend(pm.find_value_match(dataframe, reference_columns))

        # Extensiv receiver info in dict
        extensiv_receiver_info = pm.create_extensiv_receiver_info(dataframe)

        # Adds matches of receiver info list
        receiver_matches.extend(
            pm.compare_receiver_info(invoice_data_receiver_info, extensiv_receiver_info)
        )

    # Replaces Customer PO # with Customer Name if match is found
    final_df = pm.make_final_df(reference_matches, receiver_matches, qbo_not_found)

    # Drop Pattern column from final DataFrame
    final_df = final_df.drop(columns=["Pattern"])

    print("Matching Completed")

    return final_df, qbo_found


if __name__ == "__main__":

    invoice_data, qbo, customer_dct = inp(
        path=input("File Path (or press Enter for current directory): ") or os.getcwd()
    )
    final_df, qbo_found = main(invoice_data, qbo, customer_dct)
    out(final_df, qbo_found)
    print("All done")
    # pass
