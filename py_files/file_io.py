"""==========================================================================================
    
    File: file_io.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:
        Contains the functions used in main.py for file input and output.

    Dependencies:
        External:
            - os
            - re
            - pandas
            - tqdm
            - typing
            - datetime
        Internal:
            - None

=========================================================================================="""

import os
from re import search, IGNORECASE
from pandas import DataFrame, ExcelWriter, ExcelFile, read_csv, read_excel
from tqdm import tqdm
from typing import Tuple
from datetime import datetime


class FileIO:

    def string_normalize(self, str: str) -> str:
        return str.lower().strip().replace(" ", "_")

    def check_file_exists(self, lst: list, pattern: str) -> Tuple[bool, str]:

        for file in lst:
            if search(pattern, self.string_normalize(file), flags=IGNORECASE):
                return True, file
        return False, None

    def raise_for_file_not_found(self, input: bool, message: str) -> None:

        if not input:
            raise FileNotFoundError(message)
        pass

    def get_input(self, path: str) -> DataFrame:

        # Define root path
        original_path: str = os.path.normpath(path)

        all_files_in_root: list = os.listdir(path)

        # Define input_files folder -> root/input_files/
        input_files_path = os.path.normpath(os.path.join(path, "input_files"))
        input_files_lst = os.listdir(input_files_path)

        # Create customer folder path -> root/input_files/customer/
        customer_path = os.path.normpath(os.path.join(input_files_path, "customers"))
        customer_lst = os.listdir(customer_path)

        # Raise error if original path does not exist
        self.raise_for_file_not_found(
            os.path.exists(original_path), "Original path not found"
        )

        # Raise error if input_files folder does not exist -> root/input_files/
        input_files_exists, input_files_folder = self.check_file_exists(
            all_files_in_root, r"input(?:_+files)?"
        )

        self.raise_for_file_not_found(
            input_files_exists,
            "Input Files folder not found.\n\
             Expected a folder like 'input_files/' in root folder.")  # fmt:skip

        # Raise error if invoice_data does not exist -> root/input_files/invoice_data
        invoice_data_exists, invoice_data_file = self.check_file_exists(
            input_files_lst, r"(fedex[_\-\s]*)?invoice[_\-\s]*(?:_+data)?"
        )
        self.raise_for_file_not_found(
            invoice_data_exists,
                "Invoice Data not found.\
                 Expected a file like 'invoice_data.xlsx' or \n\
                'fedex_invoice.xlsx' in 'input_files/' folder.",  # fmt:skip
        )

        # Raise error if qbo does not exist -> root/input_files/qbo
        qbo_exists, qbo_file = self.check_file_exists(
            input_files_lst, r"(qbo|quickbooks)"
        )

        self.raise_for_file_not_found(
            qbo_exists,
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

        print("Uploading Files")

        # Iterate through list of files in input_files
        for i in tqdm(input_files_lst):

            # Check if file is invoice_data
            if i == invoice_data_file:  # fmt:skip

                # Get path of current file
                current_path = os.path.join(input_files_path, i)

                # Get sheets object and name
                inv_sheets = ExcelFile(current_path)
                inv_sheet_names = inv_sheets.sheet_names

                # Check if file exists and input correct sheet and output correct sheet name
                invoice_sheet_exists, correct_sheet = self.check_file_exists(
                    inv_sheet_names, r"(fedex[_\-\s]*)?invoice[_\-\s]*(data)?"
                )

                self.raise_for_file_not_found(
                    invoice_sheet_exists,
                    f"No valid sheet found in '{input_files_path} for Invoice Data",
                )

                # Read Files
                if i.endswith(".xlsx"):
                    invoice_data = read_excel(current_path, sheet_name=correct_sheet)
                elif i.endswith("csv"):
                    invoice_data = read_csv(current_path, sheet_name=correct_sheet)
                else:
                    raise Exception("Invoice Data File must end in .csv or .xlsx")

            # Load qbo
            elif i == qbo_file:

                current_path = os.path.join(input_files_path, i)

                # Read Files
                if i.endswith(".xlsx"):
                    qbo = read_excel(current_path)
                elif i.endswith("csv"):
                    qbo = read_csv(current_path)
                else:
                    raise Exception("QBO File must end in .csv or .xlsx")

        # Check if customer folder exists
        customer_folder_exist = self.check_file_exists(input_files_lst, r"customers?")

        # Raise error if customer folder does not exists or is not a directory
        self.raise_for_file_not_found(
            customer_folder_exist, "Please create a customer folder."
        )
        self.raise_for_file_not_found(
            os.path.isdir(customer_path), "Please create a customer folder."
        )

        # Raise error if customer folder is empty
        self.raise_for_file_not_found(
            len(customer_lst) != 0, "Customer folder must not be empty."
        )

        customer_dct = {}
        # Iterate through each customer in customer directory
        for customer in customer_lst:

            # Read Files into customer dictionary
            if customer.endswith(".xlsx"):
                customer_name = customer.removesuffix(".xlsx")
                current_customer_path = f"{os.path.join(customer_path, customer)}"
                customer_dct[customer_name] = read_excel(current_customer_path)

            elif customer.endswith(".csv"):
                customer_name = customer.removesuffix(".csv")
                current_customer_path = f"{os.path.join(customer_path, customer)}"
                customer_dct[customer_name] = read_csv(current_customer_path)
            else:
                raise Exception("Customer files must end in '.csv' or '.xlsx'")

        return invoice_data, qbo, customer_dct

    def output(self, final_df: DataFrame, qbo_found: DataFrame) -> None:

        print("Writing Excel")

        # Get current directory
        current_path = os.getcwd()

        # Create output_files/ path -> root/output_files/
        output_dir = os.path.join(current_path, "output_files")

        # Create output_files folder if doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Create output file path
        target_path = os.path.join(
            current_path,
            "output_files",
            f"final_df_{datetime.now().strftime('%Y-%m-%d_%H:%M')}",
        )

        # Create Excel file -> root/output_files/excel.xlsx
        with ExcelWriter(f"{target_path}.xlsx") as writer:

            final_df.to_excel(writer, sheet_name="final_df")
            qbo_found.to_excel(writer, sheet_name="qbo_found")


if __name__ == "__main__":
    io = FileIO()
    invoice_data, qbo, customer_dct = io.get_input(
        path=input("File Path (or press Enter for current directory): ") or os.getcwd()
    )
    pass
