import numpy as np
import pandas as pd

from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp


class TypeColExtracter:

    @staticmethod
    def extract_num_cols(df_data, df_profiles):#, adjacent=False):
        """

        :param df_data:
        :param df_profiles:
        :return df_num:

        This function looks for columns in df_data with mainly numeric entries and packs these in df_num. Non-numeric
        entries in seemingly numeric columns are replaced with zeros.
        """
        #num_headers = list()
        nrows = df_profiles.shape[0]
        float_sum = (df_profiles == SheetTypeDefinitions.FLOAT).sum()
        zero_float_sum = np.logical_or(df_profiles == SheetTypeDefinitions.ZERO_FLOAT, df_profiles == SheetTypeDefinitions.EMPTY_STRING).sum()
        #zero_float_sum = (df_profiles == SheetTypeDefinitions.ZERO_FLOAT).sum()
        bool_modifier = np.logical_or(float_sum != 0, zero_float_sum >= nrows -2)
        type_sum = (float_sum + zero_float_sum) * bool_modifier

        new_headers = (type_sum/nrows) > pp.MIN_NUM_RATIO_NUM_COL
        # Make a new DataFrame with only floats
        vals = df_data[new_headers.index[new_headers]].copy().values
        vals[df_profiles[new_headers.index[new_headers]].values != SheetTypeDefinitions.FLOAT] = 0
        vals = vals.astype(np.float64, copy=False)
        df_num = pd.DataFrame(vals, columns=new_headers.index[new_headers], index=df_data.index)

        return df_num

    @staticmethod
    def extract_string_cols(ds):
        string_cols = pd.Series(False, index=ds.df_profiles.columns)
        for name, col in ds.df_profiles.iteritems():
            #gen_col_ratio = (np.sum(col.values == SheetTypeDefinitions.STRING) + np.sum(col.values == SheetTypeDefinitions.EMPTY_STRING))/col.size
            col_ratio = np.sum(col.values == SheetTypeDefinitions.STRING)/ col.size
            if col_ratio > pp.MIN_STRING_RATIO_STRING_COL:
                string_cols[name] = True

        # get the columns
        df_string = ds.df_data[string_cols.index[string_cols]]
        return df_string