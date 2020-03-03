from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
import pandas as pd
import numpy as np
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
import jsonpickle
import re
from skimage.measure import label
import pickle


class StringFiller:

    @staticmethod
    def fill_hollow_str_cols(dh):
        # get string cols
        for ds in dh:
            for name, col in ds.df_profiles.iteritems():
                str_ratio = np.sum(col.values == SheetTypeDefinitions.STRING) / col.size
                # TODO: check what happened after POI change (triangulation)
                #not_marked_empties = np.sum(np.logical_and(col.values == SheetTypeDefinitions.STRING,
                #                                           ds.df_data[name] == "")) / col.size

                empty_ratio = np.sum(col.values == SheetTypeDefinitions.EMPTY_STRING) / col.size
                empty_ratio += np.sum(ds.df_data[name] == 0) / col.size
                #str_ratio -= not_marked_empties
                #empty_ratio += not_marked_empties
                if str_ratio > pp.MIN_STRING_RATIO_HOLLOW_STRING_COL and col.size >= 20 and empty_ratio > pp.MIN_EMPTY_RATIO_HOLLOW_STRING_COL:
                    data_col = ds.df_data[name].copy()
                    prof_col = ds.df_profiles[name].copy()
                    last_entry = None
                    for i in range(len(data_col)):
                        if (data_col.iloc[i] == data_col.iloc[i]) and (data_col.iloc[i] != "" and data_col.iloc[i] != 0):
                            last_entry = [data_col.iloc[i], prof_col.iloc[i]]
                        elif last_entry is not None:
                            data_col.iloc[i] = last_entry[0]
                            prof_col.iloc[i] = last_entry[1]
                    ds.df_data = ds.df_data.copy()
                    ds.df_profiles = ds.df_profiles.copy()
                    ds.df_data.loc[:, name] = data_col
                    ds.df_profiles.loc[:, name] = prof_col
        return dh


class DateFiller:

    clf = None
    with open(pdir.RESOURCES_DIR + '/svm_learning_data/date_svm.pickle', 'rb') as temp_file:
        clf = jsonpickle.decode(pickle.load(temp_file))

    @staticmethod
    def identify_and_gen_date_cols(dh, **kwargs):
        replace_col = True
        if 'replace_col' in kwargs:
            replace_col = kwargs['replace_col']
        for dh_ind, ds in enumerate(dh):
            df_data, df_profiles = ds.df_data, ds.df_profiles
            sep = ", "
            if ps.TRANSFORMED_DATE_COL_NAME in sep.join(df_data.columns):
                return df_data, df_profiles
            cols, mat = DateFiller.identify_incomplete_date_cols(ds, **kwargs)
            DateFiller.gen_transformed_date_col(ds, cols, mat, replace_col)
            #DateColIdentifier.fill_in_similar(ds, cols, mat)
        return dh

    @staticmethod
    def gen_transformed_date_col(ds, cols, mat, replace_col):
        df_data, df_profiles = ds.df_data, ds.df_profiles
        # Generate and add the new column
        for col in cols.index[cols.values]:
            new_col_name = col + ps.TRANSFORMED_DATE_COL_NAME
            last_date = ""
            old_col = df_data[col].values
            new_col = np.zeros(shape=old_col.shape, dtype=object)
            new_prof = np.ones(shape=old_col.shape, dtype=int) * SheetTypeDefinitions.STRING_DATE
            for i in range(len(old_col)):
                if mat.loc[mat.index[i], col] == 1:
                    last_date = DateColIdentifier.match(old_col[i], return_match=True)
                if isinstance(last_date, str):
                    new_col[i] = re.sub("[^0-9]", "", last_date)
                else:
                    new_col[i] = last_date
            if replace_col:
                df_data[col] = pd.Series(new_col, index=df_data.index)
                df_profiles[col] = pd.Series(new_prof, index=df_data.index)
                df_data.rename(columns={col: new_col_name}, inplace=True)
                df_profiles.rename(columns={col: new_col_name}, inplace=True)
            else:
                df_data[new_col_name] = pd.Series(new_col, index=df_data.index)
                df_profiles[new_col_name] = pd.Series(new_prof, index=df_data.index)
                # remove date entries
                data_col = df_data[col].copy()
                indexer = mat[col] == 1
                # get matches
                matches_list = [DateColIdentifier.match(el, return_match=True) for el in data_col.iloc[indexer.values]]
                strings = [str(string).replace(match, "") for string, match in zip(data_col.iloc[indexer.values], matches_list)]
                data_col.iloc[indexer.values] = np.array(strings)
                df_data[col] = data_col
                profile_col = df_profiles[col].copy()
                empties = data_col == ""
                profile_col.iloc[indexer.values] = SheetTypeDefinitions.STRING
                profile_col.iloc[empties.values] = SheetTypeDefinitions.EMPTY_STRING
                df_profiles[col] = profile_col

    @staticmethod
    def identify_incomplete_date_cols(ds, **kwargs):
        svm_logger = None
        if "svm_logger" in kwargs:
            svm_logger = kwargs["svm_logger"]
        # This is the heart of date identification. In the ideal case, a date column has:
        # at least pp.MIN_N_DATES_DATE_COL date col entries (n)
        # a certain ratio should be either date cells or non-numeric cells (r)
        # in case of many non-numerics, the date cells should be nicely spread (s)
        date_cols, mat = DateColIdentifier.identify_date_cols(ds)
        X = DateFiller.gen_svm_score_matrix(mat)
        prediction = DateFiller.clf.predict(X)
        inc_date_cols = pd.Series(prediction, index=mat.columns, dtype=bool)
        if svm_logger is not None:
            matrix = np.column_stack([X, inc_date_cols.values])
            for row, is_date in zip(matrix, date_cols.values):
                if not is_date:
                    svm_logger.info(", ".join([str(el) for el in row]))
                else:
                    pass
        inc_date_cols = inc_date_cols & (date_cols == False)
        # Mark the date entries in the date cols
        DateColIdentifier.mark_date_entries(ds, inc_date_cols, mat)
        return inc_date_cols, mat

    @staticmethod
    def gen_svm_score_matrix(mat):
        # Calculate the date score
        bool_mat = mat == 1
        n_date_cells = bool_mat.sum(axis=0)
        n_numeric_non_dates = (mat == 0).sum(axis=0)

        n_score_raw = n_date_cells

        r_score_raw = n_numeric_non_dates
        # now compute the more complex s_score
        np_d_temp = np.ones(len(mat.columns))
        np_s_temp = np.ones(len(mat.columns))
        np_temp = np.zeros(len(mat.columns))
        for name, col in mat.iteritems():
            bool_col = col.values != 1
            components, n_comp = label(bool_col, return_num=True)
            if n_comp > 3:
                # get component sizes
                comp_sizes = np.sort(([np.sum(components == i) for i in range(1, n_comp + 1)]))
                # compare the two biggest
                deviation = comp_sizes[-1] / comp_sizes[-2]
                np_d_temp[mat.columns.get_loc(name)] = deviation - 1
                np_s_temp[mat.columns.get_loc(name)] = np.abs(n_comp - n_date_cells[name])
                temp_val = np.exp(-deviation / 3 - np.abs(n_comp - n_date_cells[name]) / n_date_cells[name])
                np_temp[mat.columns.get_loc(name)] = temp_val

        X = np.column_stack([n_score_raw.values, r_score_raw.values, np_d_temp, np_s_temp])
        return X
