"""==========================================================================================
    
    File: io_tests.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:
        Contains the unit tests for file_io.py.

    Dependencies:
        External:
            - unittest
            - os
            - shutil
            - xlsxwriter
            - tempfile
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


class TestIO(unittest.TestCase):
    """
    Test cases to test input functionality and appropriate error catching.
    """

    def setUp(self):

        self.temp_dir = TemporaryDirectory()
        self.temp_dir_name = self.temp_dir.name

        self.input_files = os.path.join(self.temp_dir_name, "input_files")
        self.customers = os.path.join(self.input_files, "customers")
        self.output_files = os.path.join(self.temp_dir_name, "output_files")

        os.makedirs(self.input_files)
        os.makedirs(self.customers)
        os.makedirs(self.output_files)

        self.fedex_invoice = os.path.join(self.input_files, "fedex_invoice.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        self.fedex_invoice_csv = os.path.join(self.input_files, "fedex_invoice.csv")
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

        workbook = Workbook(file_path)
        worksheet = workbook.add_worksheet(worksheet_name)
        worksheet.write(0, 0, "Sample Data")
        worksheet.write(1, 0, "More Sample Data")  # Add some data
        workbook.close()

    """================================= Test __init__ ====================================="""

    def test_init_file_type(self):

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

    def test_validate_root_path(self):

        # Test IO when original path does not exist
        shutil.rmtree(self.temp_dir_name)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Original path not found")

    """=============================== Test Files Exist ============================="""

    def test_files_exist_excel(self):

        self.create_excel_file(self.fedex_invoice, worksheet_name="fedex_invoice")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

        # Test IO when everything is present
        FileIO(self.temp_dir_name)

    def test_files_exist_csv(self):

        self.create_csv_file(self.fedex_invoice_csv)
        self.create_csv_file(self.qbo_csv)
        self.create_csv_file(self.test_customer_csv)

        # Test IO when everything is present
        FileIO(self.temp_dir_name)

    def test_validate_input_files_path(self):

        # Test when input files folder does not exist
        shutil.rmtree(self.input_files)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Input Files folder not found. Expected a folder like 'input_files/' in root folder.",
        )

    def test_validate_fedex_invoice_path_excel(self):

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

    def test_validate_fedex_invoice_path_csv(self):

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

    def test_validate_qbo_path_excel(self):

        # Test IO when qbo does not exist
        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_validate_qbo_path_csv(self):

        # Test IO when qbo does not exist
        self.create_csv_file(self.fedex_invoice_csv)
        self.create_csv_file(self.test_customer_csv)

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_validate_customer_path_exist(self):

        shutil.rmtree(self.customers)

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        # Test IO when customer file does not exist

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Please create a customer folder.")

    def test_validate_customer_path_empty(self):

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        # Test IO when customer file does not exist

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Customer folder must not be empty.")

    def test_validate_customer_path_not_directory(self):

        shutil.rmtree(self.customers)
        customer_file = os.path.join(self.input_files, "customers")

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(customer_file, worksheet_name="customer_sheet")

        # Test IO when customer file exists but not customer directory
        with self.assertRaises(NotADirectoryError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(str(error.exception), "Customer path is not a directory")

    """================================ Test RegEx ========================================="""

    def test_spelling_fedex_invoice(self):

        self.fedex_invoice = os.path.join(self.input_files, "INvoIce DatA.xlsx")

        self.create_excel_file(self.fedex_invoice, worksheet_name="INvoIce DatA")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_spelling_fedex_invoice_2(self):

        self.fedex_invoice = os.path.join(self.input_files, "fedex_invoice_data.xlsx")

        self.create_excel_file(self.fedex_invoice, worksheet_name="fedex_invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_spelling_fedex_invoice_3(self):

        self.fedex_invoice = os.path.join(self.input_files, "fedex_data.xlsx")

        self.create_excel_file(self.fedex_invoice, worksheet_name="fedex_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_spelling_qbo(self):

        self.qbo = os.path.join(self.input_files, "qBo CustOmers.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="qBo CustOmers")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")
        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")

        FileIO(self.temp_dir_name)

    def test_spelling_qbo_2(self):

        self.qbo = os.path.join(self.input_files, "Quickbooks.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="Quickbooks")
        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        FileIO(self.temp_dir_name)

    def test_invoice_qbo_name_wrong(self):

        self.fedex_invoice = os.path.join(self.input_files, "INvoise_dayta.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")
        self.create_excel_file(self.fedex_invoice, worksheet_name="INvoise_dayta.xlsx")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "Invoice Data not found.\
                Expected a file like 'invoice_data' or \
                'fedex_invoice' in 'input_files/' folder.",
        )

    def test_invoice_qbo_name_wrong_2(self):

        self.qbo = os.path.join(self.input_files, "cookbooks.xlsx")

        self.create_excel_file(self.qbo, worksheet_name="cookbooks")
        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        with self.assertRaises(FileNotFoundError) as error:
            FileIO(self.temp_dir_name)

        self.assertEqual(
            str(error.exception),
            "QBO not found. Expected a file like 'qbo' in 'input_files/' folder",
        )

    def test_invoice_suffix(self):

        self.fedex_invoice = os.path.join(self.input_files, "invoice_data.json")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        io = FileIO(self.temp_dir_name)
        with self.assertRaises(FileNotFoundError) as error:
            io.get_input()

        self.assertEqual(
            str(error.exception), "Invoice Data File must end in .csv or .xlsx"
        )

    def test_qbo_suffix(self):

        self.fedex_invoice = os.path.join(self.input_files, "invoice_data.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo")
        self.test_customer = os.path.join(self.customers, "test_customer.xlsx")

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="customer_sheet")

        io = FileIO(self.temp_dir_name)
        with self.assertRaises(FileNotFoundError) as error:
            io.get_input()

        self.assertEqual(str(error.exception), "QBO File must end in .csv or .xlsx")

    def test_customer_suffix(self):

        self.fedex_invoice = os.path.join(self.input_files, "invoice_data.xlsx")
        self.qbo = os.path.join(self.input_files, "qbo.xlsx")
        self.test_customer = os.path.join(self.customers, "test_customer")

        self.create_excel_file(self.fedex_invoice, worksheet_name="invoice_data")
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
