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

from re import Pattern, sub, compile, fullmatch
from pandas import DataFrame, Series, merge, isna
from rapidfuzz import fuzz
from dataclasses import dataclass, field


# class PatternMatch:
#     #! Might use this as parent class to inherit but might not be necessary.
#     #! The final DF isnt being made from qbo_found
#     """
#     PatternMatch class handles the logic for comparing the FedEx invoice with Quickbooks
#     and comparing [Reference] and [Receiver Name],[Receiver Company], and [Receiver Address] values
#     in FedEx invoice to find matches in Extensiv.

#     Special Concerns:
#         - Class handles logic for several different purposes. Considering breaking up class
#           into smaller subclasses to handle QBO <-> FedEx invoice, and FedEx invoice <-> Extensiv
#     """


@dataclass
class FindCustomerPO:

    qbo: DataFrame
    fedex_invoice: DataFrame

    def __post_init__(self):
        if not isinstance(self.qbo, DataFrame):
            raise ValueError("Extensiv Table Must be Pandas DataFrame")
        if not isinstance(self.fedex_invoice, DataFrame):
            raise ValueError("Extensiv Table Must be Pandas DataFrame")

    def compare_qbo(self) -> DataFrame:  # fmt:skip
        """
        compare_qbo() Compares FedEx invoice with QuickBooks via keys [Customer PO #] and [Display_Name], respectively.

        :param qbo: Pandas Dataframe of original QuickBooks data
        :param fedex_invoice: Pandas Dataframe of FedEx invoice data
        :return qbo_found: Pandas DataFrame with records found in QBO
        :return qbo_not_found: Pandas DataFrame with records not in QBO
        """

        # Merge qbo and fedex_invoice via Customer PO # and Display_Name via inner merge

        qbo_found = merge(
            self.qbo,
            self.fedex_invoice,
            right_on="Customer PO #",
            left_on="Display_Name",
            how="inner",
            suffixes=["_qbo", "_fedex_invoice"],
        )

        # Only include columns from fedex_invoice in merged dataset
        fedex_columns = list(self.fedex_invoice.columns)
        qbo_found = qbo_found[fedex_columns]

        # Create sets of found and not found references
        self.found_references_unique = set(qbo_found["Customer PO #"].unique())
        self.all_references_unique = set(self.fedex_invoice["Customer PO #"])
        self.unmatched_references = (self.all_references_unique - self.found_references_unique)  # fmt: skip

        # Create new DataFrame, add Customer PO #'s, and merge with fedex_invoice on left merge
        qbo_not_found = DataFrame(list(self.unmatched_references), columns=["Customer PO #"])  # fmt:skip

        # Merge with invoice data
        qbo_not_found = qbo_not_found.merge(
            self.fedex_invoice,
            on="Customer PO #",
            how="left",
        )

        return (qbo_found, qbo_not_found)


@dataclass
class FindPatternMatches:

    name: str
    extensiv_table: DataFrame
    fedex_invoice: DataFrame

    def __post_init__(self):
        try:
            if not (
                isinstance(self.extensiv_table, DataFrame)
                or isinstance(self.fedex_invoice, DataFrame)
            ):
                raise TypeError("Both tables must be DataFrames")
        except TypeError as e:
            print(f"Error {e}")

    """For receiever information comparison"""
    extensiv_receiver_dct: dict = field(default_factory=dict)
    fedex_invoice_receiver_dct: dict = field(default_factory=dict)

    """For output of stats during runtime"""
    receiver_matches: list = field(default_factory=list)
    reference_matches: list = field(default_factory=list)

    def append_match(self, reference_match: str = None, receiver_match: str = None):

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
            f"Unique # of Reference Matches in Extensiv: {len(self.reference_matches)}\n"
            f"Reference Matches in Extensiv: {', \n'.join(map(str,self.reference_matches)) if not None else None}\n"
            f"{'-' * 70 }\n"
            f"\n"
            f"Unique # of Receiver Matches in Extensiv: {len(self.receiver_matches)}\n"
            f"Receiver Matches in Extensiv: {', \n'.join(map(str,self.receiver_matches)) if not None else None}\n"
            f"\n"
            f"{'-' * 70 }\n"
        )

    def __reg_tokenizer(self, value: str) -> Pattern:
        """Called during compare_qbo() to create [Pattern] column in FedEx invoice"""

        # Add pattern tokens to FedEx invoice table in a new column called "Reference"
        with_letters = sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers = sub(r"\d+(\.\d+)?", r"\\d+(\\.\\d+)?", with_letters)
        with_spaces = sub(r"\s+", r"\\s+", with_numbers)

        final = compile(with_spaces)

        return final

    def __find_matching_columns(self,extensiv_table: DataFrame,ref_pattern: Series,) -> set[str]:  # fmt:skip
        """
        Private method called in find_extensiv_reference_columns() to use to iterate over each [Reference] pattern.

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

        # Iterate through each column in Extensiv table
        for col in extensiv_table.columns:

            # Iterate through the first 25 values of each column
            for value in extensiv_table[col][:SAMPLE_SIZE]:

                # If match of the current reference RegEx pattern, add to set
                if fullmatch(ref_pattern, str(value)):

                    # Break after first match
                    cols.add(col.strip())
                    break

        if cols:
            return cols

    def __find_extensiv_reference_columns(
        self, extensiv_table: DataFrame, fedex_invoice: DataFrame) -> dict[str,set]:  # fmt: skip
        """
        Subfunction called in compare_references() that iterates through each [Reference] and calls find_matching_columns()
        for each reference.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param fedex_invoice: Pandas DataFrame of FedEx invoice without values found in QBO
        :return match_dct: Dictionary of dictionaries. Outer dictionary key are References, values
         are sets of columns with matching RegEx patterns.
        """

        match_dct = dict()

        # Iterate through Reference column in fedex_invoice
        for i, v in enumerate(fedex_invoice["Reference"]):

            # Call column matcher function on each value in reference column
            cols = self.__find_matching_columns(extensiv_table, fedex_invoice["Pattern"][i])  # fmt: skip

            # Add match list to dictionary
            if cols is not None and not isna(v):
                match_dct[str(v)] = cols

        return match_dct

    def compare_references(self) -> list[dict]:  # fmt:skip
        """
        Function called in main.py that compares each reference value in the FedEx invoice (by exact match and fuzzy match)
        with every value in the selected columns (matched by RegEx) until a match is found.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param fedex_invoice: Pandas DataFrame of FedEx invoice data not found in QBO
        :return match_lst: list of dictionaries containing the [Reference], [Column], and [Customer] of matched reference
        """
        FUZZY_SCORE: int = 75
        match_lst: list = list()
        unique_references: set = set()

        self.fedex_invoice["Pattern"] = self.fedex_invoice["Reference"].apply(self.__reg_tokenizer)  # fmt:skip
        reference_columns = self.__find_extensiv_reference_columns(self.extensiv_table, self.fedex_invoice)  # fmt:skip

        # Iterate through references
        for reference, columns in reference_columns.items():

            # Iterate through each column in Extensiv table
            for col in self.extensiv_table[list(columns)]:

                # Iterate through each value in column
                for val in self.extensiv_table[col]:

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

    def __create_extensiv_receiver_info(self, extensiv_table: DataFrame) -> dict:
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

    def __create_fedex_invoice_receiver_info(self, fedex_invoice: DataFrame) -> dict:
        """Private method to create FedEx Invoice receiver information dictionaries for comparison"""

        # Extract receiver information from FedEx Invoice DataFrame and drop duplicates
        fedex_invoice_info = fedex_invoice.drop_duplicates(
            ["Receiver Address", "Receiver Company", "Receiver Name"]
        )

        # Add to dictionary
        for i, row in fedex_invoice_info.iterrows():

            self.fedex_invoice_receiver_dct[i] = {
                "Receiver Address": row["Receiver Address"],
                "Receiver Company": row["Receiver Company"],
                "Receiver Name": row["Receiver Name"],
            }

    def compare_receiver_info(self) -> list[dict]:  # fmt: skip
        """
        Compares the receiver information ([Receiver Address], [Receiver Name], [Receiver Company]) using fuzzy matching,
        of the Extensiv DataFrame to that of the FedEx Invoice DataFrame.

        :param extensiv_table: Pandas DataFrame of individual customer table in Extensiv
        :param fedex_invoice: Pandas DataFrame of FedEx invoice data not found in QBO
        :return match_lst: List of Dictionaries containing receiver information and customer name of matched values

        Notes:
            - All three receiver information categories must exceed a fuzzy score of 70 to be matched
            - fuzzy function token_set_ratio() is used - compares strings based on common words
        """
        FUZZY_SCORE = 70
        match_lst = []

        self.__create_extensiv_receiver_info(self.extensiv_table)
        self.__create_fedex_invoice_receiver_info(self.fedex_invoice)

        # Iterate through FedEx invoice receiver info
        for i, fedex_receiver in self.fedex_invoice_receiver_dct.items():

            # Prepare normalized strings for FedEx invoice data
            fedex_address = str(fedex_receiver["Receiver Address"]).lower().strip()
            fedex_name = str(fedex_receiver["Receiver Name"]).lower().strip()
            fedex_company = str(fedex_receiver["Receiver Company"]).lower().strip()

            # Iterate through extensiv receiver info
            for e, extensiv_receiver in self.extensiv_receiver_dct.items():

                # Prepare normalized strings for extensiv data
                extensiv_address = (str(extensiv_receiver["Receiver Address"]).lower().strip())  # fmt:skip
                extensiv_name = str(extensiv_receiver["Receiver Name"]).lower().strip()  # fmt:skip
                extensiv_company = (str(extensiv_receiver["Receiver Company"]).lower().strip())  # fmt:skip

                # Calculate fuzzy scores
                address_score = fuzz.token_set_ratio(fedex_address, extensiv_address)
                name_score = fuzz.token_set_ratio(fedex_name, extensiv_name)
                company_score = fuzz.token_set_ratio(fedex_company, extensiv_company)

                # Check if all scores exceed the threshold
                if (
                    address_score > FUZZY_SCORE
                    and name_score > FUZZY_SCORE
                    and company_score > FUZZY_SCORE
                ):
                    match_entry = {
                        "Address": fedex_receiver["Receiver Address"],
                        "Name": fedex_receiver["Receiver Name"],
                        "Company": fedex_receiver["Receiver Company"],
                        "Customer": self.name,
                    }

                    # Add to match list if unique
                    if match_entry not in match_lst:
                        self.append_match(receiver_match=match_entry)
                        match_lst.append(match_entry)

        return match_lst


def make_final_df(
    reference_matches: list[dict[str, str]],
    receiver_matches: list[dict[str, str]],
    fedex_invoice: DataFrame,
) -> DataFrame:
    """
    Makes new DataFrame of records with [Customer PO #]'s not found in QBO, with the [Customer PO #]
    replaced by the customer name, if a match was found in Extensiv through [Reference] or [Receiver Name],
    [Receiver Company], or [Receiver Address].

    :param reference_matches: List of dictionaries of references found in Extensiv table with respective customer name
    :param receiver_matches: List of dictionaries of receiver information found in Extensiv table with respective customer name
    :param fedex_invoice: DataFrame with records whose [Customer PO #] was not found in Quickbooks
    :return final_df: DataFrame with [Customer PO #]'s replaced with customer name if match found in Extensiv table
    """

    # Add reference and receiver information into master list
    final_matches_lst = []
    final_matches_lst.extend(reference_matches)
    final_matches_lst.extend(receiver_matches)

    # Iterate through FedEx invoice
    for i, row in fedex_invoice.iterrows():

        fedex_reference = str(row["Reference"]).lower().strip()
        fedex_receiver_address = str(row["Receiver Address"]).lower().strip()
        fedex_receiver_name = str(row["Receiver Name"]).lower().strip()
        fedex_receiver_company = str(row["Receiver Company"]).lower().strip()

        # Iterate through each dictionary in master list
        for dct in final_matches_lst:

            extensiv_reference = str(dct["Reference"]).lower().strip() \
                                     if "Reference" in dct else None  # fmt:skip

            extensiv_receiver_address = str(dct["Address"]).lower().strip() \
                                     if "Address" in dct else None  # fmt:skip

            extensiv_receiver_name = str(dct["Name"]).lower().strip() \
                                     if " Name" in dct else None  # fmt:skip

            extensiv_receiver_company = str(dct["Company"]).lower().strip() \
                                     if "Company" in dct else None  # fmt:skip

            # Replace [Customer PO #] with customer name if match is found in Extensiv
            if "Reference" in dct and extensiv_reference == fedex_reference:

                fedex_invoice.loc[i, "Customer PO #"] = dct["Customer"]

            elif ("Address" in dct and extensiv_receiver_address == fedex_receiver_address):  # fmt:skip

                fedex_invoice.loc[i, "Customer PO #"] = dct["Customer"]

            elif "Name" in dct and extensiv_receiver_name == fedex_receiver_name:

                fedex_invoice.loc[i, "Customer PO #"] = dct["Customer"]

            elif ("Company" in dct and extensiv_receiver_company == fedex_receiver_company):  # fmt:skip

                fedex_invoice.loc[i, "Customer PO #"] = dct["Customer"]

    # Drop RegEx column from final_df
    final_df = fedex_invoice.drop(columns=["Pattern"])

    return final_df
