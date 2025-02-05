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
            - dataclasses
        Internal:
            - None

=========================================================================================="""

import os
from re import search, IGNORECASE
from pandas import DataFrame, ExcelWriter, ExcelFile, read_csv, read_excel
from tqdm import tqdm
from typing import Tuple, Optional
from datetime import datetime


def string_normalize(str: str) -> str:
    return str.lower().strip().replace(" ", "_")


def check_file_exists(lst: list, pattern: str) -> Tuple[bool, str]:

    for file in lst:
        if search(pattern, string_normalize(file), flags=IGNORECASE):
            return True, file
    return False, None


class FileIO:

    def __init__(self, path):

        self.path: str | None = path if path else os.getcwd()

        if not (isinstance(self.path, str) or isinstance(self.path, type(None))):
            raise TypeError("Path must be String or NoneType")

        # Define root path
        self.original_path: str = os.path.normpath(self.path)
        self._validate_root_path()
        self._setup_input_files_path()
        self._validate_input_files_path()
        self._setup_customer_path()
        self._validate_customer_path()
        self._setup_invoice_data_path()
        self._validate_invoice_data_path()
        self._setup_sheets()
        self._validate_sheets()
        self._setup_qbo_path()
        self._validate_qbo_path()

    def _validate_root_path(self) -> None:
        # Raise error if original path does not exist
        if not os.path.exists(self.original_path):
            raise FileNotFoundError("Original path not found")
        self.all_files_in_root: list = os.listdir(self.original_path)

    def _setup_input_files_path(self) -> None:

        self.input_files_exists: bool
        self.input_files_folder: Optional[bool | str]

        # Define input_files folder -> root/input_files/
        self.input_files_path: str = os.path.normpath(
            os.path.join(self.path, "input_files")
        )

        # Raise error if input_files folder does not exist -> root/input_files/
        self.input_files_exists, self.input_files_folder = check_file_exists(
            self.all_files_in_root, r"input(?:_+files)?"
        )

    def _validate_input_files_path(self) -> None:

        if not self.input_files_exists:
            raise FileNotFoundError(
                "Input Files folder not found.\n\
                Expected a folder like 'input_files/' in root folder."
            )
        self.input_files_lst: str = os.listdir(self.input_files_path)

    def _setup_customer_path(self) -> None:

        self.customer_folder_exists: bool

        # Create customer folder path -> root/input_files/customer/
        self.customer_path: str = os.path.normpath(
            os.path.join(self.input_files_path, "customers")
        )
        self.customer_folder_exists = check_file_exists(
            self.input_files_lst, r"customers?"
        )

    def _validate_customer_path(self) -> None:

        if not self.customer_folder_exists:
            raise FileNotFoundError("Please create a customer folder.")
        # Raise error if customer folder does not exists or is not a directory
        if not os.path.isdir(self.customer_path):
            raise FileNotFoundError("Please create a customer folder.")

        self.customer_lst: str = os.listdir(self.customer_path)

        # Raise error if customer folder is empty
        if not len(self.customer_lst) > 0:
            raise FileNotFoundError("Customer folder must not be empty.")

    def _setup_invoice_data_path(self) -> None:

        self.invoice_data_exists: bool
        self.invoice_data_file: Optional[bool | str]

        # Raise error if invoice_data does not exist -> root/input_files/invoice_data
        self.invoice_data_exists, self.invoice_data_file = check_file_exists(
            self.input_files_lst, r"(fedex[_\-\s]*)?invoice[_\-\s]*(?:_+data)?"
        )

    def _validate_invoice_data_path(self) -> None:

        if not self.invoice_data_exists:
            raise FileNotFoundError(
                "Invoice Data not found.\
                                    Expected a file like 'invoice_data.xlsx' or \n\
                                    'fedex_invoice.xlsx' in 'input_files/' folder."
            )

        self.invoice_data_path: str = os.path.join(
            self.input_files_path, self.invoice_data_file
        )

    def _setup_sheets(self) -> None:

        self.invoice_sheet_exists: bool
        self.correct_sheet: Optional[bool | str]

        # Get sheets object and name
        self.inv_sheets: ExcelFile = ExcelFile(self.invoice_data_path)
        self.inv_sheet_names: list = self.inv_sheets.sheet_names

        # Check if file exists and input correct sheet and output correct sheet name
        self.invoice_sheet_exists, self.correct_sheet = check_file_exists(
            self.inv_sheet_names, r"(fedex[_\-\s]*)?invoice[_\-\s]*(data)?"
        )

    def _validate_sheets(self) -> None:

        if not self.invoice_sheet_exists:
            raise FileNotFoundError(
                f"No valid sheet found in '{self.input_files_path} for Invoice Data",
            )

    def _setup_qbo_path(self) -> None:

        self.qbo_exists: bool
        self.qbo_file: Optional[bool | str]

        # Raise error if qbo does not exist -> root/input_files/qbo
        self.qbo_exists, self.qbo_file = check_file_exists(
            self.input_files_lst, r"(qbo|quickbooks)"
        )

    def _validate_qbo_path(self) -> None:

        if not self.qbo_exists:
            raise FileNotFoundError(
                "QBO not found. Expected a file like 'qbo' in 'input_files/' folder"
            )

    def get_input(self) -> DataFrame:

        print("Uploading Files")

        # Iterate through list of files in input_files
        for i in tqdm(self.input_files_lst):

            self.current_path: str = os.path.join(self.input_files_path, i)

            if i == self.invoice_data_file:
                # Read Files
                if i.endswith(".xlsx"):
                    self.invoice_data = read_excel(
                        self.current_path, sheet_name=self.correct_sheet
                    )
                elif i.endswith("csv"):
                    self.invoice_data = read_csv(
                        self.current_path, sheet_name=self.correct_sheet
                    )
                else:
                    raise Exception("Invoice Data File must end in .csv or .xlsx")

            # Load qbo
            elif i == self.qbo_file:

                # Read Files
                if i.endswith(".xlsx"):
                    self.qbo = read_excel(self.current_path)
                elif i.endswith("csv"):
                    self.qbo = read_csv(self.current_path)
                else:
                    raise Exception("QBO File must end in .csv or .xlsx")

        # Check if customer folder exists

        self.customer_dct: dict = {}
        # Iterate through each customer in customer directory
        for customer in self.customer_lst:

            # Read Files into customer dictionary
            if customer.endswith(".xlsx"):
                customer_name = customer.removesuffix(".xlsx")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                self.customer_dct[customer_name] = read_excel(current_customer_path)

            elif customer.endswith(".csv"):
                customer_name = customer.removesuffix(".csv")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                self.customer_dct[customer_name] = read_csv(current_customer_path)
            else:
                raise Exception("Customer files must end in '.csv' or '.xlsx'")

        return self.invoice_data, self.qbo, self.customer_dct

    def output(self, final_df: DataFrame, qbo_found: DataFrame) -> None:

        print("Writing Excel")

        # Create output_files/ path -> root/output_files/
        self.output_dir: str = os.path.join(self.original_path, "output_files")

        # Create output_files folder if doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Create output file path
        target_path: str = os.path.join(
            self.output_dir,
            f"final_df_{datetime.now().strftime('%Y-%m-%d_%H:%M')}",
        )

        # Create Excel file -> root/output_files/excel.xlsx
        with ExcelWriter(f"{target_path}.xlsx") as writer:

            final_df.to_excel(writer, sheet_name="final_df")
            qbo_found.to_excel(writer, sheet_name="qbo_found")


if __name__ == "__main__":
    path = input("File Path (or press Enter for current directory): ")
    io = FileIO(path)
    fedex_invoice, qbo, customer_dct = io.get_input()
    io.output(qbo, fedex_invoice)
    print(fedex_invoice, qbo, customer_dct)
