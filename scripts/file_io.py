"""==========================================================================================
    
    File:       file_io.py
    Author:     Dan Sagher
    Date:       12/25/24
    Description:
        Contains the FileIO class and methods used in main.py for file input and output.

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

    Special Concerns:
        - CSV compatibility assumes that only the fedex invoice sheet is included, not the 
          itemized sheet.

=========================================================================================="""

import os
from re import search, IGNORECASE
from pandas import DataFrame, ExcelWriter, ExcelFile, read_csv, read_excel
from tqdm import tqdm
from typing import Tuple, Optional, Dict
from datetime import datetime


def string_normalize(str: str) -> str:
    return str.lower().strip().replace(" ", "_")

def check_file_exists(lst: list, pattern: str) -> Tuple[bool, str] | Tuple[bool, None]:

    for file in lst:
        if search(pattern, string_normalize(file), flags=IGNORECASE):
            return True, file
    return False, None


class FileIO:
    """
    The FileIO class is invoked in main.py with the user's specified path as the only argument.
    If the user presses enter without providing a path, the current working directory is used by default.

    Parameters:
        - path: The user's desired directory, including necessary folders and files.

    Errors Raised:
        - self._validate_root_path(): Raises FileNotFoundError if the root path does not exist.
        - self._validate_input_files_path(): Raises FileNotFoundError if the input files path is missing.
        - self._validate_fedex_invoice_path(): Raises FileNotFoundError if the invoice data file is not found.
        - self._validate_sheets(): Raises FileNotFoundError if the invoice data does not contain the correct sheet
        (applies to .xlsx files only).
        - self._validate_qbo_path(): Raises FileNotFoundError if the QBO file is not found.
        - self._validate_customer_path():
        - Raises FileNotFoundError if the customer folder does not exist.
        - Raises NotADirectoryError if the path is not a directory.
        - Raises FileNotFoundError if the customer folder is empty.
    """

    def __init__(self, path):
        """
        Defines and validates the user root path through a series of setups and error checks.
        """
        if not (isinstance(path, str)):
            raise TypeError("Path must be String")

        self.current_directory: str = os.path.normpath(os.path.normcase(os.getcwd()))

        # If user doesn't enter a path, current directory will be returned
        self.original_path: str = path if path != "" else self.current_directory

        """-------------------------Call Error Checks------------------------------"""
        self._validate_root_path()

        self._setup_input_files_path()
        self._validate_input_files_path()

        self._setup_fedex_invoice_path()
        self._validate_fedex_invoice_path()

        self._setup_sheets()
        self._validate_sheets()

        self._setup_qbo_path()
        self._validate_qbo_path()

        self._setup_customer_path()
        self._validate_customer_path()

    """----------------------------Define Error Checks-----------------------------"""

    def _validate_root_path(self):

        if not os.path.exists(self.original_path):
            raise FileNotFoundError("Original path not found")

        self.all_files_in_root: list = os.listdir(self.original_path)

    def _setup_input_files_path(self):

        self.input_files_exists: bool
        self.input_files_folder: str | None

        # root/input_files/
        self.input_files_path: str = os.path.normpath(os.path.join(self.original_path, "input_files"))

        self.input_files_exists, self.input_files_folder = check_file_exists(
            self.all_files_in_root, r"input(?:_+files)?"
        )

    def _validate_input_files_path(self):

        if not self.input_files_exists:
            raise FileNotFoundError(
                "Input Files folder not found. Expected a folder like 'input_files/' in root folder."
            )

        # root/input_files/
        self.input_files_lst: list[str] = os.listdir(self.input_files_path)

    def _setup_fedex_invoice_path(self):

        self.fedex_invoice_exists: bool
        self.fedex_invoice_file: str | None

        self.fedex_invoice_exists, self.fedex_invoice_file = check_file_exists(self.input_files_lst,
            r"\b(fedex|invoice)(?:[_\-\s]+(fedex|invoice))?(?:_+data)?\b",
        )

    def _validate_fedex_invoice_path(self):

        if not self.fedex_invoice_exists:
            raise FileNotFoundError(
                "Invoice Data not found.\
                Expected a file like 'invoice_data' or \
                'fedex_invoice' in 'input_files/' folder."
            )

        if self.fedex_invoice_file is not None:
            # root/input_files/invoice_data
            self.fedex_invoice_path: str = os.path.join(self.input_files_path, self.fedex_invoice_file)

    def _setup_sheets(self):

        if self.fedex_invoice_file is not None:

            if self.fedex_invoice_file.endswith(".xlsx"):

                self.invoice_sheet_exists: bool
                self.correct_sheet: Optional[None | str]

                self.inv_sheets: ExcelFile = ExcelFile(self.fedex_invoice_path)
                self.inv_sheet_names: list = self.inv_sheets.sheet_names

                self.invoice_sheet_exists, self.correct_sheet = check_file_exists(self.inv_sheet_names,
                    r"\b(fedex|invoice)(?:[_\-\s]+(fedex|invoice))?(?:_+data)?\b",
                )

    def _validate_sheets(self):

        if self.fedex_invoice_file is not None:
            if (self.fedex_invoice_file.endswith(".xlsx") and not self.invoice_sheet_exists):
                raise FileNotFoundError(f"No valid sheet found in '{self.input_files_path} for Invoice Data")

    def _setup_qbo_path(self):

        self.qbo_exists: bool
        self.qbo_file: str | None

        self.qbo_exists, self.qbo_file = check_file_exists(self.input_files_lst, r"(qbo|quickbooks)")

    def _validate_qbo_path(self):

        if not self.qbo_exists:
            raise FileNotFoundError("QBO not found. Expected a file like 'qbo' in 'input_files/' folder")

    def _setup_customer_path(self):

        self.customer_folder_exists: bool
        self.customer_folder_name: str | None

        # root/input_files/customer/
        self.customer_path: str = os.path.normpath(os.path.join(self.input_files_path, "customers"))

        if os.path.isdir(self.customer_path):
            self.customer_lst: list[str] = os.listdir(self.customer_path)

        self.customer_folder_exists, self.customer_folder_name = check_file_exists(self.input_files_lst, r"customers?")

    def _validate_customer_path(self):

        if not self.customer_folder_exists:
            raise FileNotFoundError("Please create a customer folder.")
        if self.customer_folder_exists and not os.path.isdir(self.customer_path):
            raise NotADirectoryError("Customer path is not a directory")

        if not len(self.customer_lst) > 0:
            raise FileNotFoundError("Customer folder must not be empty.")

    def get_input(self) -> Tuple[DataFrame, DataFrame, Dict[str, DataFrame]]:
        """
        Parses through each file in input_files folder and reads Excel and CSV files into
        Pandas DataFrames.

        Reads the FedEx invoice, QBO, and customer data into their respective DataFrames.

        Returns:
            - fedex_invoice: Pandas DataFrame of the original FedEx invoice.
            - qbo: Pandas DataFrame of the original QBO file.
            - customer_dct: Dictionary with customer names as keys and DataFrames as values.

        Errors Raised:
            - FileNotFoundError if FedEx invoice file does not end in .csv or .xlsx
            - FileNotFoundError if QBO file does not end in .csv or .xlsx
            - FileNotFoundError if any customer file does not end in .csv or .xlsx
        """
        print("Uploading Files")

        fedex_invoice = None
        qbo = None
        customer_dct = {}

        # Iterate through list of files in input_files
        for i in tqdm(self.input_files_lst):

            current_path: str = os.path.join(self.input_files_path, i)

            if i == self.fedex_invoice_file:

                if i.endswith(".xlsx"):
                    fedex_invoice = read_excel(current_path, sheet_name=self.correct_sheet)
                elif i.endswith(".csv"):
                    fedex_invoice = read_csv(current_path)
                else:
                    raise FileNotFoundError("Invoice Data File must end in .csv or .xlsx")

            # Load qbo
            elif i == self.qbo_file:

                if i.endswith(".xlsx"):
                    qbo = read_excel(current_path)
                elif i.endswith(".csv"):
                    qbo = read_csv(current_path)
                else:
                    raise FileNotFoundError("QBO File must end in .csv or .xlsx")

        # Iterate through each customer in customer directory
        for customer in self.customer_lst:

            if customer.endswith(".xlsx"):
                customer_name = customer.removesuffix(".xlsx")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                customer_dct[customer_name] = read_excel(current_customer_path)

            elif customer.endswith(".csv"):
                customer_name = customer.removesuffix(".csv")
                current_customer_path = f"{os.path.join(self.customer_path, customer)}"
                customer_dct[customer_name] = read_csv(current_customer_path)
            else:
                raise FileNotFoundError("Customer files must end in '.csv' or '.xlsx'")

        return fedex_invoice, qbo, customer_dct

    def output(self, final_df: DataFrame, qbo_found: DataFrame):
        """
        Outputs resulting Excel file to output folder in original path.
        Creates a new output folder (/root/output_folder) if does not exist.

        Parameters:
            - final_df: Pandas DataFrame of fully reconciled data
            - qbo_found: Pandas DataFrame of values found in QBO
        """
        print("Writing Excel")

        # root/output_files/
        output_dir: str = os.path.join(self.original_path, "output_files")

        os.makedirs(output_dir, exist_ok=True)

        target_path: str = os.path.join(
            output_dir,
            f"Reconciled_{datetime.now().strftime('%Y.%m.%d_%H-%M-%S')}")

        # root/output_files/filename.xlsx
        with ExcelWriter(f"{target_path}.xlsx") as writer:

            final_df.to_excel(writer, sheet_name="Reconciled")
            qbo_found.to_excel(writer, sheet_name="Found_In_QBO")


if __name__ == "__main__":
    path = input("File Path (or press Enter for current directory): ")
    io = FileIO(path)
    fedex_invoice, qbo, customer_dct = io.get_input()
    io.output(qbo, fedex_invoice)
