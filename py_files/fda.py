from pattern_match import *

# from processing import invoice_data, qbo, whill, gp_acoustics, amt
import os
import datetime
import pandas as pd


def io(input_path):

    orig_path = os.path.join(input_path, "input_files")

    # Get list of files in input_files
    for i in os.listdir(orig_path):
        print(i)
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

    # # Tunnel into path/input_files/customers
    # os.chdir(os.path.join(os.getcwd(), "customers"))

    # # Create customer_dct from all files in customer folder
    # customer_dct = {}
    # for i in os.listdir():
    #     if i.endswith(".xlsx"):
    #         customer_dct[i] = pd.read_excel(f"{os.path.join(os.getcwd(),i)}")

    # customer_dct = {
    #     key.removesuffix(".xlsx"): value for key, value in customer_dct.items()
    # }


io(input("File Path: "))


def main(invoice_data, qbo, customer_dct):

    # Compare FedEx invoice to QBO
    qbo_found, qbo_not_found = compare_qbo(qbo, invoice_data)

    # Create Pattern Column
    qbo_not_found["Pattern"] = qbo_not_found["Reference"].apply(reg_tokenizer)

    invoice_data_receiver_info = create_invoice_data_receiver_info(qbo_not_found)

    # Find Reference and Receiver matches in Extensiv
    reference_matches = list()
    receiver_matches = list()

    # Loop through Extensiv tables
    for customer, dataframe in customer_dct.items():

        reference_columns = find_extensiv_reference_columns(
            dataframe, qbo_not_found, customer
        )

        reference_matches.extend(find_value_match(dataframe, reference_columns))

        extensiv_receiver_info = create_extensiv_receiver_info(dataframe)
        print(extensiv_receiver_info)
        receiver_matches.extend(
            compare_receiver_info(invoice_data_receiver_info, extensiv_receiver_info)
        )

        final_df = make_final_df(reference_matches, receiver_matches, qbo_not_found)

    del final_df["Pattern"]

    return final_df


if __name__ == "__main__":

    # main(invoice_data, qbo, customer_dct)
    pass
