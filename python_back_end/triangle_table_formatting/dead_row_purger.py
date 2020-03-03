from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
import numpy as np

class DeadRowPurger:

    @staticmethod
    def purge_dead_rows(dh):
        for ds in dh:
            removal_list = list()
            for i in range(ds.df_data.shape[0]):
                prof_row = ds.df_profiles.iloc[i, :]
                data_row = ds.df_data.iloc[i, :]
                tr_data = data_row[prof_row == SheetTypeDefinitions.TRIANGLE_ELEMENT]
                if tr_data.sum() == 0:
                    date_data = data_row[prof_row == SheetTypeDefinitions.STRING_DATE]
                    match = np.array([DateColIdentifier.match(el) for el in date_data])
                    if np.all(match != 1):
                        removal_list.append(i)
            ds.df_data.drop(ds.df_data.index[removal_list], inplace=True)
            ds.df_profiles.drop(ds.df_profiles.index[removal_list], inplace=True)
        return dh


