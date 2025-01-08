import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm
import re
from typing import Tuple


def str_normalize(str: str) -> str:
    return str.lower().strip().replace(" ", "_")


def check_file_exists(lst: list, pattern: str) -> Tuple[bool, str]:

    for file in lst:
        if re.search(pattern, str_normalize(file), flags=re.IGNORECASE):
            return True, file
    return False, False


def inp(path: str) -> pd.DataFrame:

    # Define root path
    original_path = os.path.normpath(path)

    # Define input_files folder -> root/input_files/
    in_path = os.path.normpath(os.path.join(path, "input_files"))

    # Raise error if original path does not exist
    if not os.path.exists(original_path):
        raise FileNotFoundError("Path does not exist")

    # Raise error if input_files folder does not exist -> root/input_files/
    input_files_exists = check_file_exists(os.listdir(path), r"input(?:_+files)?")
    if not input_files_exists:
        raise FileNotFoundError(
            "Input Files folder not found. Expected a folder like 'input_files/' in root folder.")  # fmt: skip

    # Raise error if invoice_data does not exist -> root/input_files/invoice_data
    invoice_data_exists = check_file_exists(os.listdir(in_path), r"invoice(?:_+data)?")
    if not invoice_data_exists:
        raise FileNotFoundError(
            "Invoice Data not found. Expected a file like 'invoice_data.xlsx' in 'input_files/' folder.")  # fmt: skip

    # Raise error if qbo does not exist -> root/input_files/qbo
    check_qbo_exists = check_file_exists(os.listdir(in_path), r"(qbo|quickbooks)")
    if not check_qbo_exists:
        raise FileNotFoundError(
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder")  # fmt: skip

    print("Taking in files")

    # Iterate through list of files in input_files
    for i in tqdm(os.listdir(in_path)):

        #! Could make more flexible with RegEx
        # Check if file is invoice_data
        if str_normalize(i).startswith("invoice_data"):

            # Get path of current file
            cur_path = os.path.join(in_path, i)

            # Get sheets object and name
            inv_sheets = pd.ExcelFile(cur_path)
            inv_sheet_names = inv_sheets.sheet_names

            # Check if file exists and input correct sheet and output correct sheet name
            invoice_sheet_exists, correct_sheet = check_file_exists(inv_sheet_names, r"invoice[_\-\s]*(data)?")  # fmt: skip
            if not invoice_sheet_exists:
                raise FileNotFoundError(
                    f"No valid sheet found in '{in_path} for Invoice Data")  # fmt:skip

            # Read Excel
            try:
                invoice_data = pd.read_excel(cur_path, sheet_name=correct_sheet)

            except Exception as e:
                raise ValueError(f"Error reading Excel file '{cur_path}': {e}.")

        # Load qbo
        elif str_normalize(i).startswith("qbo") or str_normalize(i).startswith("quickbooks"):  # fmt: skip

            cur_path = os.path.join(in_path, i)

            qbo = pd.read_excel(cur_path)

    # Create customer folder path -> root/input_files/customer/
    customer_path = os.path.normpath(os.path.join(in_path, "customers"))

    # Check if customer folder exists
    customer_folder_exist = check_file_exists(os.listdir(in_path), r"customers?")

    # Raise error if customer folder does not exists or is not a directory
    if not customer_folder_exist or not os.path.isdir(customer_path):
        raise FileNotFoundError("Please create a customer folder.")

    # Raise error if customer folder is empty
    if len(os.listdir(customer_path)) == 0:
        raise FileNotFoundError("Customer folder is empty.")

    #! Create functionality for CSV
    # Create customer_dct from all files in customer folder to feed into main()
    customer_dct = {}

    # Iterate through each customer in customer directory
    for i in os.listdir(customer_path):

        # Read Excel into customer dictionary
        # {customer_name: pd.DataFrame}
        if i.endswith(".xlsx"):
            customer_dct[i] = pd.read_excel(f"{os.path.join(customer_path,i)}")

    # Remove .xlsx suffix from each key
    customer_dct = {
        key.removesuffix(".xlsx"): value for key, value in customer_dct.items()
    }

    return invoice_data, qbo, customer_dct


def out(final_df: pd.DataFrame, qbo_found: pd.DataFrame) -> None:

    print("Writing Excel")

    # Get current directory
    cur_path = os.getcwd()

    # Create output_files/ path -> root/output_files/
    output_dir = os.path.join(cur_path, "output_files")

    # Create output_files folder if doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create output file path
    target_path = os.path.join(
        cur_path,
        "output_files",
        f"final_df_{datetime.now().strftime('%Y-%m-%d_%H:%M')}",
    )

    # Create Excel file -> root/output_files/excel.xlsx
    with pd.ExcelWriter(f"{target_path}.xlsx") as writer:

        final_df.to_excel(writer, sheet_name="final_df")
        qbo_found.to_excel(writer, sheet_name="qbo_found")


if __name__ == "__main__":

    invoice_data, qbo, customer_dct = inp(
        path=input("File Path (or press Enter for current directory): ") or os.getcwd()
    )
    # out(final_df, qbo_found)
    pass
