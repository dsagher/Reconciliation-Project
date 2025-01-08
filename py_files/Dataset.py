import pandas as pd


class Dataset:
    """
    This class is supposed to capture facts about the dataset through the pattern match process.
    This will be helpful in debugging, and displaying outputs to user.
    """

    def __init__(self, name, original_dataset=None):
        self.name = name
        self.original_dataset = original_dataset
        self._row_num = 0
        self._column_num = 0
        self.reference_match_lst = []
        self.receiver_match_lst = []
        self.reference_counter = 0
        self.final_match_count = 0
        self.receiver_counter = 0
        self.final_counter = 0

    def set_shape(self, dataset: pd.DataFrame):
        self._row_num = dataset.shape[0]
        self._column_num = dataset.shape[1]

    @property
    def row_num(self):

        if self._row_num == 0:
            print("Row number not intialized")
            return None
        else:
            return self._row_num

    @property
    def column_num(self):

        if self._column_num == 0:
            print("Column number not intialized")
            return None
        else:
            return self._column_num

    @property
    def row_diff(self):
        return len(self.original_dataset) - self.row_num

    def get_name(self):
        return self.name

    def set_pattern_matches(self, match_dct):
        self._matches = match_dct

    def get_pattern_match_dct(self):
        return self._matches

    def get_pattern_match_ref(self):
        return list(self._matches.keys())

    def append_reference_match(self, match):
        self.reference_match_lst.append(match)

    def count_reference_match(self):
        self.reference_counter += 1

    def get_reference_match_count(self):
        return self.reference_counter

    def get_reference_matches(self):
        return self.reference_match_lst

    def count_receiver_match(self):
        self.receiver_counter += 1

    def get_receiver_match_count(self):
        return self.receiver_counter

    def append_receiver_match(self, value):
        self.receiver_match_lst.append(value)

    def get_receiver_matches(self):
        return self.receiver_match_lst

    def get_customer_match_count(self):
        return self.receiver_counter + self.reference_counter

    def count_final_matches(self):
        self.final_counter += 1

    def get_final_count(self):
        return self.final_counter
