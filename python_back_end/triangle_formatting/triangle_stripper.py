import numpy as np
import pandas as pd

from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.exceptions import NoTriangleElementsDetectedException
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp, PROGRAM_STRINGS as ps
from python_back_end.utilities.help_functions import ascend_ind, desc_ind
from python_back_end.exceptions import RequiredColumnsNotPresent
from python_back_end.utilities.help_functions import general_adjacent


class TriangleStripper:

    @staticmethod
    def strip_triangles(dh, **kwargs):
        tri_type = kwargs["tri_type"]
        copy = dh.copy_without_memory()
        tr_cols_dict = TriangleStripper.identify_triangle_cols(dh)
        keep_cols_dict = dict()
        for ds in dh:
            tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_profiles.shape]
            # Kill all non-numeric triangle components
            tr_els = ds.df_data[tr_cols.index[tr_cols]].copy()
            tr_els[ds.df_profiles[tr_cols.index[tr_cols]] != SheetTypeDefinitions.FLOAT] = 0

            ds.df_data[tr_cols.index[tr_cols]] = tr_els
            ds.df_profiles[tr_cols.index[tr_cols]] = SheetTypeDefinitions.TRIANGLE_ELEMENT

            # Find date col
            d_col = DateColIdentifier.identify_marked_date_cols(ds)
            # Label it correctly
            ds.df_profiles[d_col.index[d_col]] = SheetTypeDefinitions.STRING_DATE
            # Find id col
            if tri_type == "single":
                id_col = TriangleStripper.identify_id_col(ds, d_col, tr_cols)
                ds.df_profiles[id_col.index[id_col]] = SheetTypeDefinitions.ID_ELEMENT
                # combine with logical or
                combined = tr_cols | d_col | id_col
            else:
                combined = tr_cols | d_col
            # save all the cols we want to keep
            keep_cols_dict[tuple(ds.df_data.columns) + ds.df_data.shape] = combined
            # if any TRIANGLE_ELEMENT non-numeric, make unfit for output.
        #Not needed, since we already remove non-numeric
        #for ds in dh:
        #    TriangleStripper.filter_non_numeric_triangles(ds)

        TriangleStripper.turn_triangle(dh, tr_cols_dict)

        for ds in dh:
            tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_profiles.shape]
            # if dates in tr_headers, check if adjustment necessary
            if tr_cols.sum() > 0:
                matches = np.array([DateColIdentifier.match(el) for el in ds.df_data.columns[tr_cols]])
                if np.sum(matches==1)/matches.size > 0.5:
                    TriangleStripper.right_adjust(ds, tr_cols)
            # Remove the rest

        for ds in dh:
            combined = keep_cols_dict[tuple(ds.df_data.columns) + ds.df_data.shape]
            ds.df_data = ds.df_data[combined.index[combined]]
            ds.df_profiles = ds.df_profiles[combined.index[combined]]

        # look for triangles without triangle elements
        elementless = np.zeros(len(dh.data_struct_list), dtype=bool)
        for ind, ds in enumerate(dh):
            if not (ds.df_profiles.values == SheetTypeDefinitions.TRIANGLE_ELEMENT).any():
                elementless[ind] = True
                ds.set_fit_for_output(False)

        # strip empty rows
        if tri_type == "single":
            TriangleStripper.strip_empty_rows(dh)



        if np.all(elementless):
            raise NoTriangleElementsDetectedException(copy)
        return dh

    @staticmethod
    def strip_empty_rows(dh):
        for ds in dh:
            id_col = ds.df_profiles.iloc[0, :] == SheetTypeDefinitions.ID_ELEMENT
            tr_cols = ds.df_profiles.iloc[0, :] == SheetTypeDefinitions.TRIANGLE_ELEMENT
            if not id_col.sum() == 1:
                raise RequiredColumnsNotPresent(dh)
            empty_ids = ds.df_data[list(id_col.index[id_col])[0]] == ""
            empty_trs = np.all(ds.df_data.loc[:, tr_cols] == 0, axis=1)
            combined = np.logical_and(empty_ids, empty_trs)
            ds.df_data = ds.df_data.loc[combined == False, :]
            ds.df_profiles = ds.df_profiles.loc[combined == False, :]




    @staticmethod
    def filter_non_numeric_triangles(ds):
        for name, col in ds.df_data.iteritems():
            if ds.df_profiles[name].iloc[0] == SheetTypeDefinitions.TRIANGLE_ELEMENT:
                temp_col = col.copy()
                for i in range(temp_col.size):
                    try:
                        if temp_col.iloc[i] == "" or temp_col.iloc[i] != temp_col.iloc[i]:
                            temp_col.iloc[i] = 0
                        else:
                            temp_col.iloc[i] = float(temp_col.iloc[i])
                    except:
                        ds.set_fit_for_output(False)
                ds.df_data[name] = temp_col

    @staticmethod
    def turn_triangle(dh, tr_cols_dict, alt_min_score = None):
        # TODO: HANDLE THE CASE WITH NON_SQUARE
        quad_list = np.zeros(dh.n, dtype=bool)
        for ind, ds in enumerate(dh.data_struct_list):
            tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_profiles.shape]
            length = tr_cols.sum()
            height = ds.df_data.shape[0]
            if length == height:
                quad_list[ind] = True

        if not quad_list.all():
            return
        # evaluate complete ascend descend ind
        ascend = 0
        descend = 0
        n_added = 0
        for ds in dh.data_struct_list:
            tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_profiles.shape]
            for name, col in ds.df_data[tr_cols.index[tr_cols]].iteritems():
                ascend += ascend_ind(col.values, col.size, strict=False)
                descend += desc_ind(col.values, col.size, strict=False)
                n_added += 1
        descend /= n_added
        ascend /= n_added
        turn = False
        if alt_min_score is None:
            if np.maximum(ascend, descend) > pp.MIN_SCORE_TURNED_TRIANGLE:
                turn = True
        else:
            if np.maximum(ascend, descend) > alt_min_score:
                turn = True

        if turn:
            # turn everything!
            for ds in dh.data_struct_list:
                tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_profiles.shape]
                tri_part = ds.df_data[tr_cols.index[tr_cols]].values
                ds.df_data[tr_cols.index[tr_cols]] = np.transpose(tri_part)


    @staticmethod
    def right_adjust(ds, tr_cols):
        # check if right adjustment needed.
        df_tr_cols = ds.df_data[tr_cols.index[tr_cols]]
        int_list = (df_tr_cols != 0).sum(axis=0).values
        length = len(int_list)
        desc = desc_ind(int_list, length)
        asc = ascend_ind(int_list, length)
        if desc > asc:
            # right adjust!
            array_tr_cols = df_tr_cols.values
            for ind in range(1, array_tr_cols.shape[0]):
                array_tr_cols[ind, ind:] = array_tr_cols[ind, :-ind]
                array_tr_cols[ind, :ind] = 0
            data_copy = ds.df_data.copy()
            data_copy.loc[:, tr_cols.index[tr_cols]] = array_tr_cols
            ds.df_data = data_copy



    @staticmethod
    def identify_triangle_cols(dh, **kwargs):
        # Take holistic approach, we need coherence in the headers for this to work!
        #last_headers = None
        header_group_dict = dict()
        for ds_ind, ds in enumerate(dh.data_struct_list):
            headers = tuple(ds.df_profiles.columns) + ds.df_profiles.shape
            if headers not in header_group_dict:
                header_group_dict[headers] = TriangleStripper.evaulate_col_headers(ds, **kwargs)
            else:
                header_group_dict[headers] += TriangleStripper.evaulate_col_headers(ds, **kwargs)

        # Boolify and label correctly
        for headers in header_group_dict:
            temp_mean = header_group_dict[headers].max()/2
            header_group_dict[headers] = header_group_dict[headers] > temp_mean
        return header_group_dict



    @staticmethod
    def evaulate_col_headers(ds, **kwargs):
        df_data, df_profiles = ds.df_data, ds.df_profiles
        if "test_min_cols" in kwargs:
            min_cols = 2
        else:
            min_cols = pp.MIN_COLS_TRIANGLE
        num_cols = TypeColExtracter.extract_num_cols(df_data, df_profiles)
        #, adjacent=True)
        if num_cols.shape[1] < min_cols:
            return pd.Series(0, index=df_profiles.columns)
        # get indices of num_cols
        num_profiles = df_profiles[num_cols.columns]
        #bool = num_profiles == SheetTypeDefinitions.ZERO_FLOAT
        bools = np.abs(num_cols) < 1e-010
        # find the column with the most zeroes, furthest from the middle
        sum = bools.sum(axis=0)/bools.shape[0]
        # Make continuity score matrix
        tr_cols_adjacent = TriangleStripper.make_tr_cols_adjacent(ds.df_profiles.columns, num_cols.columns)
        tr_cols_ramp = TriangleStripper.make_tr_cols_ramp(ds.df_profiles.columns, sum, min_cols)
        max_ids = np.where(sum == sum.max())[0]
        deviation = np.abs(num_profiles.shape[1]/2-max_ids)
        tr_extr_ind = max_ids[np.argmax(deviation)]
        # tr_extr_name = sum.idxmax()
        # tr_extr_ind = list(num_profiles.columns).index(tr_extr_name)
        if tr_extr_ind > num_profiles.shape[1]/2:
            num_profiles = num_profiles.iloc[:, :tr_extr_ind+1]
        else:
            num_profiles = num_profiles.iloc[:, tr_extr_ind:]
        tr_cols_most_zero = pd.Series(0, index=df_profiles.columns)
        tr_cols_most_zero[num_profiles.columns] = 1
        tr_cols = tr_cols_ramp + tr_cols_most_zero + tr_cols_adjacent
        # Now see if any of the column names are clearly off
        # Check if any header contains a date
        match_list = [DateColIdentifier.match(header) for header in tr_cols.index]
        if 1 in match_list:
            tr_cols[np.array(match_list) == 1] += 1
        return tr_cols

    @staticmethod
    def make_tr_cols_adjacent(col_names, num_col_names):
        adj_headers = general_adjacent(num_col_names)
        tr_cols_adjacent = pd.Series(0, index=col_names)
        tr_cols_adjacent[adj_headers] = 1
        return tr_cols_adjacent


    @staticmethod
    def make_tr_cols_ramp(col_names, sum, min_cols):
        score_m = pd.DataFrame(1e10, index=sum.index[0:-(min_cols-1)], columns=sum.index[min_cols-1:])
        for i, ind in enumerate(score_m.index):
            for j, col in enumerate(score_m.columns):
                if j >= i:
                    j += min_cols-1
                    steps = j-i
                    temp = np.abs(sum.iloc[i:j].values - sum.iloc[i+1:j+1].values)-1/steps
                    score_m.loc[ind, col] = np.sum(np.square(temp))/steps
        tr_cols_ramp = pd.Series(0, index=col_names)
        start = score_m.min(axis=1).idxmin()
        stop = score_m.min(axis=0).idxmin()
        started = False
        for ind in tr_cols_ramp.index:
            if ind == start:
                started = True
            if started:
                tr_cols_ramp[ind] = 1
            if ind == stop:
                break
        return tr_cols_ramp

    @staticmethod
    def identify_id_col(ds, d_col, tr_cols):
        remaining = (tr_cols | d_col) == False
        id_col = pd.Series(False, index=ds.df_data.columns)
        if (remaining == False).all():
            return id_col

        rem_vals = ds.df_data[remaining.index[remaining]]
        max_col, max_num = TriangleStripper.get_id_max_col(rem_vals)
        # check for solutions in the date cols
        if np.sum(d_col) >= 2:
            d_vals = ds.df_data[d_col.index[d_col]]
            d_max_col, d_max_num = TriangleStripper.get_id_max_col(d_vals)
            if d_max_num > max_num:
                max_col = d_max_col
                d_col[d_max_col] = False

        id_col[max_col] = True

        return id_col

    @staticmethod
    def get_id_max_col(df):

        unique_list = [(key, len(pd.unique(col))) for key, col in df.iteritems()]
        unique_series = pd.Series([el[1] for el in unique_list], index=[el[0] for el in unique_list])
        max_col = unique_series.idxmax()
        max_num = unique_series.max()
        return max_col, max_num