from python_back_end.utilities.custom_multiprocessing import DebuggablePool
import numpy as np
import pandas as pd
from python_back_end.triangle_formatting.date_sorter import DateSorter
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.exceptions import NonpermissibleDateColumnDetected
from python_back_end.program_settings import PROGRAM_STRINGS as ps, PROGRAM_PARAMETERS as pp
from python_back_end.utilities.help_functions import strict_index, sum_unique
from python_back_end.utilities.state_handling import DataHolder, DataStruct
from functools import partial

class TriangleFromTableBuilder:

    @staticmethod
    def build_triangle_from_table(dh):
        new_dh = DataHolder(dh.name)
        pool = DebuggablePool(pp.N_CORES)
        # First find all date cols and see if one of them has target structure.
        for dh_ind, ds in enumerate(dh.data_struct_list):
            id_col, hori_date_col, vert_date_col = TriangleFromTableBuilder.do_the_magic(ds, pool)
            # cut each id into one row
            cut_list = TriangleFromTableBuilder.make_cut_list(ds.df_data[id_col])
            # use the cut_list to insert all elements
            tr_cols = pd.Series(ds.df_profiles.iloc[0, :] == SheetTypeDefinitions.TRIANGLE_ELEMENT, index=ds.df_profiles.columns)
            pad_header_mapping = TriangleFromTableBuilder.make_pad_header_mapping(ds, hori_date_col)
            vert_col_tup = (vert_date_col, ds.df_data[vert_date_col])
            hori_col_tup = (hori_date_col, ds.df_data[hori_date_col])
            id_col_tup = (id_col, ds.df_data[id_col])
            func = partial(TriangleFromTableBuilder.apply_cuts, cut_list, vert_col_tup, hori_col_tup, id_col_tup, pad_header_mapping)
            tr_col_tup_list = [(col_name, ds.df_data[col_name]) for col_name in tr_cols.index[tr_cols]]
            out = pool.map(func, tr_col_tup_list)
            #for name, tr_col in ds.df_data[tr_cols.index[tr_cols]].iteritems():
            for temp_df_data, temp_df_profiles, name in out:
                new_dh.add_sheet(name, temp_df_data, temp_df_profiles)
            #new_dh.add_sheet(name, temp_df_data, temp_df_profiles)
        pool.close()
        return new_dh
    @staticmethod
    def make_pad_header_mapping(ds, hori_date_col):
        start_pad = ds.df_data.columns[-1][:pp.N_DIGITS_HEADER_PADDING]
        start_pad = int(start_pad)
        temp = ds.df_data[hori_date_col].values
        temp_headers = sorted(np.unique(temp))
        pad_header_mapping = {head: str(ind).zfill(pp.N_DIGITS_HEADER_PADDING) + ". " + str(head)
                              for head, ind in zip(temp_headers, range(start_pad, len(temp_headers) + start_pad))}
        return pad_header_mapping




    @staticmethod
    def apply_cuts(cut_list, vert_col_tup, hori_col_tup, id_col_tup, pad_header_mapping, tr_col_tup):

        col_list = list()
        for cut in cut_list:
            # make unique column headers by summing
            temp_headers = hori_col_tup[1][cut].values

            temp_values = tr_col_tup[1][cut].values
            temp_headers, temp_values = sum_unique(temp_headers, temp_values)
            temp_headers = [pad_header_mapping[el] for el in temp_headers]
            col_df = pd.Series(temp_values, index=temp_headers)
            # add stuff to the series
            temp_num = vert_col_tup[1][cut[0]]
            temp_id = id_col_tup[1][cut[0]]
            col_df.loc[vert_col_tup[0]] = temp_num
            col_df.loc[id_col_tup[0]] = temp_id
            col_list.append(col_df)
        temp_df_data = pd.concat(col_list, axis=1, sort=True)
        temp_df_data = temp_df_data.transpose()
        temp_df_data = temp_df_data.fillna(0)
        # get the year column for sorting
        sorting_col = temp_df_data.loc[:, vert_col_tup[0]]
        temp_df_data = DateSorter.append_and_sort(temp_df_data, sorting_col)

        temp_df_profiles = pd.DataFrame(SheetTypeDefinitions.TRIANGLE_ELEMENT, columns=temp_df_data.columns,
                                        index=temp_df_data.index)
        temp_df_profiles.loc[:, vert_col_tup[0]] = SheetTypeDefinitions.STRING_DATE
        temp_df_profiles.loc[:, id_col_tup[0]] = SheetTypeDefinitions.ID_ELEMENT
        #temp_ds = DataStruct()
        return temp_df_data, temp_df_profiles, tr_col_tup[0]

    @staticmethod
    def make_cut_list(id_col):
        cut_list = []
        uniques = id_col.unique()
        index_form = pd.Index(id_col)
        for id in uniques:
            idxs = id_col.index[index_form.get_loc(id)]
            if isinstance(idxs, pd.Index):
                idxs = idxs.tolist()
            else:
                idxs = [idxs]
            cut_list.append(idxs)
        return cut_list

    @staticmethod
    def do_the_magic(ds, pool):
        date_cols = DateColIdentifier.identify_marked_date_cols(ds)
        id_cols = pd.Series(ds.df_profiles.iloc[0, :] == SheetTypeDefinitions.ID_ELEMENT, index=ds.df_profiles.columns)
        horizontal_matches = pd.DataFrame(0, columns=date_cols.index[date_cols], index=id_cols.index[id_cols])
        for date_name in date_cols.index[date_cols]:
            date_col = ds.df_data[date_name]
            id_date_match_part = partial(TriangleFromTableBuilder.id_date_match, date_col)
            id_col_list = [ds.df_data[col] for col in id_cols.index[id_cols]]
            temp = pool.map(id_date_match_part, id_col_list)
            temp_list = list(temp)
            horizontal_matches.loc[:, date_name] = temp_list
            #for id_name in id_cols.index[id_cols]:
            #    horizontal_matches.loc[id_name, date_name] = TriangleFromTableBuilder.id_date_match(ds, id_name, date_name)
        id_col_name = horizontal_matches.max(axis=1).idxmax()
        hori_date_col = horizontal_matches.max(axis=0).idxmax()
        print(hori_date_col)
        # remove the chosen horizontal column
        date_cols[hori_date_col] = False
        id_col = ds.df_data[id_col_name]
        vert_col_match_part = partial(TriangleFromTableBuilder.verti_col_match, id_col)
        date_col_list = [ds.df_data[date_col_name] for date_col_name in date_cols.index[date_cols]]
        vert_scores = pool.map(vert_col_match_part, date_col_list)
        vertical_matches = pd.Series(vert_scores, index=date_cols.index[date_cols])
        #for date_col_name in date_cols.index[date_cols]:
        #    vertical_matches[date_col_name] = TriangleFromTableBuilder.verti_col_match(ds, id_col_name, date_col_name)
        vert_date_col = vertical_matches.idxmax()

        return id_col_name, hori_date_col, vert_date_col

    @staticmethod
    def verti_col_match(id_col, date_col):
        #id_col, date_col = ds.df_data[id_col_name], ds.df_data[date_col_name]
        # get number of unique items in date_col
        match = len(date_col.unique())
        # now minus for each break within one id
        uniques = id_col.unique()
        index_form = pd.Index(id_col)
        for id in uniques:
            idxs = index_form.get_loc(id)
            dates = date_col.iloc[idxs]
            if isinstance(dates, pd.Series):
                match -= len(dates.unique()) - 1
        return match

    @staticmethod
    def id_date_match(date_col, id_col):
        #id_col, date_col = ds.df_data[id_col_name], ds.df_data[date_col_name]
        # for one id, dates should be strict
        uniques = id_col.unique()
        index_form = pd.Index(id_col)
        strict_ness = 0
        for id in uniques:
            idxs = index_form.get_loc(id)
            dates = date_col.iloc[idxs]
            if isinstance(dates, pd.Series):
                increment = strict_index(dates.values)
                strict_ness += increment
        return strict_ness

