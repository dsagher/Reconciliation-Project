import unittest
import tempfile
import os
import shutil
import xlsxwriter
from file_io import inp, out


class TestIO(unittest.TestCase):

    def setUp(self):

        "-----------------------------------------"
        # Create temporary project folder
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_name = self.temp_dir.name

        # Create inner folder paths
        self.input_files = os.path.join(self.temp_dir_name, "input_files")
        self.customers = os.path.join(self.input_files, "customers")

        # Create inner folders
        os.makedirs(self.input_files)
        os.makedirs(self.customers)

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
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet(worksheet_name)
        worksheet.write(0, 0, "Sample Data")  # Add some data
        workbook.close()

    def test_file_existence(self):
        inp(self.temp_dir_name)

    def test_invoice_non_exist(self):
        #!
        os.remove(self.invoice_data)

        with self.assertRaises(FileNotFoundError):
            self.logger.info(inp(self.temp_dir_name))

    def test_qbo_non_exist(self):
        #!

        os.remove(self.qbo)
        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)
        with self.assertRaises(UnboundLocalError):
            inp(self.temp_dir_name)

    def test_customer_file_non_exist(self):
        os.remove(self.test_customer)
        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)

    def test_customer_folder_non_exist(self):
        shutil.rmtree(self.customers)
        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)

    def test_input_files_non_exist(self):
        shutil.rmtree(self.input_files)
        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)

    def test_customer_file_not_folder(self):

        shutil.rmtree(self.customers)
        customer_file = os.path.join(self.input_files, "customers")
        self.create_excel_file(customer_file, worksheet_name="customer_sheet")
        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)

    def test_name_qbo_invoice_data(self):

        os.remove(self.invoice_data)
        os.remove(self.qbo)

        self.invoice_data = os.path.join(self.input_files, "INvoIce DatA.xlsx")
        self.qbo = os.path.join(self.input_files, "qBo CustOmers.xlsx")

        self.create_excel_file(self.invoice_data, worksheet_name="INvoIce DatA")
        self.create_excel_file(self.qbo, worksheet_name="qBo CustOmers")

        inp(self.temp_dir_name)

    def test_name_qbo(self):
        #!
        os.remove(self.qbo)

        self.qbo = os.path.join(self.input_files, "Quickbooks.xlsx")
        self.create_excel_file(self.qbo, worksheet_name="Quickbooks")

        inp(self.temp_dir_name)

        os.remove(self.invoice_data)
        os.remove(self.qbo)

        self.invoice_data_wrong = os.path.join(self.input_files, "INvoise_dayta.xlsx")
        self.qbo_wrong = os.path.join(self.input_files, "cookbooks.xlsx")

        self.create_excel_file(self.qbo_wrong, worksheet_name="cookbooks.xlsx")
        self.create_excel_file(
            self.invoice_data_wrong, worksheet_name="INvoise_dayta.xlsx"
        )

        with self.assertRaises(FileNotFoundError):
            inp(self.temp_dir_name)


if __name__ == "__main__":
    unittest.main()
