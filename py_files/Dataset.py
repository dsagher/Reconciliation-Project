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
        self.match_lst = []
        self.counter = 0

    def get_shape(self, dataset: pd.DataFrame):
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

    def set_pattern_matches(self, match_dct):
        self._matches = match_dct

    def get_pattern_match_dct(self):
        return self._matches

    def get_pattern_match_ref(self):
        return list(self._matches.keys())

    def append_match(self, match):
        self.match_lst.append(match)

    def count_match(self):
        self.counter += 1

    def get_match_count(self):
        return self.counter

    def get_matches(self):
        return self.match_lst
