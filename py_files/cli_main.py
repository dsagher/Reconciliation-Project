import pandas as pd
from recon import *

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


def main(qbo, invoice_data, extensiv):

    invoice_data_not_in_qbo = compare_qbo(qbo, invoice_data)

    invoice_data_w_patterns = add_pattern_column(invoice_data_not_in_qbo)

    gp_reference_columns = find_extensiv_reference_columns(
        extensiv, invoice_data_w_patterns
    )

    reference_matches = find_value_match(extensiv, gp_reference_columns)

    print(reference_matches)
    # invoice_data_receiver_info = create_invoice_data_receiver_info(
    #     invoice_data_not_in_qbo, reference_matches
    # )

    # extensiv_receiver_info = create_extensiv_receiver_info(extensiv)

    # receiver_info_matches = compare_receiver_info(
    #     invoice_data_receiver_info, extensiv_receiver_info
    # )

    # print(receiver_info_matches)


main(qbo=qbo, invoice_data=invoice_data, extensiv=gp_acoustics)
