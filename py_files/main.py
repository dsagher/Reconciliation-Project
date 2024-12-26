from pattern_match import *
from processing import convert_floats2ints
import os
from datetime import date
import pandas as pd
from tqdm import tqdm


def inp(input_path: str) -> pd.DataFrame:

    #! Add Error handling and logging

    orig_path = os.path.join(input_path, "input_files")

    print("Taking in files")
    # Get list of files in input_files
    for i in tqdm(os.listdir(orig_path)):

        # Load invoice_data
        if i.lower().strip().replace(" ", "_").startswith("invoice_data"):

            cur_path = os.path.join(orig_path, i)
            invoice_data = pd.read_excel(
                cur_path,
                sheet_name=f"{i.rstrip('.xlsx')}",
            )
        # Load qbo
        elif i.lower().strip().replace(" ", "_").startswith("qbo"):

            cur_path = os.path.join(orig_path, i)
            qbo = pd.read_excel(cur_path)

    # Tunnel into path/input_files/customers
    customer_path = os.path.join(orig_path, "customers")

    # Create customer_dct from all files in customer folder
    customer_dct = {}
    for i in os.listdir(customer_path):
        if i.endswith(".xlsx"):
            customer_dct[i] = pd.read_excel(f"{os.path.join(customer_path,i)}")

    customer_dct = {
        key.removesuffix(".xlsx"): value for key, value in customer_dct.items()
    }
    return invoice_data, qbo, customer_dct


def out(final_df: pd.DataFrame, qbo_found: pd.DataFrame) -> None:

    print("Writing Excel")

    cur_path = os.getcwd()
    output_dir = os.path.join(cur_path, "output_files")
    os.makedirs(output_dir, exist_ok=True)

    target_path = os.path.join(cur_path, "output_files", f"final_df_{date.today()}")

    with pd.ExcelWriter(f"{target_path}.xlsx") as writer:

        final_df.to_excel(writer, sheet_name="final_df")
        qbo_found.to_excel(writer, sheet_name="qbo_found")


def main(
    invoice_data: pd.DataFrame, qbo: pd.DataFrame, customer_dct: dict
) -> pd.DataFrame:

    print("Pre-Processing")
    # Pre-process
    convert_floats2ints(invoice_data)
    convert_floats2ints(qbo)
    for df in customer_dct.values():
        convert_floats2ints(df)

    print("Comparing FedEx Invoice to QBO")
    # Compare FedEx invoice to QBO
    qbo_found, qbo_not_found = compare_qbo(qbo, invoice_data)

    # Create Pattern Column
    qbo_not_found["Pattern"] = qbo_not_found["Reference"].apply(reg_tokenizer)

    invoice_data_receiver_info = create_invoice_data_receiver_info(qbo_not_found)

    # Find Reference and Receiver matches in Extensiv
    reference_matches = list()
    receiver_matches = list()

    print("Searching through Extensiv tables for reference and receiver info matchces")
    # Loop through Extensiv tables and find matches
    for customer, dataframe in tqdm(customer_dct.items(), smoothing=0.1):

        reference_columns = find_extensiv_reference_columns(
            dataframe, qbo_not_found, customer
        )

        reference_matches.extend(find_value_match(dataframe, reference_columns))

        extensiv_receiver_info = create_extensiv_receiver_info(dataframe)

        receiver_matches.extend(
            compare_receiver_info(invoice_data_receiver_info, extensiv_receiver_info)
        )

        final_df = make_final_df(reference_matches, receiver_matches, qbo_not_found)

    final_df = final_df.drop(columns=["Pattern"])

    print("Matching Completed")

    return final_df, qbo_found


if __name__ == "__main__":

    invoice_data, qbo, customer_dct = inp(
        input(
            input_path=input("File Path (or press Enter for current directory): ")
            or os.getcwd()
        )
    )
    final_df, qbo_found = main(invoice_data, qbo, customer_dct)
    out(final_df, qbo_found)
    print("All done")
