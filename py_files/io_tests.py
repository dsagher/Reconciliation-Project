"""==========================================================================================
    
    File: io_tests.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:
        Contains the unit tests for file_io.py.

    Dependencies:
        External:
            - unittest
            - tempfile
            - shutil
            - xlsxwriter
            - os
            - pandas
            - csv
        Internal:
            - file_io

=========================================================================================="""

import unittest
import os
import shutil
from xlsxwriter import Workbook
from tempfile import TemporaryDirectory
from pandas import DataFrame
import csv

from file_io import FileIO

"""====================================== Setup  ========================================="""
#! These are still named after invoice. Should be changed to FedEx invoice.


class TestIO(unittest.TestCase):
    """Needs docstring"""

    def setUp(self):

        # Create temporary project folder
        self.temp_dir = TemporaryDirectory()
        self.temp_dir_name = self.temp_dir.name

        # Create inner folder paths
        self.input_files = os.path.join(self.temp_dir_name, "input_files")
        self.customers = os.path.join(self.input_files, "customers")
        self.output_files = os.path.join(self.temp_dir_name, "output_files")

        # Create inner folders
        os.makedirs(self.input_files)
        os.makedirs(self.customers)
        os.makedirs(self.output_files)

        # Create Excel paths
        self.invoice_data = os.path.join(self.input_files, "invoice_data.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        # Create CSV paths
        self.invoice_data_csv = os.path.join(self.input_files, "invoice_data.csv")
        self.qbo_csv = os.path.join(self.input_files, "qbo.csv")
        self.test_customer_csv = os.path.join(self.customers, "test_customer.csv")

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_csv_file(self, file_path):

        csv_file = open(file_path, "w")
        test_csv = csv.DictWriter(csv_file, fieldnames=["column1", "column2"])
        test_csv.writeheader()
        test_csv.writerow({"column1": 0, "column2": 0})
        test_csv.writerow({"column1": 1, "column2": 1})
        test_csv.writerow({"column1": 2, "column2": 2})
        csv_file.close()

    def create_excel_file(self, file_path, worksheet_name):

        # Create dummy Excel file
        workbook = Workbook(file_path)
        worksheet = workbook.add_worksheet(worksheet_name)
        worksheet.write(0, 0, "Sample Data")
        worksheet.write(1, 0, "More Sample Data")  # Add some data
        workbook.close()

    """================================= Test __init__ ====================================="""

    #! Rename these or Comment these to make it easier to reference filio.py

    def test_root_non_exist(self):

        # Test IO when original path does not exist
        shutil.rmtree(self.temp_dir_name)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Original path not found")

    def test_init_file_types(self):

        # Test when file is instantiated with non-string
        with self.assertRaises(TypeError) as error:
            FileIO(123)

        self.assertEqual(str(error.exception), "Path must be String")

    def test_init_file_types_2(self):

        # Test when file is instantiated with non-string
        df = DataFrame()
        with self.assertRaises(TypeError) as error:
            FileIO(df)

        self.assertEqual(str(error.exception), "Path must be String")

    """=============================== Test Files Exist ============================="""

    def test_excel_files_exist(self):

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

        # Test IO when everything is present
        FileIO(self.temp_dir_name)

    def test_csv_files_exist(self):

        self.create_csv_file(self.invoice_data_csv)
        self.create_csv_file(self.qbo_csv)
        self.create_csv_file(self.test_customer_csv)

        # Test IO when everything is present
        FileIO(self.temp_dir_name)

    def test_input_files_folder_exist(self):

        # Test when input files folder does not exist
        shutil.rmtree(self.input_files)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Input Files folder not found. Expected a folder like 'input_files/' in root folder.",
        )

    def test_excel_invoice_non_exist(self):

        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

        # Test IO when FedEx Invoice does not exist
        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Invoice Data not found.\
                Expected a file like 'invoice_data' or \
                'fedex_invoice' in 'input_files/' folder.",
        )

    def test_csv_invoice_non_exist(self):

        self.create_csv_file(self.qbo_csv)
        self.create_csv_file(self.test_customer_csv)

        # Test IO when FedEx Invoice does not exist
        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Invoice Data not found.\
                Expected a file like 'invoice_data' or \
                'fedex_invoice' in 'input_files/' folder.",
        )

    def test_excel_qbo_non_exist(self):

        # Test IO when qbo does not exist
        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_csv_qbo_non_exist(self):

        # Test IO when qbo does not exist
        self.create_csv_file(self.invoice_data_csv)
        self.create_csv_file(self.test_customer_csv)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_excel_customer_file_non_exist(self):

        shutil.rmtree(self.customers)

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        # Test IO when customer file does not exist

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Please create a customer folder.")

    def test_customer_file_non_exist(self):

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        # Test IO when customer file does not exist

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Customer folder must not be empty.")

    def test_customer_file_not_folder(self):

        shutil.rmtree(self.customers)
        customer_file = os.path.join(self.input_files, "customers")

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(customer_file, worksheet_name="customer_sheet")

        # Test IO when customer file exists but not customer directory
        with self.assertRaises(NotADirectoryError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Customer path is not a directory")

    """================================ Test RegEx ========================================="""

    def test_spelling_invoice_data(self):

        self.invoice_data = os.path.join(self.input_files, "INvoIce DatA.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="INvoIce DatA")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_spelling_invoice_data_2(self):

        self.invoice_data = os.path.join(self.input_files, "fedex_invoice_data.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="fedex_invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_spelling_invoice_data_3(self):

        self.invoice_data = os.path.join(self.input_files, "fedex_data.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="fedex_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_invoice_qbo_name_wrong(self):

        self.invoice_data = os.path.join(self.input_files, "INvoise_dayta.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")
        self.create_excel_file(self.invoice_data, worksheet_name="INvoise_dayta.xlsx")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Invoice Data not found.\
                Expected a file like 'invoice_data' or \
                'fedex_invoice' in 'input_files/' folder.",
        )

    def test_spelling_qbo(self):

        self.qbo = os.path.join(self.input_files, "qBo CustOmers.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="qBo CustOmers")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")
        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")

        FileIO(self.temp_dir_name)

    def test_spelling_qbo_2(self):

        self.qbo = os.path.join(self.input_files, "Quickbooks.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="Quickbooks")
        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_invoice_qbo_name_wrong(self):

        self.qbo = os.path.join(self.input_files, "cookbooks.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="cookbooks")
        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_file_format_invoice_suffix(self):

        self.invoice_data = os.path.join(self.input_files, "invoice_data.json")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        io = FileIO(self.temp_dir_name)
        with self.assertRaises(FileNotFoundError) as error:
            io.get_input()

        self.assertEqual(
            str(error.exception), "Invoice Data File must end in .csv or .xlsx"
        )

    def test_file_format_qbo_suffix(self):

        self.invoice_data = os.path.join(self.input_files, "invoice_data.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        io = FileIO(self.temp_dir_name)
        with self.assertRaises(FileNotFoundError) as error:
            io.get_input()

        self.assertEqual(str(error.exception), "QBO File must end in .csv or .xlsx")

    def test_file_format_customer_suffix(self):

        self.invoice_data = os.path.join(self.input_files, "invoice_data.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer")

        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        io = FileIO(self.temp_dir_name)
        self.test_customer = os.path.join(self.customers, "test_customer")

        with self.assertRaises(FileNotFoundError) as error:
            io.get_input()

        self.assertEqual(
            str(error.exception), "Customer files must end in '.csv' or '.xlsx'"
        )

    """=========================================================================================="""


if __name__ == "__main__":
    unittest.main()
