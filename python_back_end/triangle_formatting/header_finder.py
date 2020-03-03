from python_back_end.data_cleaning.cleaning_utils import HeaderFinder
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.utilities.help_functions import longest_numeral, strict_index
from python_back_end.utilities.state_handling import DataStruct, DataHolder
from python_back_end.definitions import SheetTypeDefinitions
import numpy as np


class TriangleHeaderFinder:

    @staticmethod
    def find_triangle_headers(dh, **kwargs):
        test_settings = False
        if 'test_settings' in kwargs:
            test_settings = kwargs['test_settings']
        return_meta = False
        meta_dh = DataHolder(dh.name + "_meta")
        if 'return_meta' in kwargs:
            return_meta = kwargs["return_meta"]

        for ds in dh.data_struct_list:
            # only do this for potential triangles:
            if ds.df_data.shape[0] >= pp.MIN_ROWS_TRIANGLE or test_settings:
                headers, pd_ind = TriangleHeaderFinder.find_ds_headers(ds)
                HeaderFinder.insert_headers(headers, pd_ind, ds.df_data, ds.df_profiles)
                ds.df_data = ds.df_data.reindex(sorted(ds.df_data.columns), axis=1)
                ds.df_profiles = ds.df_profiles.reindex(sorted(ds.df_profiles.columns), axis=1)
                # now remove unnecessary rows
                ds = TriangleHeaderFinder.remove_stray_rows(ds, pd_ind)
                if return_meta and ds is not None:
                    for split in ds.col_split_ds():
                        if not np.all(split.df_profiles == SheetTypeDefinitions.EMPTY_STRING) and not (np.all(split.df_data == "")):
                            meta_dh.add_ds(split)
        if return_meta:
            return dh, meta_dh
        else:
            return dh

    @staticmethod
    def find_ds_headers(ds):
        df_data, df_profiles = ds.df_data, ds.df_profiles
        if df_data.size == 0:
            return [], 0
        # Only check top n rows for header
        #outtake = df_data.iloc[:pp.N_POSSIBLE_HEADER_ROWS, ]
        pd_ind, monotonicity, counter = df_data.index[0], 0, 0
        for ind, row in df_data.iterrows():
            counter += 1
            int_list = np.array([longest_numeral(el) for el in row])
            increments = int_list[1:] - int_list[0:-1]
            unique, counts = np.unique(increments, return_counts=True)
            # ignore zero increment
            if 0 in unique:
                counts = counts[unique != 0]
            date_matches = np.array([DateColIdentifier.match(el) == 1 for el in row]).sum()/len(int_list)
            if len(counts) > 0:

                temp = np.max(counts)/len(int_list) + date_matches
            else:
                temp = date_matches
            if temp > monotonicity:
                monotonicity = temp
                pd_ind = ind
            if counter > pp.N_POSSIBLE_HEADER_ROWS and monotonicity > 0.1:
                break
        headers = df_data.loc[[pd_ind]]
        return headers, pd_ind

    @staticmethod
    def remove_stray_rows(ds, h_ind):

        # save the junk as meta-data
        leading = []
        for ind in ds.df_data.index:
            if ind > h_ind:
                break
            leading.append(ind)
        if leading:
            df_data_meta = ds.df_data.loc[leading, :]
            df_profiles_meta = ds.df_profiles.loc[leading, :]
            meta_ds = DataStruct(df_data_meta, df_profiles_meta, ds.name, orig_sheet_name=ds.orig_sheet_name)

            # now drop all garbage
            ds.df_data.drop(leading, inplace=True)
            ds.df_profiles.drop(leading, inplace=True)
            return meta_ds