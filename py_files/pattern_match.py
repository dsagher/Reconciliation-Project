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
            - rapidfuzz
        Internal:
            - None
            
=========================================================================================="""

import pandas as pd
import re as re
from rapidfuzz import fuzz


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

        return (
            f"\n"
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

    def __reg_tokenizer(self, value: str) -> re.Pattern:
        """Called during compare_qbo() to create [Pattern] column in FedEx invoice"""

        # Add pattern tokens to FedEx invoice table in a new column called "Reference"
        with_letters = re.sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers = re.sub(r"\d+(\.\d+)?", r"\\d+(\\.\\d+)?", with_letters)
        with_spaces = re.sub(r"\s+", r"\\s+", with_numbers)

        final = re.compile(with_spaces)

        return final

    def compare_qbo(self, qbo: pd.DataFrame, invoice_data: pd.DataFrame) -> pd.DataFrame:  # fmt:skip
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
        self.unmatched_references = (
            self.all_references_unique - self.found_references_unique
        )

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

    def __find_matching_columns(self,extensiv_table: pd.DataFrame,ref_pattern: pd.Series,) -> set[str]:  # fmt:skip
        """
        Subfunction in find_extensiv_reference_columns() to use to iterate over each [Reference] pattern.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param ref_pattern: RegEx pattern of current [Reference] in iteration
        :const SAMPLE_SIZE: number of records to search through in Extensiv table to find a pattern match. Default is 25
        :return cols: a unique set of columns in the Extensiv table with a matching pattern to current [Reference]

        Special Concerns:
            - Search loop breaks when *one* match is found in each Extensiv column, and only searches
              up to 25 cells per column. If there are pattern matches beyond the 25th record, they will
              be missed. This is a performance saving measure. Future iterations with multiprocessing
              can check more values in Extensiv columns.
        """
        SAMPLE_SIZE = 25
        cols = set()

        if not isinstance(extensiv_table, pd.DataFrame):
            raise ValueError("Extensiv Table Must be Pandas DataFrame")

        if ref_pattern == None:
            raise ValueError("Reference Cannot be None")

        # Iterate through each column in Extensiv table
        for col in extensiv_table.columns:

            # Iterate through the first 25 values of each column
            for value in extensiv_table[col][:SAMPLE_SIZE]:

                # If match of the current reference RegEx pattern, add to set
                if re.fullmatch(ref_pattern, str(value)):

                    # Break after first match
                    cols.add(col.strip())
                    break

        if cols:
            return cols

    def __find_extensiv_reference_columns(
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
            cols = self.__find_matching_columns(
                extensiv_table, qbo_not_found["Pattern"][i]
            )

            # Add match list to dictionary of dictionaries along with Tracking # and Customer
            if cols is not None and not pd.isna(v):
                match_dct[str(v)] = cols

        return match_dct

    ### - Find Extensiv Reference Columns

    def compare_references(self, extensiv_table: pd.DataFrame, invoice_data: pd.DataFrame) -> list[dict]:  # fmt:skip
        """
        Function called in main.py that compares each reference value in the FedEx invoice (by exact match and fuzzy match)
        with every value in the selected columns (matched by RegEx) until a match is found.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param invoice_data: Pandas DataFrame of FedEx invoice data not found in QBO
        :return match_lst: list of dictionaries containing the [Reference], [Column], and [Customer] of matched reference
        """
        FUZZY_SCORE = 75
        match_lst = list()
        unique_references = set()

        invoice_data["Pattern"] = invoice_data["Reference"].apply(self.__reg_tokenizer)

        reference_columns = self.__find_extensiv_reference_columns(
            extensiv_table, invoice_data
        )

        # Iterate through references
        for reference, columns in reference_columns.items():

            # Iterate through each column in Extensiv table
            for col in extensiv_table[list(columns)]:

                # Iterate through each value in column
                for val in extensiv_table[col]:

                    val_str = str(val).lower().strip()
                    ref_str = str(reference).lower().strip()

                    # Exact match check
                    if val_str == ref_str:
                        if reference not in unique_references:
                            match_lst.append(
                                {
                                    "Reference": reference,
                                    "Column": col,
                                    "Customer": self.name,
                                }
                            )
                            unique_references.add(reference)
                            self.append_match(reference_match=reference)

                    # Fuzzy match check
                    elif (
                        fuzz.partial_ratio(ref_str, str(self.name).lower().strip())
                        > FUZZY_SCORE
                        and reference not in unique_references
                    ):
                        match_lst.append(
                            {
                                "Reference": reference,
                                "Column": col,
                                "Customer": self.name,
                            }
                        )
                        unique_references.add(reference)
                        self.append_match(reference_match=reference)

        return match_lst

    def __create_extensiv_receiver_info(self, extensiv_table: pd.DataFrame) -> dict:
        """Private method to create Extensiv receiver information dictionaries for comparison"""

        # Extract receiver information from Extensiv DataFrame and drop duplicates
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

    def __create_invoice_data_receiver_info(self, invoice_data: pd.DataFrame) -> dict:
        """Private method to create FedEx Invoice receiver information dictionaries for comparison"""

        # Extract receiver information from FedEx Invoice DataFrame and drop duplicates
        invoice_data_info = invoice_data.drop_duplicates(
            ["Receiver Address", "Receiver Company", "Receiver Name"]
        )

        # Add to dictionary
        for i, row in invoice_data_info.iterrows():

            self.invoice_data_receiver_dct[i] = {
                "Receiver Address": row["Receiver Address"],
                "Receiver Company": row["Receiver Company"],
                "Receiver Name": row["Receiver Name"],
            }

    def compare_receiver_info(self, extensiv_table: pd.DataFrame, invoice_data: pd.DataFrame) -> list[dict]:  # fmt: skip
        """
        Compares the receiver information ([Receiver Address], [Receiver Name], [Receiver Company]) using fuzzy matching,
        of the Extensiv DataFrame to that of the FedEx Invoice DataFrame.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param invoice_data: Pandas DataFrame of FedEx invoice data not found in QBO
        :return match_lst: List of Dictionaries containing receiver information and customer name of matched values.

        Notes:
            - All three receiver information categories must exceed a fuzzy score of 70 to be matched
            - fuzzy function token_set_ratio() is used - compares strings based on common words.
        """
        FUZZY_SCORE = 70
        match_lst = []

        self.__create_extensiv_receiver_info(extensiv_table)
        self.__create_invoice_data_receiver_info(invoice_data)

        # Iterate through invoice_data receiver info
        for i, invoice_receiver in self.invoice_data_receiver_dct.items():

            # Prepare normalized strings for invoice data
            invoice_address = str(invoice_receiver["Receiver Address"]).lower().strip()
            invoice_name = str(invoice_receiver["Receiver Name"]).lower().strip()
            invoice_company = str(invoice_receiver["Receiver Company"]).lower().strip()

            # Iterate through extensiv receiver info
            for e, extensiv_receiver in self.extensiv_receiver_dct.items():

                # Prepare normalized strings for extensiv data
                extensiv_address = (str(extensiv_receiver["Receiver Address"]).lower().strip())  # fmt:skip
                extensiv_name = str(extensiv_receiver["Receiver Name"]).lower().strip()  # fmt:skip
                extensiv_company = (str(extensiv_receiver["Receiver Company"]).lower().strip())  # fmt:skip

                # Calculate fuzzy scores
                address_score = fuzz.token_set_ratio(invoice_address, extensiv_address)
                name_score = fuzz.token_set_ratio(invoice_name, extensiv_name)
                company_score = fuzz.token_set_ratio(invoice_company, extensiv_company)

                # Check if all scores exceed the threshold
                if (
                    address_score > FUZZY_SCORE
                    and name_score > FUZZY_SCORE
                    and company_score > FUZZY_SCORE
                ):
                    match_entry = {
                        "Address": invoice_receiver["Receiver Address"],
                        "Name": invoice_receiver["Receiver Name"],
                        "Company": invoice_receiver["Receiver Company"],
                        "Customer": self.name,
                    }

                    # Add to match list if unique
                    if match_entry not in match_lst:
                        self.append_match(receiver_match=match_entry)
                        match_lst.append(match_entry)

        return match_lst

    def make_final_df(
        self,
        reference_matches: list[dict[str, str]],
        receiver_matches: list[dict[str, str]],
        invoice_data_not_qbo: pd.DataFrame,
    ) -> pd.DataFrame:

        final_matches_lst = []
        final_matches_lst.extend(reference_matches)
        final_matches_lst.extend(receiver_matches)

        for i, row in invoice_data_not_qbo.iterrows():

            invoice_reference = str(row["Reference"]).lower().strip()
            invoice_receiver_address = str(row["Receiver Address"]).lower().strip()
            invoice_receiver_name = str(row["Receiver Name"]).lower().strip()
            invoice_receiver_company = str(row["Receiver Company"]).lower().strip()

            for dct in final_matches_lst:

                extensiv_reference = str(dct["Reference"]).lower().strip() \
                                     if "Reference" in dct else None  # fmt:skip

                extensiv_receiver_address = str(dct["Address"]).lower().strip() \
                                     if "Address" in dct else None  # fmt:skip

                extensiv_receiver_name = str(dct["Name"]).lower().strip() \
                                     if " Name" in dct else None  # fmt:skip

                extensiv_receiver_company = str(dct["Company"]).lower().strip() \
                                     if "Company" in dct else None  # fmt:skip

                if "Reference" in dct and extensiv_reference == invoice_reference:

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

                elif ("Address" in dct and extensiv_receiver_address == invoice_receiver_address):  # fmt:skip

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

                elif "Name" in dct and extensiv_receiver_name == invoice_receiver_name:

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

                elif ("Company" in dct and extensiv_receiver_company == invoice_receiver_company):  # fmt:skip

                    invoice_data_not_qbo.loc[i, "Customer PO #"] = dct["Customer"]

        final_df = invoice_data_not_qbo.drop(columns=["Pattern"])

        return final_df
