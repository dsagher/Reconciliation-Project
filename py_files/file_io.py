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
from typing import Tuple, Optional, NoReturn
from datetime import datetime


def string_normalize(str: str) -> str:
    return str.lower().strip().replace(" ", "_")


def check_file_exists(
    lst: list, pattern: str
) -> Optional[Tuple[bool, str] | Tuple[bool, None]]:

    for file in lst:
        if search(pattern, string_normalize(file), flags=IGNORECASE):
            return True, file
    return False, None


class FileIO:

    def __init__(self, path):

        if not (isinstance(path, str)):
            raise TypeError("Path must be String")

        self.current_directory: str = os.path.normpath(os.path.normcase(os.getcwd()))

        # If user doesn't enter a path, current directory will be returned
        self.original_path: str = path if path != "" else self.current_directory

        # Call error checks
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

    def _validate_root_path(self) -> NoReturn:
        # Raise error if original path does not exist
        if not os.path.exists(self.original_path):
            raise FileNotFoundError("Original path not found")

        self.all_files_in_root: list = os.listdir(self.original_path)

    def _setup_input_files_path(self) -> NoReturn:

        self.input_files_exists: bool
        self.input_files_folder: Optional[None | str]

        # Define input_files folder -> root/input_files/
        self.input_files_path: str = os.path.normpath(
            os.path.join(self.original_path, "input_files")
        )

        # Check if file matches RegEx
        self.input_files_exists, self.input_files_folder = check_file_exists(
            self.all_files_in_root, r"input(?:_+files)?"
        )

    def _validate_input_files_path(self) -> NoReturn:

        if not self.input_files_exists:
            raise FileNotFoundError(
                "Input Files folder not found.\n\
                Expected a folder like 'input_files/' in root folder."
            )
        self.input_files_lst: str = os.listdir(self.input_files_path)

    def _setup_customer_path(self) -> NoReturn:

        self.customer_folder_exists: bool

        # Create customer folder path -> root/input_files/customer/
        self.customer_path: str = os.path.normpath(
            os.path.join(self.input_files_path, "customers")
        )

        # Check if file matches RegEx
        self.customer_folder_exists = check_file_exists(
            self.input_files_lst, r"customers?"
        )

    def _validate_customer_path(self) -> NoReturn:

        # Raise error if customer folder does not exists or is not a directory
        if not self.customer_folder_exists:
            raise FileNotFoundError("Please create a customer folder.")
        if not os.path.isdir(self.customer_path):
            raise FileNotFoundError("Please create a customer folder.")

        # Create list of customers
        self.customer_lst: str = os.listdir(self.customer_path)

        # Raise error if customer folder is empty
        if not len(self.customer_lst) > 0:
            raise FileNotFoundError("Customer folder must not be empty.")

    def _setup_invoice_data_path(self) -> NoReturn:

        self.invoice_data_exists: bool
        self.invoice_data_file: Optional[None | str]

        # Check if file matches RegEx -> root/input_files/invoice_data
        self.invoice_data_exists, self.invoice_data_file = check_file_exists(
            self.input_files_lst, r"(fedex[_\-\s]*)?invoice[_\-\s]*(?:_+data)?"
        )

    def _validate_invoice_data_path(self) -> NoReturn:

        # Raise error if fedex invoice file does not exist
        if not self.invoice_data_exists:
            raise FileNotFoundError(
                "Invoice Data not found.\
                Expected a file like 'invoice_data.xlsx' or \n\
                'fedex_invoice.xlsx' in 'input_files/' folder."
            )

        # Create invoice data path
        self.invoice_data_path: str = os.path.join(
            self.input_files_path, self.invoice_data_file
        )

    def _setup_sheets(self) -> NoReturn:

        self.invoice_sheet_exists: bool
        self.correct_sheet: Optional[None | str]

        # Get sheets object and name
        self.inv_sheets: ExcelFile = ExcelFile(self.invoice_data_path)
        self.inv_sheet_names: list = self.inv_sheets.sheet_names

        # Check if sheets match RegEx and output correct sheet name
        self.invoice_sheet_exists, self.correct_sheet = check_file_exists(
            self.inv_sheet_names, r"(fedex[_\-\s]*)?invoice[_\-\s]*(data)?"
        )

    def _validate_sheets(self) -> NoReturn:

        # Raise error if none of the correct Excel sheets exist
        if not self.invoice_sheet_exists:
            raise FileNotFoundError(
                f"No valid sheet found in '{self.input_files_path} for Invoice Data",
            )

    def _setup_qbo_path(self) -> NoReturn:

        self.qbo_exists: bool
        self.qbo_file: Optional[None | str]

        # Check if file matches RegEx in root/input_files/qbo or quickbooks
        self.qbo_exists, self.qbo_file = check_file_exists(
            self.input_files_lst, r"(qbo|quickbooks)"
        )

    def _validate_qbo_path(self) -> NoReturn:

        # Raise error if qbo file does not exist
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

                # Read files
                if i.endswith(".xlsx"):
                    invoice_data = read_excel(
                        self.current_path, sheet_name=self.correct_sheet
                    )
                elif i.endswith(".csv"):
                    invoice_data = read_csv(
                        self.current_path, sheet_name=self.correct_sheet
                    )
                else:
                    raise Exception("Invoice Data File must end in .csv or .xlsx")

            # Load qbo
            elif i == self.qbo_file:

                # Read files
                if i.endswith(".xlsx"):
                    qbo = read_excel(self.current_path)
                elif i.endswith(".csv"):
                    qbo = read_csv(self.current_path)
                else:
                    raise Exception("QBO File must end in .csv or .xlsx")

        customer_dct: dict = {}

        # Iterate through each customer in customer directory
        for customer in self.customer_lst:

            # Read Files into customer dictionary
            if customer.endswith(".xlsx"):
                customer_name = customer.removesuffix(".xlsx")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                customer_dct[customer_name] = read_excel(current_customer_path)

            elif customer.endswith(".csv"):
                customer_name = customer.removesuffix(".csv")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                customer_dct[customer_name] = read_csv(current_customer_path)
            else:
                raise Exception("Customer files must end in '.csv' or '.xlsx'")

        return invoice_data, qbo, customer_dct

    def output(self, final_df: DataFrame, qbo_found: DataFrame) -> NoReturn:

        print("Writing Excel")

        # Create output_files/ path -> root/output_files/
        output_dir: str = os.path.join(self.original_path, "output_files")

        # Create output_files folder if doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Create output file path with current date and time
        target_path: str = os.path.join(
            output_dir,
            f"final_df_{datetime.now().strftime('%Y.%m.%d_%H-%M-%S')}",
        )

        # Create Excel file -> root/output_files/filename.xlsx
        with ExcelWriter(f"{target_path}.xlsx") as writer:

            final_df.to_excel(writer, sheet_name="final_df")
            qbo_found.to_excel(writer, sheet_name="qbo_found")


if __name__ == "__main__":
    path = input("File Path (or press Enter for current directory): ")
    io = FileIO(path)
    fedex_invoice, qbo, customer_dct = io.get_input()
    io.output(qbo, fedex_invoice)
