from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.utilities.help_functions import longest_numeral
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.definitions import SheetTypeDefinitions
import pandas as pd
import numpy as np

class DateNumifyer:

    @staticmethod
    def numify_dates(dh):
        meta_dh = DataHolder(dh.name + "_meta")
        for ds in dh:
            d_cols = DateColIdentifier.identify_marked_date_cols(ds)
            date_data = ds.df_data[d_cols.index[d_cols]]

            meta_data = pd.DataFrame()
            meta_profiles = pd.DataFrame()
            for name, col in date_data.iteritems():
                ds.df_profiles.loc[:, name] = SheetTypeDefinitions.STRING_DATE
                types = col.map(lambda x: isinstance(x, float))
                if types.all():
                    #do nothing basically
                    ds.df_data[name] = col.astype(int)
                else:
                    meta_data[name] = col.copy()
                    meta_profiles[name] = ds.df_profiles[name].copy()
                    temp_col = col.copy()
                    temp_col[types] = temp_col[types]
                    #SOME PROBLEM WITH KEEPING TYEPS INT IN SHEET W
                    temp_col[np.logical_not(types)] = temp_col[np.logical_not(types)].map(lambda x: longest_numeral(x))
                    temp_col = temp_col.astype(int)
                    ds.df_data[name] = temp_col
                # meta_backed = False
                # for index, val in col.iteritems():
                #     if not isinstance(val, int):
                #         if not meta_backed:
                #             meta_backed = True
                #             meta_data[name] = col.copy()
                #             meta_profiles[name] = ds.df_profiles[name].copy()
                #         num = longest_numeral(val)
                #         ds.df_data.loc[index, name] = num
                    meta_dh.add_sheet("date_backup", meta_data, meta_profiles, orig_sheet_name=ds.orig_sheet_name)
            return dh, meta_dh




