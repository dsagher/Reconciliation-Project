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
            - typing
        Internal:
            - None
            
=========================================================================================="""

from re import Pattern, sub, compile, fullmatch
from pandas import DataFrame, Series, merge, isna, concat
from rapidfuzz import fuzz
from typing import NoReturn


class FindCustomerPO:

    def __init__(self, qbo: DataFrame, fedex_invoice: DataFrame):

        self.qbo: DataFrame = qbo
        self.fedex_invoice: DataFrame = fedex_invoice

        # Raise error if inputs to class are not DataFrames
        try:
            if not (
                isinstance(self.qbo, DataFrame)
                and isinstance(self.fedex_invoice, DataFrame)
            ):
                raise TypeError("Both tables must be DataFrames")
        except TypeError as e:
            print(f"Error {e}")

    def compare_qbo(
        self, qbo_key_lst: list, fedex_key: str = "Customer PO #"
    ) -> DataFrame:
        """
        compare_qbo() Compares FedEx invoice with QuickBooks via keys [Customer PO #] and [Display_Name], respectively.

        :param qbo_key_lst: List of keys in QBO dataset to search for matches
        :param fedex_invoice: Fedex key to look for in QBO. Default is "Customer PO #"
        :return qbo_found: Pandas DataFrame with records found in QBO
        :return qbo_not_found: Pandas DataFrame with records not found in QBO
        """
        # Merge qbo and fedex_invoice DataFrames based on list of QBO keys and one FedEx key (Customer PO #)
        qbo_found: DataFrame = DataFrame()

        for qbo_key in qbo_key_lst:
            merged_df: DataFrame = merge(
                self.qbo,
                self.fedex_invoice,
                left_on=qbo_key,
                right_on=fedex_key,
                how="inner",
            )

            qbo_found = concat(
                [qbo_found, merged_df], ignore_index=True
            ).drop_duplicates(ignore_index=True)

        # Only include columns from fedex_invoice in merged dataset
        fedex_columns: list = list(self.fedex_invoice.columns)
        qbo_found = qbo_found[fedex_columns]

        # Create sets of found and not found references
        self.found_references_unique: set = set(qbo_found["Customer PO #"].unique())
        self.all_references_unique: set = set(self.fedex_invoice["Customer PO #"])
        self.unmatched_references: set = (self.all_references_unique - self.found_references_unique)  # fmt: skip

        # Create new DataFrame with only unique unmatched_references
        qbo_not_found: DataFrame = DataFrame(list(self.unmatched_references), columns=["Customer PO #"])  # fmt:skip

        #! This maybe should be an inner merge
        # Merge with fedex invoice
        qbo_not_found: DataFrame = qbo_not_found.merge(
            self.fedex_invoice,
            on="Customer PO #",
            how="left",
        )

        return (qbo_found, qbo_not_found)


class FindPatternMatches:

    def __init__(self, name: str, extensiv_table: DataFrame, fedex_invoice: DataFrame):

        self.name: str = name
        self.extensiv_table: DataFrame = extensiv_table
        self.fedex_invoice: DataFrame = fedex_invoice

        # For output of stats during runtime
        self.receiver_matches: list = list()
        self.reference_matches: list = list()

        # Raise error if datasets inputted during class instantiation are not DataFrames
        try:
            if not (
                isinstance(self.extensiv_table, DataFrame)
                and isinstance(self.fedex_invoice, DataFrame)
            ):
                raise TypeError("Both tables must be DataFrames")
        except TypeError as e:
            print(f"Error {e}")

    # Called during comparisons for output of stats during runtime
    def append_match(
        self, reference_match: str = None, receiver_match: str = None
    ) -> NoReturn:

        if receiver_match is not None:
            self.receiver_matches.append(receiver_match)

        if reference_match is not None:
            self.reference_matches.append(reference_match)

    # Printing of stats during runtime
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
        """Called during compare_qbo() to create [Pattern] column in FedEx Invoice"""

        # Add pattern tokens to FedEx invoice table in a new column called "Reference"
        with_letters: str = sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers: str = sub(r"\d+(\.\d+)?", r"\\d+(\\.\\d+)?", with_letters)
        with_spaces: str = sub(r"\s+", r"\\s+", with_numbers)

        final: Pattern = compile(with_spaces)

        return final

    def __find_matching_columns(self, reference_pattern: Series,) -> set[str]:  # fmt:skip
        """
        Private method called in __find_extensiv_reference_columns() to use to iterate over each [Reference] pattern.

        :param reference_pattern: RegEx pattern of current [Reference] in iteration
        :const SAMPLE_SIZE: number of records to search through in Extensiv table to find a pattern match. Default is 25
        :return columns: a unique set of columns in the Extensiv table with a matching pattern to current [Reference]

        Special Concerns:
            - Search loop breaks when *one* match is found in each Extensiv column, and only searches
              up to 25 cells per column. If there are pattern matches beyond the 25th record, they will
              be missed. This is a performance saving measure. Future iterations with multiprocessing
              can check more values in Extensiv columns.
        """
        SAMPLE_SIZE: int = 25
        columns: set = set()

        # Iterate through each column in Extensiv table
        for column in self.extensiv_table.columns:

            # Iterate through the first 25 values of each column
            for value in self.extensiv_table[column][:SAMPLE_SIZE]:

                # If match of the current reference RegEx pattern, add to set
                if fullmatch(reference_pattern, str(value)):

                    # Break after first match
                    columns.add(column.strip())
                    break

        if columns:
            return columns

    #! This might not need an argument
    def __find_extensiv_reference_columns(
        self, reference_column_name
    ) -> dict[str, set]:
        """
        Subfunction called in compare_references() that iterates through each [Reference] and calls __find_matching_columns()
        for each reference.

        :param reference_column_name: Column in FedEx Invoice to be compared against values in Extensiv
        :return match_dct: Dictionary of dictionaries. Outer dictionary key are References, values
         are sets of columns with matching RegEx patterns.
        """

        match_dct: dict = dict()

        # todo Could just iterate through each of the patterns instead of iterating through the reference first
        # Iterate through Reference column in fedex_invoice
        for i, v in enumerate(self.fedex_invoice[reference_column_name]):

            # Call column matcher function on each value in reference column
            pattern = self.fedex_invoice[self.reference_pattern_column][i]
            cols = self.__find_matching_columns(pattern)

            # Add match list to dictionary
            if cols is not None and not isna(v):
                match_dct[str(v)] = cols

        return match_dct

    def compare_references(self, reference_column_name: str) -> list[dict[str, str]]:  # fmt:skip
        """
        Function called in main.py that compares each value of a column (specified in main.py)
        in the FedEx invoice (by exact match and fuzzy match) with every value in the selected columns
        (matched by RegEx) until a match is found.

        :param reference_column_name: Column in FedEx Invoice to be compared against values in Extensiv
        :return match_lst: list of dictionaries containing the [Reference], [Column], and [Customer] of matched reference
        """

        FUZZY_SCORE: int = 75
        match_lst: list = list()
        unique_references: set = set()

        self.reference_pattern_column: str = reference_column_name + "_Pattern"
        self.fedex_invoice[self.reference_pattern_column] = self.fedex_invoice[
                                reference_column_name].apply(self.__reg_tokenizer)  # fmt:skip

        reference_columns: dict = self.__find_extensiv_reference_columns(
            reference_column_name
        )

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

        # Drop [Pattern] column
        self.fedex_invoice = self.fedex_invoice.drop(
            columns=[self.reference_pattern_column]
        )

        return match_lst

    def __create_extensiv_receiver_info(self) -> NoReturn:
        """Private method to create Extensiv receiver information dictionaries for comparison"""

        # Extract receiver information from Extensiv DataFrame and drop duplicates
        extensiv_receiver_info = self.extensiv_table.drop_duplicates(
            [
                "ShipTo.CompanyName",
                "ShipTo.Name",
                "ShipTo.Address1",
            ]
        )

        self.extensiv_receiver_lst: list = []

        for _, row in extensiv_receiver_info.iterrows():

            entry = {
                "Receiver Address": row["ShipTo.Address1"],
                "Receiver Company": row["ShipTo.CompanyName"],
                "Receiver Name": row["ShipTo.Name"],
            }
            self.extensiv_receiver_lst.append(entry)

    def __create_fedex_invoice_receiver_info(self) -> NoReturn:
        """Private method to create FedEx Invoice receiver information dictionaries for comparison"""

        # Extract receiver information from FedEx Invoice DataFrame and drop duplicates
        fedex_invoice_info = self.fedex_invoice.drop_duplicates(
            ["Receiver Address", "Receiver Company", "Receiver Name"]
        )

        self.fedex_invoice_receiver_lst: list = []

        for _, row in fedex_invoice_info.iterrows():
            entry = {
                "Receiver Address": row["Receiver Address"],
                "Receiver Company": row["Receiver Company"],
                "Receiver Name": row["Receiver Name"],
            }

            self.fedex_invoice_receiver_lst.append(entry)

    def compare_receiver_info(self) -> list[dict[str, str]]:
        """
        Compares the receiver information ([Receiver Address], [Receiver Name], [Receiver Company]) using fuzzy matching,
        of the Extensiv DataFrame to that of the FedEx Invoice DataFrame.

        :return match_lst: List of Dictionaries containing receiver information and customer name of matched values

        Notes:
            - All three receiver information categories must exceed a fuzzy score of 70 to be matched
            - fuzzy function token_set_ratio() is used - compares strings based on common words
        """

        FUZZY_SCORE: int = 70
        match_lst: list = []

        self.__create_extensiv_receiver_info()
        self.__create_fedex_invoice_receiver_info()

        # Iterate through FedEx invoice receiver info
        for fedex_receiver in self.fedex_invoice_receiver_lst:

            # Prepare normalized strings for FedEx invoice data
            fedex_address: str = str(fedex_receiver["Receiver Address"]).lower().strip()
            fedex_name: str = str(fedex_receiver["Receiver Name"]).lower().strip()
            fedex_company: str = str(fedex_receiver["Receiver Company"]).lower().strip()

            # Iterate through extensiv receiver info
            for extensiv_receiver in self.extensiv_receiver_lst:
                # Prepare normalized strings for extensiv data
                extensiv_address: str = (str(extensiv_receiver["Receiver Address"]).lower().strip())  # fmt:skip
                extensiv_name: str = str(extensiv_receiver["Receiver Name"]).lower().strip()  # fmt:skip
                extensiv_company: str = (str(extensiv_receiver["Receiver Company"]).lower().strip())  # fmt:skip

                # Calculate fuzzy scores
                address_score: int = fuzz.token_set_ratio(fedex_address, extensiv_address)  # fmt:skip
                name_score: int = fuzz.token_set_ratio(fedex_name, extensiv_name)  # fmt:skip
                company_score: int = fuzz.token_set_ratio(fedex_company, extensiv_company)  # fmt:skip

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

    Notes:
        - Not a part of any class. Gets called in main.py after all comparisons have been made.
    """
    final_df: DataFrame = fedex_invoice

    # Add reference and receiver information into master list
    final_matches_lst: list = []
    final_matches_lst.extend(reference_matches)
    final_matches_lst.extend(receiver_matches)

    # Iterate through FedEx invoice
    for i, row in final_df.iterrows():

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

                final_df.loc[i, "Customer PO #"] = dct["Customer"]

            elif ("Address" in dct and extensiv_receiver_address == fedex_receiver_address):  # fmt:skip

                final_df.loc[i, "Customer PO #"] = dct["Customer"]

            elif "Name" in dct and extensiv_receiver_name == fedex_receiver_name:

                final_df.loc[i, "Customer PO #"] = dct["Customer"]

            elif ("Company" in dct and extensiv_receiver_company == fedex_receiver_company):  # fmt:skip

                final_df.loc[i, "Customer PO #"] = dct["Customer"]

    return final_df


if __name__ == "__main__":
    pass
