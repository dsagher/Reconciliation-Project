from pattern_match import *

# from processing import invoice_data, qbo, whill, gp_acoustics, amt
import os
import datetime
import pandas as pd


os.chdir(os.path.join(os.getcwd(), "input_files"))

for i in os.listdir():

    if i.lower().strip().replace(" ", "_").startswith("invoice_data"):
        invoice_data = pd.read_excel(
            f"{os.path.join(os.getcwd(), i)}",
            sheet_name=f"{i.rstrip('.xlsx')}",
        )
    elif i.lower().strip().replace(" ", "_").startswith("qbo"):
        qbo = pd.read_excel(f"{os.path.join(os.getcwd(), i)}")


os.chdir(os.path.join(os.getcwd(), "customers"))

customer_lst = []

print(os.listdir())

# print(customer_lst)
customer_dct = {}

for i in os.listdir():
    if i.endswith(".xlsx"):
        customer_dct[i] = pd.read_excel(f"{os.path.join(os.getcwd(),i)}")


customer_dct = {
    key.removesuffix(".xlsx").lower().replace(" ", "_"): value
    for key, value in customer_dct.items()
}

print(customer_dct)


def main(invoice_data, qbo, customer_dct):

    qbo_found, qbo_not_found = compare_qbo(qbo, invoice_data)

    qbo_not_found["Pattern"] = qbo_not_found["Reference"].apply(reg_tokenizer)

    for customer, dataframe in customer_dct.items():

        reference_columns = find_extensiv_reference_columns(dataframe, qbo_not_found)
    return reference_columns


# amt_reference_columns = find_extensiv_reference_columns(amt, qbo_not_found)
# whill_reference_columns = find_extensiv_reference_columns(whill, qbo_not_found)

# gp_reference_matches = find_value_match(gp_acoustics, gp_reference_columns)
# amt_reference_matches = find_value_match(amt, amt_reference_columns)
# whill_reference_matches = find_value_match(whill, gp_reference_columns)

# gp_receiver_info = create_extensiv_receiver_info(gp_acoustics)
# amt_receiver_info = create_extensiv_receiver_info(amt)
# whill_receiver_info = create_extensiv_receiver_info(whill)
# invoice_data_receiver_info = create_invoice_data_receiver_info(qbo_not_found)

# gp_receiver_matches = compare_receiver_info(
#     invoice_data_receiver_info, gp_receiver_info
# )
# amt_receiver_matches = compare_receiver_info(
#     invoice_data_receiver_info, amt_receiver_info
# )
# whill_receiver_matches = compare_receiver_info(
#     invoice_data_receiver_info, whill_receiver_info
# # )

# final_df = make_final_df(gp_reference_matches, gp_receiver_matches, qbo_not_found)
# final_df = make_final_df(amt_reference_matches, amt_receiver_matches, qbo_not_found)
# final_df = make_final_df(
#     whill_reference_matches, whill_receiver_matches, qbo_not_found
# )

# del final_df["Pattern"]
# return final_df


print(main(invoice_data, qbo, customer_dct))
