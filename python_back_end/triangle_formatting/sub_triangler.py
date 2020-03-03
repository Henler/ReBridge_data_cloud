from difflib import SequenceMatcher
from string import digits
from copy import deepcopy
import numpy as np
import pandas as pd
from scipy.sparse.csgraph._traversal import connected_components
from python_back_end.utilities.help_functions import general_adjacent
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier, TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.triangle_formatting.triangle_chopper import TriangleChopper
from python_back_end.utilities.state_handling import DataHolder, DataStruct


class SubTriangler:
    remove_digits = str.maketrans('', '', digits)

    @staticmethod
    def make_standard_triangles(dh, **kwargs):
        assert 'meta_dh' in kwargs
        meta_dh = kwargs['meta_dh']
        tri_type = "single"
        if "tri_type" in kwargs:
            tri_type = kwargs['tri_type']
        n_outputs = 1
        if "n_outputs" in kwargs:
            n_outputs = kwargs['n_outputs']
        new_dh_dict = dict()
        # This call will reset all entries in new_dh_dict
        new_dh_dict[dh.name] = dh
        for dh in new_dh_dict.values():
            SubTriangler.name_and_scrub_triangle(dh, new_dh_dict, meta_dh=meta_dh)

        for ds in list(new_dh_dict.values())[0].data_struct_list:
            SubTriangler.divide_into_subtriangles(ds, new_dh_dict, meta_dh)

        for new_dh in new_dh_dict.values():
            SubTriangler.scrub_rows(new_dh)

        # choose dh in dict
        dh_name = SubTriangler.data_holder_selector(new_dh_dict, dh.name, tri_type, n_outputs)
        return new_dh_dict[dh_name], new_dh_dict

    @staticmethod
    def scrub_rows(dh):
        for ds in dh:
            d_cols = DateColIdentifier.identify_marked_date_cols(ds)
            d_cols = d_cols[d_cols].index
            date_form = []
            for col_name in d_cols:
                col = ds.df_data[col_name]
                if len(date_form) == 0:
                    date_form = DateColIdentifier.date_form(col) == 1
                else:
                    date_form = np.logical_or(date_form, DateColIdentifier.date_form(col) == 1)

            not_date_form = date_form == False
            ds.df_data = ds.df_data.drop(ds.df_data.index[not_date_form])
            ds.df_profiles = ds.df_profiles.drop(ds.df_profiles.index[not_date_form])

    @staticmethod
    def data_holder_selector(dh_dict, orig_name, tri_type, n_outputs):
        # only decompositions that exist for all sheets are acknowledged
        fully_represented, n_orig_sheets = SubTriangler.get_fully_represented(dh_dict, orig_name)
        if len(fully_represented) == 1:
            return fully_represented[0]
        # check size coherence
        deviations = list()
        if tri_type == "aggregate":
            # search for the most square ones!
            for name in fully_represented:
                dh = dh_dict[name]
                square_ind1 = [ds.df_data.shape[0]/ds.df_data.shape[1] for ds in dh]
                square_ind2 = [ds.df_data.shape[1] / ds.df_data.shape[0] for ds in dh]
                square_index = np.minimum(square_ind1, square_ind2).mean()
                deviations.append(1-square_index)
        elif tri_type == "single":
            # get the dh with the most coherent sizes
            for name in fully_represented:
                dh = dh_dict[name]
                n_sheet_dev = np.maximum(0, pp.N_DESIRED_PER_SHEET*n_outputs - dh.n)
                len_list = np.array([ds.df_data.shape[0] for ds in dh])
                len_dev = np.sum(1-(len_list/np.max(len_list)))
                dev = n_sheet_dev + len_dev
                # if n_outputs == 1:
                #     dev = np.abs(pp.N_DESIRED_PER_SHEET - dh.n)
                # else:
                #     occurence_list = [ds.orig_sheet_name for ds in dh]
                #     unique, counts = np.unique(occurence_list, return_counts=True)
                #     dev = np.sum(np.abs(counts - pp.N_DESIRED_PER_SHEET)) / len(unique)
                deviations.append(dev)
        else:
            raise ValueError("Unknown triangle type: " + tri_type)
        deviations = np.array(deviations)
        return fully_represented[np.argmin(deviations)]





    @staticmethod
    def get_fully_represented(dh_dict, orig_name):
        orig_dh = dh_dict[orig_name]
        orig_sheets = {ds.orig_sheet_name for ds in orig_dh}
        fully_represented = list()
        for key, dh in dh_dict.items():
            sheets = {ds.orig_sheet_name for ds in dh}
            if len(orig_sheets.difference(sheets)) == 0:
                fully_represented.append(key)
        return fully_represented, len(orig_sheets)


    @staticmethod
    def name_and_scrub_triangle(dh, new_dh_dict, meta_dh=None):
        new_dh = DataHolder(dh.name)
        word_set_list = list()
        for ds in dh:
            word_set_list.append(SubTriangler.identify_category_name(ds, meta_dh))
        if meta_dh != None:
            if meta_dh.n > 0:
                SubTriangler.divide_meta_data(dh, meta_dh, word_set_list)
        # Find the most unique name
        for i in range(len(word_set_list)):
            ds = dh.data_struct_list[i]
            difference = word_set_list[i].copy()
            for j in range(len(word_set_list)):
                if j != i and ds.orig_sheet_name == dh.data_struct_list[j].orig_sheet_name:
                    difference = difference.difference(word_set_list[j])
            if len(difference) > 0:
                stringified = sorted([str(el) for el in difference])
                name = " ".join(stringified)
                name = name.translate(SubTriangler.remove_digits)
            else:
                name = str(i)
            if ds.name != ds.orig_sheet_name:
                name = ds.name + " " + name

            new_dh.add_sheet(name, ds.df_data, ds.df_profiles, orig_sheet_name=ds.orig_sheet_name)
        new_dh_dict[dh.name] = new_dh

    @staticmethod
    def divide_meta_data(dh, meta_dh, word_set_list):
        # map each meta data to the triangle closest under it
        tr_ids = [ds.id for ds in dh]
        meta_ids = [ds.id for ds in meta_dh.data_struct_list]
        #content = pd.Series([ds.df_data.values[0] for ds in meta_dh], index=meta_ids)
        distances = pd.DataFrame(np.iinfo(np.uint32).max, columns=tr_ids, index=meta_ids)
        #check if median is a reasonable measure of distance
        spatial_info = SubTriangler.generate_tr_spatial_info(dh)

        for ds in dh:
            if len(ds.df_data.index) > 0:
                ds_low = np.min(np.array(ds.df_data.index))
                ds_high = np.max(np.array(ds.df_data.index))
                if ds.name in meta_dh.data_dict:
                    for meta_ds in meta_dh.data_dict[ds.name]:
                        if ds.df_data.size > meta_ds.df_data.size:
                            meta_high = np.max(np.array(meta_ds.df_data.index))
                            # check = meta_ds.df_data.iloc[0,0]
                            # if check == 'Combined':
                            #     meta_col_int_array = np.array(
                            #         [int(el[0:pp.N_DIGITS_HEADER_PADDING]) for el in meta_ds.df_data.columns])
                            #     print('found')
                            if meta_high <= ds_high:
                                tr_col_int_array = spatial_info[ds.id]['int_array']
                                meta_col_int_array = np.array(
                                    [int(el[0:pp.N_DIGITS_HEADER_PADDING]) for el in meta_ds.df_data.columns])
                                #meta_vert_median = np.array(meta_ds.df_data.index)[int(np.floor(len(meta_ds.df_data.index) / 2))]
                                if len(tr_col_int_array) > 0:
                                    if spatial_info['use_median']:
                                        meta_median = meta_col_int_array[int(np.floor(len(meta_col_int_array) / 2))]
                                        col_dist = np.abs(meta_median - spatial_info[ds.id]['hori_median'])
                                    else:
                                        col_mat = np.abs(tr_col_int_array - meta_col_int_array)
                                        col_dist = np.min(col_mat)
                                    ind_dist = np.abs(meta_high-ds_low)
                                    distances.loc[meta_ds.id, ds.id] = ind_dist + col_dist
        closest_dists = distances.min(axis=1)
        closest_ids = {index: distances.columns[np.where(distances.loc[index, :] == closest_dists[index])] for index in
                       closest_dists.index}

        for word_set, ds in zip(word_set_list, dh):
            for meta_id in closest_dists.index:
                if closest_dists[meta_id] < pp.MAX_LENGTH_TO_RELATED_DATA:
                    if ds.id in closest_ids[meta_id]:
                        vals = meta_dh.id_dict[meta_id].df_data.values.flatten()
                        word_list = [str(el) for el in vals]
                        word_set.update(word_list)

    @staticmethod
    def generate_tr_spatial_info(dh):
        outer_dict = dict()
        for ds in dh:
            tr_spatial_dict = dict()
            num_cols = TypeColExtracter.extract_num_cols(ds.df_data, ds.df_profiles)
            adj_headers = general_adjacent(num_cols.columns)
            num_cols = num_cols[adj_headers]
            if num_cols.size > 0:
                tr_col_int_array = np.array([int(el[0:pp.N_DIGITS_HEADER_PADDING]) for el in num_cols.columns])
                tr_spatial_dict["hori_median"] = tr_col_int_array[int(np.floor(len(tr_col_int_array) / 2))]
                tr_spatial_dict["int_array"] = tr_col_int_array.reshape((tr_col_int_array.size, 1))
                tr_spatial_dict["vert_median"] = np.array(num_cols.index)[int(np.floor(len(num_cols.index) / 2))]
            else:
                tr_spatial_dict["hori_median"] = np.iinfo(np.uint32).max
                tr_spatial_dict["int_array"] = np.array([])
                tr_spatial_dict["vert_median"] = np.iinfo(np.uint32).max
            tr_spatial_dict['name'] = ds.name
            outer_dict[ds.id] = tr_spatial_dict

        use_median = True
        for name in dh.data_dict:
            info_array = np.array([np.array([el['hori_median'], el['vert_median']]) for el in outer_dict.values()
                                   if el['name'] == name])
            distances = np.zeros((len(info_array), len(info_array))) + pp.MIN_MEDIAN_DISTANCE
            for i in range(len(info_array)):
                for j in range(i + 1, len(info_array)):
                    distances[i, j] = np.linalg.norm(info_array[i, :] - info_array[j, :])
            min_dist = np.min(distances)
            if min_dist < pp.MIN_MEDIAN_DISTANCE:
                use_median = False
        outer_dict['use_median'] = use_median

        return outer_dict




    @staticmethod
    def divide_into_subtriangles(ds, new_dh_dict, meta_dh):
        SubTriangler.vertical_category_division(ds, new_dh_dict, meta_dh)
        SubTriangler.horizontal_category_division(ds, new_dh_dict, meta_dh)


    @staticmethod
    def vertical_category_division(ds, new_dh_dict, meta_dh):
        # find the category column
        # Should be strings (for now) (used)
        # Kind of periodic (thus repetitive entries) (used)
        # some entries may change slightly (used)
        # period may change slightly (not checked for now)(should be checked in new if statment)
        # Should get tag matches in dict (not checked for now)
        df_data = ds.df_data
        df_profiles = ds.df_profiles
        orig_name = ds.orig_sheet_name
        for col_name, col in df_data.iteritems():

            string_ratio = np.sum(df_profiles[col_name].values == SheetTypeDefinitions.STRING) / df_profiles[col_name].values.size
            if string_ratio > pp.MIN_STRING_RATIO_CAT_COL:
                # check periodic potential
                string_col = col.astype(str)
                unique, counts = np.unique(string_col, return_counts=True)
                ratio = np.max(counts) / col.size
                if ratio < pp.MAX_RATIO_LARGEST_CAT and ratio > pp.MIN_RATIO_LARGEST_CAT  and len(unique) < pp.MAX_N_CATS:
                    if col_name in new_dh_dict:
                        new_dh = new_dh_dict[col_name]
                    else:
                        new_dh = DataHolder(col_name)
                        new_dh_dict[col_name] = new_dh
                    #period_label_bool = counts * period > string_col.size - period
                    # now get the remaining
                    #sub_period_label = unique[period_label_bool == False]
                    match_dict = SubTriangler.component_finder(unique)

                    # now load the new_dh

                    for name in match_dict:
                        cond = np.array([string_col.values == sub_name for sub_name in match_dict[name]]).any(axis=0)
                        sub_df_data = df_data[cond].drop(columns=[string_col.name])
                        sub_df_profiles = df_profiles[cond].drop(columns=[string_col.name])
                        if name == "" or np.sum(cond) < 4:
                            new_ds = DataStruct(sub_df_data, sub_df_profiles, name, orig_sheet_name=orig_name)
                            for split in new_ds.col_split_ds():
                                if not np.all(split.df_profiles == SheetTypeDefinitions.EMPTY_STRING) and not (
                                np.all(split.df_data == "")):
                                    meta_dh.add_ds(split)
                        else:
                            new_dh.add_sheet(ds.name + " - " + name, sub_df_data, sub_df_profiles, orig_sheet_name=orig_name)

    @staticmethod
    def horizontal_category_division(ds, new_dh_dict, meta_dh):
        # find potential category rows
        # for now, look for strings
        str_ratio = (ds.df_profiles == SheetTypeDefinitions.STRING).sum(axis=1)/ds.df_profiles.shape[1]
        cat_cols = str_ratio >= pp.MIN_STRING_RATIO_CAT_ROW
        for ind in cat_cols.index[cat_cols]:
            cat_row = ds.df_data.loc[ind, :]
            unique, counts = np.unique(cat_row, return_counts=True)
            ratio = np.max(counts) / cat_row.size
            if ratio < 0.5 and len(unique)/cat_row.size < 0.5:
                row_name = "Row " + str(ind)
                if row_name in new_dh_dict:
                    new_dh = new_dh_dict[row_name]
                else:
                    new_dh = DataHolder(row_name)
                    new_dh_dict[row_name] = new_dh
                match_dict = SubTriangler.component_finder(unique)
                rev_match_dict = dict()
                for key, val in match_dict.items():
                    for item in val:
                        rev_match_dict[item] = key
                count_dict = {}
                for key, val in match_dict.items():
                    active = np.isin(unique, val)
                    count_dict[key] = np.sum(counts[active])
                # get number of data_structs to make
                headers_dict = {}
                for key, val in count_dict.items():
                    if val > pp.MIN_YEARS_SPANNED:
                        headers_dict[key] = []
                len_array = np.zeros(len(headers_dict), dtype=int)
                for enum, key in enumerate(headers_dict):
                    for name, val in cat_row.iteritems():
                        if rev_match_dict[val] not in headers_dict or rev_match_dict[val] == key:
                            headers_dict[key].append(name)
                    len_array[enum] = len(headers_dict[key])

                # Now fill the dh
                # First, if same length, find optimal header naming
                same_length = np.std(len_array) == 0
                if same_length:
                    out_headers = deepcopy(headers_dict)
                    for i in range(len_array[0]):
                        i_headers = np.array([val[i] for val in headers_dict.values()])
                        missing = np.array(["Missing header" in header for header in i_headers])
                        if np.any(missing) and np.any(np.logical_not(missing)):
                            header = i_headers[np.logical_not(missing)][0]
                            for key in out_headers:
                                out_headers[key][i] = header

                for key, val in headers_dict.items():
                    df_data = ds.df_data.loc[ds.df_data.index != ind, val]
                    df_profiles = ds.df_profiles.loc[ds.df_data.index != ind, val]
                    if same_length:
                        df_data = pd.DataFrame(df_data.values, index=df_data.index, columns=out_headers[key])
                        df_profiles = pd.DataFrame(df_profiles.values, index=df_profiles.index, columns=out_headers[key])
                    new_dh.add_sheet(ds.name + " - " + key, df_data, df_profiles, orig_sheet_name=ds.orig_sheet_name)

    # find similar entries, group them and make collective name
    @staticmethod
    def component_finder(uniques):
        n_el = len(uniques)
        dist_m = np.zeros(shape=(n_el,n_el))
        for i in range(n_el):
            for j in range(i, n_el):
                dist_m[i][j] = SequenceMatcher(None, uniques[i], uniques[j]).ratio()
        dist_m = dist_m + np.transpose(dist_m) - np.eye(n_el)
        n_components, labels = connected_components(dist_m >= pp.MIN_LABEL_SIM)
        # make matches
        match_dict = dict()
        for i in range(n_components):
            comp = np.array(uniques)[labels == i]
            if len(comp) == 1:
                match_dict[comp[0]] = comp
            else:
                # find a common name
                block = SequenceMatcher(None, comp[0], comp[1]).find_longest_match(0, len(comp[0]), 0, len(comp[1]))
                name = comp[0][block.a:block.size+block.a]
                match_dict[name] = comp

        return match_dict

    @staticmethod
    def identify_category_name(ds, meta_dh):
        #df_data = ds.df_data
        d_cols = DateColIdentifier.identify_marked_date_cols(ds)
        d_cols = d_cols[d_cols].index
        date_form = []
        for col_name in d_cols:
            col = ds.df_data[col_name]
            if len(date_form) == 0:
                date_form = DateColIdentifier.date_form(col) == 1
            else:
                date_form = np.logical_or(date_form, DateColIdentifier.date_form(col) == 1)

        not_date_form = date_form == False
        for ind in ds.df_data.index[not_date_form]:
            for col in ds.df_data.columns:
                if ds.df_data.loc[ind, col] != "" and ds.df_profiles.loc[ind, col] == SheetTypeDefinitions.STRING:
                    temp_data = pd.DataFrame(ds.df_data.loc[ind, col], index=[ind], columns=[col])
                    temp_profile = pd.DataFrame(SheetTypeDefinitions.STRING, index=[ind], columns=[col])
                    meta_dh.add_sheet(ds.name, temp_data, temp_profile, orig_sheet_name=ds.orig_sheet_name)
        #wordset = set(ds.df_data.values[not_date_form, :].flatten())
        #ds.df_data = ds.df_data.drop(ds.df_data.index[not_date_form])
        #ds.df_profiles = ds.df_profiles.drop(ds.df_profiles.index[not_date_form])

        #kill repeated headers
        # strip repeated headers
        repeated, deviating_entries = TriangleChopper.find_repeated_headers(ds)
        #wordset.update(deviating_entries)
        for ind in ds.df_data.index[repeated]:
            for col in deviating_entries:
                if ds.df_data.loc[ind, col] != "" and ds.df_profiles.loc[ind, col] == SheetTypeDefinitions.STRING:
                    temp_data = pd.DataFrame(ds.df_data.loc[ind, col], index=[ind], columns=[col])
                    temp_profile = pd.DataFrame(SheetTypeDefinitions.STRING, index=[ind], columns=[col])
                    meta_dh.add_sheet(ds.name, temp_data, temp_profile, orig_sheet_name=ds.orig_sheet_name)
        for ind in repeated:
            ds.df_data = ds.df_data.drop(ds.df_data.index[ind])
            ds.df_profiles = ds.df_profiles.drop(ds.df_profiles.index[ind])

        #wordset.add(ds.name)
        #return wordset
        return set()
