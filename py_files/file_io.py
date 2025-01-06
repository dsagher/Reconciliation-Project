import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm
import re


def str_normalize(str: str) -> str:
    return str.lower().strip().replace(" ", "_")


def check_file_exists(path, pattern):

    for file in path:
        if re.search(pattern, str_normalize(file), flags=re.IGNORECASE):
            return True, file
    return False, False


def inp(path: str) -> pd.DataFrame:

    #! add helper functions for check_file_exists and check_regex_pattern

    original_path = os.path.normpath(path)
    in_path = os.path.normpath(os.path.join(path, "input_files"))

    if not os.path.exists(original_path):
        raise FileNotFoundError("Path does not exist")

    input_files_exists = check_file_exists(os.listdir(path), r"input(?:_+files)?")
    if not input_files_exists:
        raise FileNotFoundError(
            "Input Files folder not found. Expected a folder like 'input_files/' in root folder.")  # fmt: skip

    invoice_data_exists = check_file_exists(os.listdir(in_path), r"invoice(?:_+data)?")
    if not invoice_data_exists:
        raise FileNotFoundError(
            "Invoice Data not found. Expected a file like 'invoice_data.xlsx' in 'input_files/' folder.")  # fmt: skip

    check_qbo_exists = check_file_exists(os.listdir(in_path), r"(qbo|quickbooks)")
    if not check_qbo_exists:
        raise FileNotFoundError(
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder")  # fmt: skip

    print("Taking in files")

    # Get list of files in input_files
    for i in tqdm(os.listdir(in_path)):

        # Load invoice_data
        if str_normalize(i).startswith("invoice_data"):

            cur_path = os.path.join(in_path, i)

            inv_sheets = pd.ExcelFile(cur_path)
            inv_sheet_names = inv_sheets.sheet_names

            invoice_sheet_exists, correct_sheet = check_file_exists(inv_sheet_names, r"invoice[_\-\s]*(data)?")  # fmt: skip
            if not invoice_sheet_exists:
                raise FileNotFoundError(
                    f"No valid sheet found in '{in_path} for Invoice Data")  # fmt:skip

            try:
                invoice_data = pd.read_excel(cur_path, sheet_name=correct_sheet)

            except Exception as e:
                raise ValueError(f"Error reading Excel file '{cur_path}': {e}.")

        # Load qbo
        elif str_normalize(i).startswith("qbo") or str_normalize(i).startswith("quickbooks"):  # fmt: skip

            cur_path = os.path.join(in_path, i)
            qbo = pd.read_excel(cur_path)

    # Tunnel into path/input_files/customers
    customer_path = os.path.normpath(os.path.join(in_path, "customers"))
    customer_folder_exist = check_file_exists(os.listdir(in_path), r"customers?")

    if not customer_folder_exist or not os.path.isdir(customer_path):
        raise FileNotFoundError("Please create a customer folder.")

    if len(os.listdir(customer_path)) == 0:
        raise FileNotFoundError("Customer folder is empty.")

    #! Create functionality for CSV

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

    target_path = os.path.join(
        cur_path,
        "output_files",
        f"final_df_{datetime.now().strftime('%Y-%m-%d_%H:%M')}",
    )

    with pd.ExcelWriter(f"{target_path}.xlsx") as writer:

        final_df.to_excel(writer, sheet_name="final_df")
        qbo_found.to_excel(writer, sheet_name="qbo_found")


if __name__ == "__main__":

    invoice_data, qbo, customer_dct = inp(
        path=input("File Path (or press Enter for current directory): ") or os.getcwd()
    )
    # out(final_df, qbo_found)
    pass
