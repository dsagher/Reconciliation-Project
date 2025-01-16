"""==========================================================================================
    
    File: pattern_match.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:
        Contains the PatternMatch class and methods for matching references and receiver info 
        in Extensiv tables.

    Dependencies:
        External:
            - pandas
            - re
        Internal:
            - None
            
=========================================================================================="""

import pandas as pd
import re as re

class PatternMatch:

    """
    PatternMatch class handles the logic for comparing the FedEx invoice with Quickbooks
    and comparing [Reference] and [Receiver Name],[Receiver Company], and [Receiver Address] values
    in FedEx invoice to find matches in Extensiv.     
    
    Special Concerns:
        - Class handles logic for several different purposes. Considering breaking up class
          into smaller subclasses to handle QBO <-> FedEx invoice, and FedEx invoice <-> Extensiv
    """


    def __init__(self, name: str = None):
        
        self.name = name

        """For receiever information comparison"""
        self.extensiv_receiver_dct: dict = {}
        self.invoice_data_receiver_dct: dict = {}

        """For output of stats during runtime"""
        self.receiver_matches: list = []
        self.reference_matches: list = []
        self.reference_counter: int = 0
        self.receiver_counter: int = 0  

    def count_reference(self):
        self.reference_counter += 1

    def get_reference_count(self):
        return self.reference_counter

    def count_receiver(self):
        self.receiver_counter += 1

    def get_receiver_count(self):
        return self.receiver_counter

    def append_match(self, reference_match=None, receiver_match=None):

        if receiver_match is not None:  
            self.receiver_matches.append(receiver_match)

        if reference_match is not None:
            self.reference_matches.append(reference_match)

    def __str__(self):

        return (f"\n"
                f"Customer: {self.name}\n"
                f"{'-' * 70 }\n"
                f"\n"
                f"Total # of Reference Matches in Extensiv: {self.reference_counter}\n"
                f"Unique # of Reference Matches in Extensiv: {len(self.reference_matches)}\n"
                f"Reference Matches in Extensiv: {', \n'.join(map(str,self.reference_matches)) if not None else None}\n"
                f"{'-' * 70 }\n"
                f"\n"
                f"Total # of Receiver Matches in Extensiv: {self.receiver_counter}\n"
                f"Unique # of Receiver Matches in Extensiv: {len(self.receiver_matches)}\n"
                f"Receiver Matches in Extensiv: {', \n'.join(map(str,self.receiver_matches)) if not None else None}\n"
                f"\n"
                f"{'-' * 70 }\n"
        )
    
    
    def reg_tokenizer(self, value: str) -> re.Pattern:
        """Called during compare_qbo() to create [Pattern] column in FedEx invoice"""
        
        # Add pattern tokens to FedEx invoice table in a new column called "Reference"
        with_letters = re.sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers = re.sub(r"\d+(\.\d+)?", r"\\d+(\\.\\d+)?", with_letters)
        with_spaces = re.sub(r"\s+", r"\\s+", with_numbers)

        final = re.compile(with_spaces)

        return final
    
    def compare_qbo(
        self, qbo: pd.DataFrame, invoice_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        compare_qbo() Compares FedEx invoice with QuickBooks via keys [Customer PO #] and [Display_Name], respectively.

        :param qbo: Pandas Dataframe of original QuickBooks data
        :param invoice_data: Pandas Dataframe of FedEx invoice data
        :return qbo_found: Pandas DataFrame with records found in QBO
        :return qbo_not_found: Pandas DataFrame with records not in QBO
        """

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
        self.found_references_unique = set(qbo_found["Customer PO #"].unique())
        self.all_references_unique = set(invoice_data["Customer PO #"])
        self.unmatched_references = self.all_references_unique - self.found_references_unique

        # Create new DataFrame, add Customer PO #'s, and merge with invoice_data on left merge
        qbo_not_found = pd.DataFrame(
            list(self.unmatched_references), columns=["Customer PO #"]
        )

        # Merge with invoice data
        qbo_not_found = qbo_not_found.merge(
            invoice_data,
            on="Customer PO #",
            how="left",
        )

        return (qbo_found, qbo_not_found)

    def find_matching_columns(
        self,
        extensiv_table: pd.DataFrame,
        ref_pattern: pd.Series,
        sample_size: int = 25,
    ) -> set[str]:
        """
        Subfunction in find_extensiv_reference_columns() to use to iterate over each [Reference] pattern.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param ref_pattern: RegEx pattern of current [Reference] in iteration
        :sample_size: number of records to search through in Extensiv table to find a pattern match. Default is 25
        :return cols: a unique set of columns in the Extensiv table with a matching pattern to current [Reference]

        Special Concerns:
            - Search loop breaks when *one* match is found in each Extensiv column, and only searches 
              up to 25 cells per column. If there are pattern matches beyond the 25th record, they will 
              be missed. This is a performance saving measure. Future iterations with multiprocessing
              can check more values in Extensiv columns. 
        """
        cols = set()

        if not isinstance(extensiv_table, pd.DataFrame):
            raise ValueError("Extensiv Table Must be Pandas DataFrame")

        if ref_pattern == None:
            raise ValueError("Reference Cannot be None")

        # Iterate through each column in Extensiv table
        for col in extensiv_table.columns:

            # Iterate through the first 25 values of each column
            for value in extensiv_table[col][:sample_size]:

                # If match of the current reference RegEx pattern, add to set
                if re.fullmatch(ref_pattern, str(value)):

                    # Break after first match
                    cols.add(col.strip())
                    break

        if cols:
            return cols

    def find_extensiv_reference_columns(
        self, extensiv_table: pd.DataFrame, qbo_not_found: pd.DataFrame) -> dict[str,set]:  # fmt: skip
        """
        Subfunction called in compare_references() that iterates through each [Reference] and calls find_matching_columns()
        for each reference.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param qbo_not_found: Pandas DataFrame of FedEx invoice without values found in QBO
        :return match_dct: Dictionary of dictionaries. Outer dictionary key are References, values
         are sets of columns with matching RegEx patterns.
        """

        match_dct = dict()

        # Iterate through Reference column in qbo_not_found
        for i, v in enumerate(qbo_not_found["Reference"]):

            # Call column matcher function on each value in reference column
            cols = self.find_matching_columns(
                extensiv_table, qbo_not_found["Pattern"][i]
            )

            # Add match list to dictionary of dictionaries along with Tracking # and Customer
            if cols is not None and not pd.isna(v):
                match_dct[str(v)] = cols
                
        return match_dct

    ### - Find Extensiv Reference Columns

    def compare_references(
        self, extensiv_table: pd.DataFrame, invoice_data: pd.DataFrame
    ) -> list[dict]:

        invoice_data["Pattern"] = invoice_data["Reference"].apply(self.reg_tokenizer)

        reference_columns = self.find_extensiv_reference_columns(
            extensiv_table, invoice_data
        )

        match_lst = list()

        # Iterate through dict. First layer is references
        for reference, columns in reference_columns.items():

            # Iterate through each pattern-matched column in Extensiv table
            for col in extensiv_table[list[columns]]:

                # Iterate through each value in each column
                for val in extensiv_table[col]:

                    # Create new dictionary entry if match found and populate Dataset class
                    if str(val) == str(reference):

                        match_entry = {
                            "Reference": reference,
                            "Column": col,
                            "Customer": self.name,
                        }

                        # Append to user output list and return list
                        if match_entry not in match_lst:
                            self.append_match(
                                reference_match=f'{match_entry["Reference"]}'
                            )
                            match_lst.append(match_entry)

        return match_lst

    def create_extensiv_receiver_info(self, extensiv_table: pd.DataFrame) -> dict:

        # Extract receiver information from Extensiv table DataFrame and drop duplicates
        extensiv_receiver_info = extensiv_table.drop_duplicates(
            [
                "ShipTo.CompanyName",
                "ShipTo.Name",
                "ShipTo.Address1",
            ]
        )

        # Add to dictionary
        for i, row in extensiv_receiver_info.iterrows():

            self.extensiv_receiver_dct[i] = {
                "Receiver Address": row["ShipTo.Address1"],
                "Receiver Company": row["ShipTo.CompanyName"],
                "Receiver Name": row["ShipTo.Name"],
            }

    def create_invoice_data_receiver_info(self, invoice_data: pd.DataFrame) -> dict:

        invoice_data_info = invoice_data.drop_duplicates(
            ["Receiver Address", "Receiver Company", "Receiver Name"]
        )

        # Create new dictionary for invoice_data receiver info
        for i, row in invoice_data_info.iterrows():

            self.invoice_data_receiver_dct[i] = {
                "Receiver Address": row["Receiver Address"],
                "Receiver Company": row["Receiver Company"],
                "Receiver Name": row["Receiver Name"],
            }

    def compare_receiver_info(
        self, extensiv_table: pd.DataFrame, invoice_data: pd.DataFrame
    ) -> list[dict]:

        match_entry = dict()
        match_lst = list()

        self.create_extensiv_receiver_info(extensiv_table)
        self.create_invoice_data_receiver_info(invoice_data)

        # Iterate through each dict of invoice_data receiver info
        for i in self.invoice_data_receiver_dct:
            
            # Iterate through each dict of extensiv receiver info
            for e in self.extensiv_receiver_dct:

                # If match, create new dictionary entry
                if (
                    str(self.invoice_data_receiver_dct[i]["Receiver Address"]).lower().strip() # fmt: skip
                    == str(self.extensiv_receiver_dct[e]["Receiver Address"]).lower().strip() # fmt: skip
                    and str(self.invoice_data_receiver_dct[i]["Receiver Name"]).lower().strip()  # fmt: skip
                    == str(self.extensiv_receiver_dct[e]["Receiver Name"]).lower().strip()  # fmt: skip
                    and str(self.invoice_data_receiver_dct[i]["Receiver Company"]).lower().strip() # fmt: skip
                    == str(self.extensiv_receiver_dct[e]["Receiver Company"]).lower().strip() # fmt: skip
                ):

                    match_entry = {
                        "Address": self.invoice_data_receiver_dct[i]["Receiver Address"],
                        "Name": self.invoice_data_receiver_dct[i]["Receiver Name"],
                        "Company": self.invoice_data_receiver_dct[i]["Receiver Company"],
                        "Customer": self.name,
                    }  # fmt: skip

                    if match_entry not in match_lst:
                        self.append_match(receiver_match=match_entry)
                        match_lst.append(match_entry)

        return match_lst

    def make_final_df(
        self,
        reference_matches: list[dict],
        receiver_matches: list[dict],
        invoice_data_not_qbo: pd.DataFrame,
    ) -> pd.DataFrame:

        final_matches_lst = []
        final_matches_lst.extend(reference_matches)
        final_matches_lst.extend(receiver_matches)

        for i, row in invoice_data_not_qbo.iterrows():

            for dct in final_matches_lst:

                if "Reference" in dct and str(dct["Reference"]).strip().lower() == \
                    str(row["Reference"]).strip().lower():

                    self.count_reference()
                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

                elif "Address" in dct and str(dct["Address"]).strip().lower() == \
                    str(row["Receiver Address"]).strip().lower():

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    self.count_receiver()

                elif "Name" in dct and str(dct["Name"]).strip().lower() == \
                    str(row["Receiver Name"]).strip().lower():

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    self.count_receiver()

                elif "Company" in dct and str(dct["Company"]).strip().lower() == \
                    str(row["Receiver Company"]).strip().lower():

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]
                    self.count_receiver()

        final_df = invoice_data_not_qbo.drop(columns=["Pattern"])

        return final_df
