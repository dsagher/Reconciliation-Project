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
        Internal:
            - file_io

    Special Concerns:
        - Not catching errors related to file existence of QBO and FedEx invoice. Will be addressed.
=========================================================================================="""

import unittest
import os
import shutil
from xlsxwriter import Workbook
from tempfile import TemporaryDirectory

from file_io import FileIO


class TestIO(unittest.TestCase):

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

        # Create Excels
        self.create_excel_file(self.invoice_data, worksheet_name="invoice_data")
        self.create_excel_file(self.qbo, worksheet_name="qbo")
        self.create_excel_file(self.test_customer, worksheet_name="test_customer")

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_excel_file(self, file_path, worksheet_name):

        # Create dummy Excel file
        workbook = Workbook(file_path)
        worksheet = workbook.add_worksheet(worksheet_name)
        worksheet.write(0, 0, "Sample Data")
        worksheet.write(1, 0, "More Sample Data")  # Add some data
        workbook.close()

    def test_file_exist(self):

        # Test IO when everything is present
        FileIO(self.temp_dir_name)

    def test_input_files_folder_exist(self):

        shutil.rmtree(self.input_files)

        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_invoice_non_exist(self):

        # Test IO when invoice_data is not present
        os.remove(self.invoice_data)

        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_qbo_non_exist(self):

        # Test IO when qbo is not present
        os.remove(self.qbo)
        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_customer_file_non_exist(self):

        # Test IO when no customer file is present
        os.remove(self.test_customer)
        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_customer_folder_non_exist(self):

        # Test IO when no customer folder is present
        shutil.rmtree(self.customers)
        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_input_files_non_exist(self):

        # Test IO when no input_files folder is present
        shutil.rmtree(self.input_files)
        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_customer_file_not_folder(self):

        # Test IO when customer file is present but no customer folder is present
        shutil.rmtree(self.customers)
        customer_file = os.path.join(self.input_files, "customers")
        self.create_excel_file(customer_file, worksheet_name="customer_sheet")
        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_spelling_qbo_invoice_data(self):

        # Test IO when invoice_data and qbo is spelled funky
        os.remove(self.invoice_data)
        os.remove(self.qbo)

        self.invoice_data = os.path.join(self.input_files, "INvoIce DatA.xlsx")
        self.qbo = os.path.join(self.input_files, "qBo CustOmers.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="INvoIce DatA")
        self.create_excel_file(self.qbo, worksheet_name="qBo CustOmers")

        FileIO(self.temp_dir_name)

    def test_spelling_qbo_invoice_data_2(self):

        os.remove(self.invoice_data)

        self.invoice_data = os.path.join(self.input_files, "Fedex Invoice Data.xlsx")
        self.create_excel_file(
            self.invoice_data, worksheet_name="Fedex Invoice Data.xlsx "
        )

        FileIO(self.temp_dir_name)

    def test_spelling_qbo(self):

        os.remove(self.qbo)

        self.qbo = os.path.join(self.input_files, "Quickbooks.xlsx")
        self.create_excel_file(self.qbo, worksheet_name="Quickbooks")

        FileIO(self.temp_dir_name)

    def test_invoice_qbo_name_wrong(self):

        os.remove(self.invoice_data)
        os.remove(self.qbo)

        self.invoice_data = os.path.join(self.input_files, "INvoise_dayta.xlsx")
        self.qbo_wrong = os.path.join(self.input_files, "cookbooks.xlsx")

        self.create_excel_file(self.qbo_wrong, worksheet_name="cookbooks.xlsx")
        self.create_excel_file(self.invoice_data, worksheet_name="INvoise_dayta.xlsx")

        with self.assertRaises(FileNotFoundError):
            FileIO(self.temp_dir_name)

    def test_file_format_invoice_suffix(self):

        os.remove(self.invoice_data)

        self.invoice_data = os.path.join(self.input_files, "invoice_data")

        with self.assertRaises(Exception):
            FileIO(self.temp_dir_name)

    def test_file_format_qbo_suffix(self):

        os.remove(self.qbo)

        self.qbo = os.path.join(self.qbo, "qbo")

        with self.assertRaises(Exception):
            FileIO(self.temp_dir_name)

    def test_file_format_customer_suffix(self):
        io = FileIO(self.temp_dir_name)

        os.remove(self.test_customer)

        self.test_customer = os.path.join(self.customers, "test_customer")

        with self.assertRaises(Exception):
            io.get_input()


if __name__ == "__main__":
    unittest.main()
