from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.exceptions import UnknownColForSortingException, DummyColForSortingException
import numpy as np
import re


class DateSorter:
    """
    This class finds all date columns, checks if they are sorted the same and sorts accordingly (vague).
    """

    @staticmethod
    def sort_by_date(dh):
        try:
            for ds in dh:
                DateSorter.sort_ds_by_dates(ds)
        except DummyColForSortingException:
            raise UnknownColForSortingException(dh)
        return dh


    @staticmethod
    def sort_ds_by_dates(ds):
        cols, mat = DateColIdentifier.identify_date_cols(ds)
        cols = DateSorter.prune_non_sortable(cols)
        # if no date cols, do nothing
        if cols.sum() == 1:
            # easy case, check if sorted
            DateSorter.sort_by_col(ds, mat, cols.index[cols][0])
        elif cols.sum() > 1:
            # First check if there is a tie
            cols_sums = (mat == 1).sum()
            max_true = cols_sums == np.max(cols_sums)
            if max_true.sum() == 1:
                # easy case again
                DateSorter.sort_by_col(ds, mat, max_true.index[max_true][0])
            if max_true.sum() > 1:
                # Do some funky shit
                tup_array = [DateSorter.is_sorted(ds, mat, name) for name in max_true.index[max_true]]
                neq_bool_array = np.array([not tup[0] for tup in tup_array])
                if np.all(neq_bool_array):
                    raise DummyColForSortingException

    @staticmethod
    def prune_non_sortable(cols):
        #TODO: write prune non-sortable function, for now, accept bsp6
        return cols

    @staticmethod
    def sort_by_col(ds, mat, col_name):
        boolean, sorting_col = DateSorter.is_sorted(ds, mat, col_name)
        if not boolean:
            # do the magic
            ds.df_data = DateSorter.append_and_sort(ds.df_data, sorting_col)
            ds.df_profiles = DateSorter.append_and_sort(ds.df_profiles, sorting_col)


    @staticmethod
    def append_and_sort(df, col):
        df = df.copy()
        df["sorter"] = col.copy()
        df["temp_index"] = df.index.copy()
        df = df.sort_values(["sorter", "temp_index"])
        del df['sorter']
        del df['temp_index']
        return df

    @staticmethod
    def is_sorted(ds, mat, col_name):
        sorting_col = ds.df_data[col_name].copy().astype(str)
        sorting_col[mat[col_name].values != 1] = ""
        # do not attempt to sort textual dates
        # check 5 first entries
        head = sorting_col.values[0:5]
        l = [re.search("[^0-9.]", string) for string in head]
        if not all(v is None for v in l):
            # assumed non-sortable format
            return True, sorting_col
        sorted = sorting_col.sort_values()
        return sorted.equals(sorting_col), sorting_col