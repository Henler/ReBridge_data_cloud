import numpy as np
from skimage.measure import label
import pandas as pd
from python_back_end.exceptions import *
from python_back_end.triangle_formatting.merging_utils import HorizontalMerger, VerticalMerger
from python_back_end.utilities.help_functions import mad
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.definitions import SheetTypeDefinitions
from difflib import SequenceMatcher
from scipy.stats import mannwhitneyu
import logging
import pickle
import re


class SheetPreProcessor:

    @staticmethod
    def pre_strip(dh):
        """
        This method removes empty rows and other unnecessary junk
        :param dh:
        :return:
        """
        # Remove order col
        for ds in dh:
            for col in ds.df_data.columns:
                if ps.ORDER_COL_NAME in col:
                    del ds.df_data[col]
                    del ds.df_profiles[col]
                    break

        # Remove empty cols
        for ds in dh:
            ds.df_data = ds.df_data.loc[:, (ds.df_profiles != SheetTypeDefinitions.EMPTY_STRING).any(axis=0)]
            ds.df_profiles = ds.df_profiles.loc[:, (ds.df_profiles != SheetTypeDefinitions.EMPTY_STRING).any(axis=0)]

        # Remove empty rows
        for ds in dh:
            ds.df_data = ds.df_data.loc[(ds.df_profiles != SheetTypeDefinitions.EMPTY_STRING).any(axis=1), :]
            ds.df_profiles = ds.df_profiles.loc[(ds.df_profiles != SheetTypeDefinitions.EMPTY_STRING).any(axis=1), :]
        return dh


class InputMatcher:
    # Here are the pre-defined input type. Each maps to a list of regexes.
    input_dicts = {
        ps.CAT_RESERVED_NAME: ["reserved", "claim - reserved", "outstanding", "o/s", "suspense"],
        ps.CAT_PAID_NAME: ["paid", "claim - paid", "payment"],
        ps.CAT_PREMIUM_NAME: ["premium"]
    }
    banlist = ["earned", "ratio"]
    BINNR = 9
    BINS = np.linspace(-5, 5, BINNR + 1)


    @staticmethod
    def match_triangles_to_output(usr_def_trng, dh):
        InputMatcher.set_fit_for_output(dh)
        with open(pdir.RESOURCES_DIR + "/distribution_dict.pickle", 'rb') as handle:
            distr = pickle.load(handle)
        for trng in usr_def_trng:

            #find catetgory names
            cat_names = [cat for cat in trng["categories"] if trng["categories"][cat]["type"] == "independent"]
            # pick out the ids belonging to right card
            ids_in_card = [key for key in dh.id_dict if (dh.id_dict[key].card_id == trng["group_id"] and dh.id_dict[key].fit_for_output)]
            df_matches = pd.DataFrame(0.0, index=ids_in_card, columns=cat_names)

            for cat in cat_names:
                assert cat in InputMatcher.input_dicts
                for id_key in ids_in_card:
                    if dh.id_dict[id_key].fit_for_output:
                        name_score = InputMatcher.compare_names(id_key, cat, dh)
                        if trng['type'] == 'aggregate':
                            dist_score = InputMatcher.compare_with_distribution(id_key, cat, dh, distr)
                            df_matches.loc[id_key, cat] = name_score * np.sqrt(dist_score)
                        else:
                            df_matches.loc[id_key, cat] = name_score
            # make greedy allocation

            maxes = InputMatcher.allocate_triangles_from_score(df_matches)

            trng["connection"] = dict()
            for cat in trng["categories"]:
                trng["connection"][cat] = []

            for cat, ds_id in maxes.iteritems():
                if ds_id not in trng["connection"][cat]:
                    trng["connection"][cat].append(ds_id)
                if cat not in dh.id_dict[ds_id].roles:
                    dh.id_dict[ds_id].roles.append(cat)

        return usr_def_trng

    @staticmethod
    def allocate_triangles_from_score(df_matches):
        """
        Allocates input-triangles to an output triangle semi-greedily, so that each input is used at most once if possible.
        :param df_matches:
        :return:
        """
        if df_matches.shape[1] > df_matches.shape[0]:
            return df_matches.idxmax(axis=0)
        df_matches_shrinking = df_matches.copy()

        outputs = pd.Series("not_set", index=df_matches_shrinking.columns)
        #id_set = list(df_matches_shrinking.index)
        while df_matches_shrinking.size > 0:
            #if np.all(df_matches_shrinking.values == 0):
            #    return df_matches.idxmax(axis=0)

            max_id = df_matches_shrinking.max(axis=1).idxmax()
            max_cat = df_matches_shrinking.max(axis=0).idxmax()
            outputs[max_cat] = max_id
            #id_set.remove(max_id)
            df_matches_shrinking.drop(max_cat, 1, inplace=True)
            df_matches_shrinking.drop(max_id, 0, inplace=True)

        return outputs

    @staticmethod
    def set_fit_for_output(dh):
        # check that array has numeric entries
        for ds in dh:
            types = ds.df_profiles.iloc[0, :]
            tr_cols = (types == SheetTypeDefinitions.TRIANGLE_ELEMENT).any()
            if not tr_cols:
                ds.fit_for_output = False

        # Check that the array is numeric
        # for ds in dh.data_struct_list:
        #     temp_col_names = ds.df_profiles.columns[
        #         (ds.df_profiles == SheetTypeDefinitions.TRIANGLE_ELEMENT).all()]
        #     values = ds.df_data[temp_col_names].values.flatten()
        #     try:
        #         values[values != 0].astype(float)
        #     except ValueError:
        #         ds.set_fit_for_output(False)

        # Check size consistency per card
        # 1.Find all header types per card.
        card_header_types = {ds.card_id: [] for ds in dh}
        for ds in dh:
            #assert hasattr(ds, "card_id")
            # check whether headers are padded
            # change to just store shape
            if ds.fit_for_output:
                shape_str = InputMatcher.make_triangle_shape_str(ds)
                card_header_types[ds.card_id].append(shape_str)
            #
            #
            # if all(InputMatcher.headers_are_padded(ds.df_data.columns)):
            #     headers_list = [head[pp.N_DIGITS_HEADER_PADDING + 1:] for head in ds.df_data.columns]
            # else:
            #     headers_list = [str(head) for head in ds.df_data.columns]
            # if ds.card_id not in card_header_types:
            #     card_header_types[ds.card_id] = ["_".join(headers_list) + str(ds.df_data.shape)]
            # else:
            #     card_header_types[ds.card_id].append("_".join(headers_list) + str(ds.df_data.shape))
        # 2. Identify majority header
        for key in card_header_types:
            temp_array = np.array(card_header_types[key])
            unique, counts = np.unique(temp_array, return_counts=True)
            # check if its a tie
            maximal_els = unique[counts == np.max(counts)]
            if len(maximal_els) > 1:
                nums = [int(el.split(", ")[0]) for el in maximal_els]
                leader = maximal_els[np.argmax(nums)]
            else:
                leader = maximal_els[0]
            # 3. ban the rest
            for ds in dh:
                if ds.card_id == key:
                    # if all(InputMatcher.headers_are_padded(ds.df_data.columns)):
                    #     headers_list = [head[pp.N_DIGITS_HEADER_PADDING + 1:] for head in ds.df_data.columns]
                    # else:
                    #     headers_list = [str(head) for head in ds.df_data.columns]
                    # key_string = "_".join(headers_list) + str(ds.df_data.shape)
                    shape_str = InputMatcher.make_triangle_shape_str(ds)
                    if not shape_str == leader:
                        ds.set_fit_for_output(False)

    @staticmethod
    def make_triangle_shape_str(ds):
        types = ds.df_profiles.iloc[0, :]
        n_cols = (types == SheetTypeDefinitions.TRIANGLE_ELEMENT).sum()
        n_rows = ds.df_data.shape[0]
        shape_str = str(n_rows) + ", " + str(n_cols)
        return shape_str

    @staticmethod
    def headers_are_padded(headers):
        bools = [bool(re.match(r"\b[0-9][0-9][0-9]\. ", str(header))) for header in headers]
        return bools

    @staticmethod
    def compare_names(id_key, category, dh):
        max_score = 0
        name = dh.id_dict[id_key].name
        for tentative_name in InputMatcher.input_dicts[category]:
                score = SequenceMatcher(None, tentative_name, name.lower()).ratio()
                banned = [ban in name.lower() for ban in InputMatcher.banlist]
                if any(banned):
                    score = 0
                if score > max_score:
                    max_score = score
        return max_score

    @staticmethod
    def compare_with_distribution(id_key, category, dh, distr):
        data_struct = dh.id_dict[id_key]
        cat_dist = distr[category]
        #cat_dist = cat_dist/np.sum(cat_dist)
        temp_col_names = data_struct.df_profiles.columns[(data_struct.df_profiles == SheetTypeDefinitions.TRIANGLE_ELEMENT).all()]
        values = data_struct.df_data[temp_col_names].values.flatten()
        if len(values) == 0:
            data_struct.set_fit_for_output(False)
            return 0
        try:
            values = values[values != 0].astype(float)
        except ValueError:
            raise NonNumericTriangleEntries(dh)
        if len(values) == 0:
            logger = logging.getLogger("data_cloud_logger")
            logger.warning("Triangle without entries detected")
            return 0
        elif (values == values[0]).all():
            logger = logging.getLogger("data_cloud_logger")
            logger.warning("Triangle with constant entries detected")
        else:
            values = values / mad(values)

        values = values - np.mean(values)
        score = mannwhitneyu(values, cat_dist, alternative="two-sided").pvalue
        # id_distr = plt.hist(values, InputMatcher.BINS)[0]
        # id_distr = id_distr/np.sum(id_distr)
        # score = np.exp(-np.linalg.norm(cat_dist-id_distr))
        # fig, ax = plt.subplots()
        # ax.hist(values, bins=InputMatcher.BINS)
        # print(os.getcwd())
        # fig.savefig("table_cleaning/resources/temp/" + data_struct.orig_sheet_name + data_struct.name.replace("/", "_") + "_distribution.pdf")
        return score


