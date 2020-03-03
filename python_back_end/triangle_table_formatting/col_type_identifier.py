import numpy as np
import pandas as pd

from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.utilities.performance_utils import effectiveSampleSize
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier


class ColTypeIdentifier:

    @staticmethod
    def identify_col_types(dh):
        for ds in dh:
            # collect the date set
            d_cols = DateColIdentifier.identify_marked_date_cols(ds)
            d_set = set()
            for name in d_cols.index[d_cols]:
                d_set.update(ds.df_data[name].values)
            # get non-date cols:
            to_be_assigned = np.logical_not(d_cols)

            rem_data, rem_profiles = ds.df_data[to_be_assigned.index[to_be_assigned]], ds.df_profiles[to_be_assigned.index[to_be_assigned]]

            # detect interesting number columns
            df_num = TypeColExtracter.extract_num_cols(rem_data, rem_profiles)
            # check effective sample size (cannot be too low)
            for name, col in df_num.iteritems():
                if np.std(col.values) > 0 and "#" not in name:
                    ess = effectiveSampleSize(col.values)
                    ratio = ess/len(col.values)
                    if ratio > pp.MIN_ESS_RATIO_VALUE_COL:
                        to_be_assigned[name] = False
                        ds.df_profiles[name] = SheetTypeDefinitions.TRIANGLE_ELEMENT
                        ds.df_data[name] = df_num[name].values

            # Now do potential id_cols
            rem_data = rem_data[to_be_assigned.index[to_be_assigned]]
            unique_dict = {key: np.unique(col.values.astype(str), return_counts=True) for key, col in rem_data.iteritems()}
            dist_dict = {key: np.abs(np.mean(val[1])-(len(d_set)/2)) for key, val in unique_dict.items()}
            # std_dict = {key: np.std(val[1]) for key, val in unique_dict.items()}
            unique_series = pd.Series(list(dist_dict.values()), index=dist_dict.keys())
            #min_name = unique_series.idxmin()
            #std = np.std(unique_dict[min_name][1])
            id_cols = unique_series < len(d_set)

            for name in id_cols.index[id_cols]:
                ds.df_profiles[name] = SheetTypeDefinitions.ID_ELEMENT

        return dh


