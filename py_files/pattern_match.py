"""==========================================================================================
    
    File: pattern_match.py
    Author: Dan Sagher
    Date: 12/25/24
    Description:  
        Defines the PatternMatch class and methods for matching references and receiver details  
        in Extensiv tables.  

    Dependencies:
        External:
            - re
            - pandas
            - rapidfuzz
            - typing
        Internal:
            - None
            
=========================================================================================="""

from re import Pattern, sub, compile, fullmatch
from pandas import DataFrame, Series, merge, isna, concat
from rapidfuzz import fuzz
from typing import Optional, Any


class FindCustomerPO:
    """
    A class for comparing FedEx invoice data with QuickBooks (QBO) data
    based on customer purchase order numbers.
    """

    def __init__(self, qbo: DataFrame, fedex_invoice: DataFrame):
        """
        Initializes the FindCustomerPO class with QBO and FedEx invoice DataFrames.

        :param qbo: DataFrame containing QuickBooks data.
        :param fedex_invoice: DataFrame containing FedEx invoice data.
        """
        self.qbo: DataFrame = qbo
        self.fedex_invoice: DataFrame = fedex_invoice

        # Raise error if inputs to class are not DataFrames

        if not (
            isinstance(self.qbo, DataFrame)
            and isinstance(self.fedex_invoice, DataFrame)
        ):
            raise TypeError("Both tables must be DataFrames")

    def compare_qbo(
        self, qbo_key_lst: list, fedex_key: str = "Customer PO #"
    ) -> tuple[DataFrame, DataFrame]:
        """
        Compares FedEx invoice data with QuickBooks using specified key columns.

        :param qbo_key_lst: List of column names in the QBO dataset to search for matches.
        :param fedex_key: Column name in the FedEx dataset to match against QBO. Default is "Customer PO #".
        :return: A tuple containing two DataFrames:
                 - qbo_found: Records found in QBO.
                 - qbo_not_found: Records not found in QBO.
        """
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

        # Merge with fedex invoice
        qbo_not_found = qbo_not_found.merge(
            self.fedex_invoice,
            on="Customer PO #",
            how="left",
        )

        return (qbo_found, qbo_not_found)


class FindPatternMatches:
    """
    A class for identifying and analyzing pattern matches between Extensiv tables and FedEx invoices.
    """

    def __init__(self, name: str, extensiv_table: DataFrame, fedex_invoice: DataFrame):
        """
        Initializes the FindPatternMatches class.

        :param name: Customer name.
        :param extensiv_table: DataFrame containing Extensiv data.
        :param fedex_invoice: DataFrame containing FedEx invoice data.
        """
        self.name: str = name
        self.extensiv_table: DataFrame = extensiv_table
        self.fedex_invoice: DataFrame = fedex_invoice

        # For output of stats during runtime
        self.receiver_matches: list = list()
        self.reference_matches: list = list()

        if not (
            isinstance(self.extensiv_table, DataFrame)
            and isinstance(self.fedex_invoice, DataFrame)
        ):
            raise TypeError("Both tables must be DataFrames")

    def append_match(
        self,
        reference_match: str | None = None,
        receiver_match: dict[str, Any] | None = None,
    ):
        """
        Stores matched reference and receiver information during comparisons.

        :param reference_match: Matched reference value (optional).
        :param receiver_match: Matched receiver value (optional).
        """

        if receiver_match:
            self.receiver_matches.append(receiver_match)

        if reference_match:
            self.reference_matches.append(reference_match)

    # Printing of stats during runtime
    def __str__(self) -> str:
        """
        Returns a formatted string summary of pattern matching results.
        """
        return (
            f"\n"
            f"Customer: {self.name}\n"
            f"{'-' * 70 }\n"
            f"Unique # of Reference Matches in Extensiv: {len(self.reference_matches)}\n"
            f"Reference Matches in Extensiv: {', \n'.join(map(str,self.reference_matches)) if self.reference_matches else None}\n"
            f"{'-' * 70 }\n"
            f"Unique # of Receiver Matches in Extensiv: {len(self.receiver_matches)}\n"
            f"Receiver Matches in Extensiv: {', \n'.join(map(str,self.receiver_matches)) if self.receiver_matches else None}\n"
            f"{'-' * 70 }\n"
        )

    def __reg_tokenizer(self, value: str) -> Pattern:
        """
        Converts a string value into a regex pattern for reference matching.

        :param value: Input string to convert.
        :return: Compiled regex pattern.
        """
        with_letters: str = sub(r"[a-zA-Z]+", r"\\w+", str(value))
        with_numbers: str = sub(r"\d+(\.\d+)?", r"\\d+(\\.\\d+)?", with_letters)
        with_spaces: str = sub(r"\s+", r"\\s+", with_numbers)

        final: Pattern = compile(with_spaces)
        return final

    def __find_matching_columns(self, reference_pattern: Series,) -> Optional[set[str]]:  # fmt:skip
        """
        Identifies columns in the Extensiv table that contain values matching a given reference pattern.

        :param reference_pattern: Regular expression pattern to search for in Extensiv table columns.
        :return: A set of column names that contain at least one match to the reference pattern.

        Notes:
            - The search is limited to the first 25 records in each column for performance reasons.
            - Future iterations may implement multiprocessing to extend the search range.
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

    def __find_extensiv_reference_columns(
        self, reference_column_name: str
    ) -> dict[str, set]:
        """
        Finds matching columns in the Extensiv table for each reference in a given FedEx invoice column.

        :param reference_column_name: Column in the FedEx Invoice to compare against Extensiv values.
        :return: A dictionary where keys are reference values, and values are sets of matching Extensiv columns.
        """
        match_dct: dict = dict()

        # Iterate through Reference column in fedex_invoice
        for i, v in enumerate(self.fedex_invoice[reference_column_name]):

            pattern = self.fedex_invoice[self.reference_pattern_column][i]
            cols = self.__find_matching_columns(pattern)

            if cols is not None and not isna(v):
                match_dct[str(v)] = cols

        return match_dct

    def compare_references(self, reference_column_lst: list) -> list[dict[str, str]]:  # fmt:skip
        """
        Compares reference values from the FedEx invoice against values in matched Extensiv table columns.

        :param reference_column_lst: List of FedEx Invoice columns to compare against Extensiv data.
        :return: A list of dictionaries containing matched reference details.

        Notes:
            - Performs both exact and fuzzy matching.
            - Matches are stored in a list of dictionaries with Reference, Column, and Customer information.
        """

        FUZZY_SCORE: int = 75
        match_lst: list = list()
        unique_references: set = set()

        # Iterate through each reference column in argument list
        for reference_column in reference_column_lst:

            self.reference_pattern_column: str = reference_column + "_Pattern"
            self.fedex_invoice[self.reference_pattern_column] = self.fedex_invoice[
                                    reference_column].apply(self.__reg_tokenizer)  # fmt:skip

            reference_columns: dict = self.__find_extensiv_reference_columns(
                reference_column
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
                columns=self.reference_pattern_column
            )

        return match_lst

    def __create_extensiv_receiver_info(self):
        """Extracts unique receiver information from the Extensiv table for comparison."""
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

    def __create_fedex_invoice_receiver_info(self):
        """Extracts unique receiver information from the FedEx Invoice for comparison."""
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
        Performs fuzzy matching to compare receiver details between the Extensiv and FedEx Invoice datasets.

        :return: A list of dictionaries containing matched receiver details and customer name.

        Notes:
            - Uses token_set_ratio for fuzzy matching.
            - All three receiver fields must exceed a fuzzy score of 70 for a match.
        """

        FUZZY_SCORE: float = 70.0
        match_lst: list = []

        self.__create_extensiv_receiver_info()
        self.__create_fedex_invoice_receiver_info()

        for fedex_receiver in self.fedex_invoice_receiver_lst:
            fedex_address: str = str(fedex_receiver["Receiver Address"]).lower().strip()
            fedex_name: str = str(fedex_receiver["Receiver Name"]).lower().strip()
            fedex_company: str = str(fedex_receiver["Receiver Company"]).lower().strip()

            for extensiv_receiver in self.extensiv_receiver_lst:
                extensiv_address: str = (str(extensiv_receiver["Receiver Address"]).lower().strip())  # fmt:skip
                extensiv_name: str = str(extensiv_receiver["Receiver Name"]).lower().strip()  # fmt:skip
                extensiv_company: str = (str(extensiv_receiver["Receiver Company"]).lower().strip())  # fmt:skip

                address_score: float = fuzz.token_set_ratio(fedex_address, extensiv_address)  # fmt:skip
                name_score: float = fuzz.token_set_ratio(fedex_name, extensiv_name)  # fmt:skip
                company_score: float = fuzz.token_set_ratio(fedex_company, extensiv_company)  # fmt:skip

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
    Updates the [Customer PO #] in fedex_invoice with the customer name if a match is found in Extensiv.

    :param reference_matches: List of dictionaries with references found in Extensiv table.
    :param receiver_matches: List of dictionaries with receiver information found in Extensiv table.
    :param fedex_invoice: DataFrame with records where [Customer PO #] was not found in QuickBooks.
    :return: Updated DataFrame with replaced [Customer PO #] values if a match is found.
    """
    final_df: DataFrame = fedex_invoice.copy()

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
