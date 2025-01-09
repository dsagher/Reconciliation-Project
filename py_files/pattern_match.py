import pandas as pd
import re as re
from dataclasses import dataclass


@dataclass
class ReferenceMatch:
    Reference: str
    Name: str
    Column: str
    Customer: str
    Tracking: str = None


@dataclass
class ReceiverMatch:
    Address: str = None
    Name: str = None
    Company: str = None
    Customer: str = None


class PatternMatch:

    def __init__(self, name: str = None):

        self.name = name
        self.receiver_matches: list = []
        self.reference_matches: list = []
        self.found_references: set = ()
        self.not_found_references: set = ()

    def compare_qbo(
        self, qbo: pd.DataFrame, invoice_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Function: Compares FedEx invoice with QuickBooks via keys 'Customer PO #' and 'Display_Name'
        Input: Original QuickBooks and FedEx Invoice file
        Output: qbo_not found: DataFrame with values not in QBO
                qbo_found: DataFrame with values found in QBO
        """

        # ? is 'Display_Name' the only key to compare against?
        # Merge qbo and invoice_data via Customer PO # and Display_Name via inner merge
        qbo_found = pd.merge(
            qbo,
            invoice_data,
            right_on="Customer PO #",
            left_on="Display_Name",
            how="inner",
            suffixes=["_qbo", "_invoice_data"],
        )

        # Only include columns from invoice_data in merged dataset
        invoice_cols = list(invoice_data.columns)
        qbo_found = qbo_found[invoice_cols]

        # Create sets of found and not found references
        found_references = set(qbo_found["Customer PO #"].unique())

        all_references = set(invoice_data["Customer PO #"])
        unmatched_references = all_references - found_references

        # Add to class instance
        self.not_found_references = unmatched_references
        self.found_references = found_references

        # Create new DataFrame, add Customer PO #'s, and merge with invoice_data on left merge
        qbo_not_found = pd.DataFrame(
            list(unmatched_references), columns=["Customer PO #"]
        )

        # Merge with invoice data
        qbo_not_found = qbo_not_found.merge(
            invoice_data,
            on="Customer PO #",
            how="left",
        )

        # Returning DataFrames and Dataset classes objects
        return (qbo_found, qbo_not_found)

    @staticmethod
    def reg_tokenizer(value: str) -> re.Pattern:

        # Add pattern tokens to FedEx invoice table in a new column called "Reference"
        with_letters = re.sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers = re.sub(r"\d+", r"\\d+", with_letters)
        with_spaces = re.sub(r"\s+", r"\\s+", with_numbers)

        final = re.compile(with_spaces)

        return final

    def find_matching_columns(
        self,
        extensiv_table: pd.DataFrame,
        ref_pattern: pd.Series,
        sample_size: int = 25,
    ) -> set[str]:
        """
        Function: Subfunction to iterate through each of the patterns in FedEx Invoice
        Input: Extensiv DataFrame, FedEx Reference patterns as a Series in a for loop
        Ouput: List of columns that match given Reference pattern
        """
        col_lst = set()

        # Iterate through each column in Extensiv table
        for col in extensiv_table.columns:

            # Iterate through the first 25 values of each column
            for value in extensiv_table[col][:sample_size]:

                # If match of the current reference RegEx pattern, add to set
                if re.fullmatch(ref_pattern, str(value)):

                    # Break after first match
                    col_lst.add(col.strip())
                    break

        if col_lst:
            return col_lst

    def find_extensiv_reference_columns(
        self, extensiv_table: pd.DataFrame, qbo_not_found: pd.DataFrame, customer: str
    ) -> dict[dict]:
        """
        Function: Finds all of the columns in the Extensiv table that match each 'Reference' in FedEx Invoice not in QBO
        Input: Extensiv DataFrame, FedEx Invoice DataFrame w/ added 'Pattern' column
        Ouput: Dictionary of Dictionaries:
            {Reference:   {'match_lst': list of Extensiv columns that match 'Reference' pattern,
                        'Total Charges': Charges associated with that 'Reference' in FedEx Invoice,
                        'Tracking #': Tracking number associated with that 'Reference' in FedEx Invoice}}
        Notes: May not need Total Charges and Tracking # in the end
        """

        match_dct = dict()
        suffix = 0

        # Iterate through Reference column in qbo_not_found
        for i, v in enumerate(qbo_not_found["Reference"]):

            # If previous reference is the same as current reference, add a suffix ex: "-s1"
            if i != 0 and v == qbo_not_found["Reference"][i - 1]:

                suffix += 1
                v = f"{v}-s{suffix}"

            # Reset suffix
            elif i != 0 and v != qbo_not_found["Reference"][i - 1]:
                suffix = 0

            # Call column matcher function on each value in reference column
            match_lst = self.find_matching_columns(
                extensiv_table, qbo_not_found["Pattern"][i]
            )

            #! Maybe could just do if v not in match_dct instead of doing suffix maker
            #! Tracking number may be unnecessary
            #! Customer may be unnecessary too, but keeping it just incase I want to change further functions to it
            # Add match list to dictionary of dictionaries along with Tracking # and Customer
            if match_lst is not None and not pd.isna(v):

                match_dct[v] = {
                    "match_lst": match_lst,
                    "Tracking #": (qbo_not_found["Tracking #"][i]),
                    "Customer": customer,
                }

        return match_dct

    ### - Find Extensiv Reference Columns

    def find_value_match(self, extensiv_table: pd.DataFrame, reference_columns: dict) -> list[dict]:  # fmt: skip

        match_lst = list()

        # Iterate through dict. First layer is references
        for reference in reference_columns:

            # Capture subdictionary
            columns = reference_columns[reference]["match_lst"]
            tracking_number = reference_columns[reference]["Tracking #"]
            customer = reference_columns[reference]["Customer"]

            # Iterate through each pattern-matched column in Extensiv table
            for col in extensiv_table[list[columns]]:

                # Iterate through each value in each column
                for i, val in enumerate(extensiv_table[col]):

                    # Remove suffix
                    base_reference = re.sub(r"-s\d+$", "", str(reference))

                    # Create new dictionary entry if match found and populate Dataset class
                    if val == reference or val == base_reference:

                        match_entry = ReferenceMatch(
                            Reference=base_reference,
                            Name=extensiv_table["CustomerIdentifier.Name"][i],
                            Column=col,
                            Customer=customer,
                            Tracking=tracking_number,
                        )

                        # Append to list
                        if match_entry not in match_lst:
                            self.reference_matches.append(match_entry)
                            match_lst.append(match_entry)

        return match_lst

    @staticmethod
    def create_extensiv_receiver_info(extensiv_table: pd.DataFrame) -> dict:

        # Extract receiver information from Extensiv table DataFrame and drop duplicates
        extensiv_receiver_info = extensiv_table.drop_duplicates(
            [
                "ShipTo.CompanyName",
                "ShipTo.Name",
                "ShipTo.Address1",
                "CustomerIdentifier.Name",
            ]
        )

        extensiv_receiver_dct = dict()

        # Add to dictionary
        for i, row in extensiv_receiver_info.iterrows():

            extensiv_receiver_dct[i] = {
                "Receiver Address": row["ShipTo.Address1"],
                "Receiver Company": row["ShipTo.CompanyName"],
                "Receiver Name": row["ShipTo.Name"],
                "Customer Identifier": row["CustomerIdentifier.Name"],
            }

        return extensiv_receiver_dct

    @staticmethod
    def create_invoice_data_receiver_info(invoice_data: pd.DataFrame) -> dict:  # fmt: skip

        invoice_data_dct = {}
        # Create new dictionary for invoice_data receiver info
        for i, row in invoice_data.iterrows():

            invoice_data_dct[i] = {
                "Receiver Address": row["Receiver Address"],
                "Receiver Company": row["Receiver Company"],
                "Receiver Name": row["Receiver Name"],
                "Tracking #": row["Tracking #"],
            }

        return invoice_data_dct

    def compare_receiver_info(self, invoice_data_receiver_info: dict, extensiv_receiver_info: dict) -> list[dict]:  # fmt: skip

        match_entry = dict()
        match_lst = list()
        # Iterate through each dict of invoice_data receiver info
        for i in invoice_data_receiver_info:

            # Iterate through each dict of extensiv receiver info
            for e in extensiv_receiver_info:

                # If match, create new dictionary entry
                if (
                    invoice_data_receiver_info[i]["Receiver Address"]
                    == extensiv_receiver_info[e]["Receiver Address"]
                    or invoice_data_receiver_info[i]["Receiver Name"]
                    == extensiv_receiver_info[e]["Receiver Name"]
                    or invoice_data_receiver_info[i]["Receiver Company"]
                    == extensiv_receiver_info[e]["Receiver Company"]
                ):

                    match_entry = ReceiverMatch(
                        Address=invoice_data_receiver_info[i]["Receiver Address"],
                        Name=invoice_data_receiver_info[i]["Receiver Name"],
                        Company=invoice_data_receiver_info[i]["Receiver Company"],
                        Customer=extensiv_receiver_info[e]["Customer Identifier"],
                    )

                    #! How is match_entry compared to those already in list?
                    #! Ex: if there is a matched Name, but not a matched Company, will it be appended?
                    if match_entry not in match_lst:
                        match_lst.append(match_entry)

        return match_lst

    def make_final_df(
        self,
        reference_matches: list[dict],
        receiver_matches: list[dict],
        invoice_data_not_qbo: pd.DataFrame,
    ) -> pd.DataFrame:

        try:

            # Combine receiver matches and reference matches into one list
            final_matches_lst = []
            final_matches_lst.extend(reference_matches)
            final_matches_lst.extend(receiver_matches)

            # Iterate through each row in invoice_data DataFrame
            for i, row in invoice_data_not_qbo.iterrows():

                # Iterate through matches list
                for dct in final_matches_lst:

                    if "Reference" in dct and dct["Reference"] == row["Reference"]:
                        invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    elif "Address" in dct and dct["Address"] == row["Receiver Address"]:
                        invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    elif "Name" in dct and dct["Name"] == row["Receiver Name"]:
                        invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    elif "Company" in dct and dct["Company"] == row["Receiver Company"]:
                        invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

        #! Or this
        except TypeError:
            pass

        return invoice_data_not_qbo
