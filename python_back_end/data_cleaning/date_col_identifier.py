import pickle
import re

import jsonpickle
import numpy as np
import pandas as pd
from skimage.measure import label

from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir, PROGRAM_STRINGS as ps, \
    PROGRAM_PARAMETERS as pp
from python_back_end.utilities.custom_multiprocessing import DebuggablePool


class DateColIdentifier:


    year_pattern = [r"(?i)([^0-9]|\b)([1][9][8-9][0-9]|[2][0-1][0-2][0-9])|"
                    r"\b(0?[1-9]|[12][0-9]|3[01])[\/\-](0?[1-9]|1[012])[\/\-]|"
                    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"]
    non_numeric_pattern = ["^([^0-9]*)$"]



    @staticmethod
    def identify_date_cols(ds):
        p = DebuggablePool(pp.N_CORES)
        df_data = ds.df_data
        collist = [df_data[col] for col in df_data]
        temp = p.map(DateColIdentifier.date_form, collist)
        p.close()
        mat = pd.DataFrame(np.transpose(temp), columns=df_data.columns)
        n_date_cells = (mat == 1).sum(axis=0)
        if mat.shape[0] > 0 and mat.shape[1] > 0:
            components = label(df_data.values == "")
            # find components on first row
            unique = np.unique(components[0, :])
            unique = unique[unique != 0]
            first_zero = np.argmax(components == 0, axis=0)

            for i in range(components.shape[1]):
                if first_zero[i] != 0:
                    components[first_zero[i] + 1:, i] = 0
            #components[first_zero != 0].iloc[first_zero[first_zero != 0]+1:, ] = 0
            for num in unique:
                temp_sum = np.sum(components == num, axis=0)
                temp_sum[components[0, :] != num] = 0
                # the multiplication is to remove cols with no dates in it
                n_date_cells += temp_sum * (n_date_cells != 0)
        length = mat.shape[0]
        if length < pp.MIN_LENGTH_NORMAL_COL:
            date_cols = n_date_cells/length > pp.MIN_DATE_RATIO_SHORT_COL
        else:
            date_cols = n_date_cells / length > pp.MIN_DATE_RATIO_NORMAL_COL
        # Mark the date entries in the date cols
        month_cols = DateColIdentifier.identify_month_cols(ds, mat)
        date_cols = np.logical_or(date_cols, month_cols)
        DateColIdentifier.mark_date_entries(ds, date_cols, mat)
        return date_cols, mat


    @staticmethod
    def identify_month_cols(ds, mat, common_denominator=12):
        month_cols = pd.Series(0, index=ds.df_data.columns, dtype=bool)
        df_num = TypeColExtracter.extract_num_cols(ds.df_data, ds.df_profiles)
        for name, col in df_num.iteritems():
            if np.std(col) > common_denominator/2:
                # not too many zeros
                zero_ratio = (col == 0).sum()/col.size
                if zero_ratio < 0.25:
                    divisible = (col % common_denominator) == 0
                    div_frac = divisible.sum()/divisible.size
                    if div_frac > pp.MIN_DIV_RATIO_MONTH_COL:
                        month_cols[name] = True
                        temp_col = mat[name].copy()
                        temp_bool = np.logical_and(divisible, temp_col == 0).values
                        #print(name)
                        #print(temp_bool.shape)
                        #print(temp_col.shape)
                        temp_col[temp_bool] = 1
                        mat[name] = temp_col
        return month_cols




    @staticmethod
    def identify_marked_date_cols(ds):
        df_data = ds.df_data
        d_col = pd.Series(False, index=df_data.columns)

        for header in d_col.index:
            d_col[header] = ps.TRANSFORMED_DATE_COL_NAME in header
        if d_col.any():
            return d_col
        elif np.any(ds.df_profiles == SheetTypeDefinitions.XL_DATE) or np.any(ds.df_profiles == SheetTypeDefinitions.STRING_DATE):
            n_date_cells = (ds.df_profiles == SheetTypeDefinitions.XL_DATE).sum(axis=0)
            n_date_cells += (ds.df_profiles == SheetTypeDefinitions.STRING_DATE).sum(axis=0)
            d_col = n_date_cells > np.minimum(pp.MIN_N_DATES_DATE_COL, df_data.shape[0] -1)
            return d_col
        else:
            date_cols, dummy = DateColIdentifier.identify_date_cols(ds)
            return date_cols



    @staticmethod
    def mark_date_entries(ds, date_cols,  mat):
        for date_col in date_cols.index[date_cols]:
            date_profs = (ds.df_profiles[date_col]).values
            date_cells = (mat[date_col] == 1).values
            xls_dates = date_profs == SheetTypeDefinitions.XL_DATE
            date_profs[date_cells] = SheetTypeDefinitions.STRING_DATE
            date_profs[xls_dates] = SheetTypeDefinitions.XL_DATE
            df_profiles_temp = ds.df_profiles.copy()
            df_profiles_temp.loc[:, date_col] = date_profs
            ds.df_profiles = df_profiles_temp

    @staticmethod
    def date_form(series):
        out = series.map(lambda val: DateColIdentifier.match(val)).values
        # out = np.empty((len(series),), dtype=int)
        # for i, val in enumerate(series):
        #     out[i] = DateColIdentifier.match(val)
        return out

    @staticmethod
    def match(input, return_match=False):
        # TODO use input type more intelligently
        string = str(input)

        # Check if contains year
        l = [re.search(pat, string) for pat in DateColIdentifier.year_pattern]
        if not all(v is None for v in l):
            if not return_match:
                return 1
            for match in l:
                if match is not None:
                    start = match.regs[0][0]
                    stop = match.regs[0][1]
                    ret_string = string[start:stop]
                    return ret_string
                # Check if cell is non-numeric
        l = [re.search(pat, string) for pat in DateColIdentifier.non_numeric_pattern]
        if not all(v is None for v in l):
            if not return_match:
                return 2
        # Remaining cells are numeric and does not contain years
        if not return_match:
            return 0
        else:
            return None

    @staticmethod
    def gen_date_col(sheet_array, headers, mat, cols):
        new_cols = dict()
        for col in cols:
            new_cols[headers[col]+ps.TRANSFORMED_DATE_COL_NAME] = []
        for col in cols:
            last_date = ""
            for i in range(len(sheet_array)):
                if mat[i, col] == 1:
                    last_date = sheet_array[i][col]
                new_cols[headers[col]+ps.TRANSFORMED_DATE_COL_NAME].append(last_date)
        return new_cols

    # @staticmethod
    # def fill_in_similar(ds, cols, mat):
    #     """
    #     This function is currently not used
    #     :param ds:
    #     :param cols:
    #     :param mat:
    #     :return:
    #     """
    #     # loop over the date_cols
    #     for date_name, date_col in mat[cols.index[cols]].iteritems():
    #         for name, non_date_profile in ds.df_profiles[cols.index[cols == False]].iteritems():
    #             ratio = ((date_col != 1) & (non_date_profile == SheetTypeDefinitions.EMPTY_STRING)).sum()/(date_col != 1).sum()
    #             if ratio >= pp.MIN_RATIO_DATE_SIMILAR_COL:
    #                 data_col = ds.df_data[name]
    #                 prof_col = ds.df_profiles[name]
    #                 last_entry = None
    #                 for i in range(len(data_col)):
    #                     if (data_col.iloc[i] == data_col.iloc[i]) and (data_col.iloc[i] != ""):
    #                         last_entry = [data_col.iloc[i], prof_col.iloc[i]]
    #                     elif last_entry is not None:
    #                         data_col[i] = last_entry[0]
    #                         prof_col[i] = last_entry[1]