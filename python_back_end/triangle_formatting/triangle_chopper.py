from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.utilities.state_handling import DataHolder, DataStruct
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.utilities.performance_utils import effectiveSampleSize
from skimage.measure import label
import numpy as np
import pandas as pd
from scipy.cluster.vq import whiten, kmeans, vq


class TriangleChopper:
    """
    This class chops up triangles with repeating headers
    """

    @staticmethod
    def chop_triangles(dh, **kwargs):
        dh = TriangleChopper.chop_triangles_horizontally(dh)
        dh = TriangleChopper.chop_triangles_vertically(dh, **kwargs)
        return dh

    @staticmethod
    def chop_triangles_vertically(dh, **kwargs):
        assert 'tri_type' in kwargs
        tri_type = kwargs["tri_type"]
        chop_lists = list()
        chop_bools = list()
        for ds in dh:
            chop = False
            # in case of aggregate, chop with respect to date column repetitions
            if tri_type == 'aggregate':
                # Get columns with the most date entries
                date_cols = DateColIdentifier.identify_marked_date_cols(ds)
                ds_chops = list()
                for name, col in ds.df_data[ds.df_data.columns[date_cols]].iteritems():
                    repetitions = TriangleChopper.make_repetitions_list(col.values, min_chunk_size=True)
                    if len(repetitions) > 0 and not np.all(repetitions == 0):
                        chop = True
                    ds_chops.append(repetitions)
                #ds_chops = chop_lists[ind]
                if chop:
                    cuts = [TriangleChopper.make_vertical_cuts(repetitions) for repetitions in ds_chops]
                    cut = TriangleChopper.choose_cut_list(cuts)
                else:
                    cut = []
            # in case of single loss, chop with respect to header repetitions
            else:
                cut, dummy = TriangleChopper.find_repeated_headers(ds)
                if len(cut) > 0:
                    chop = True
                    cut = np.append(cut, ds.df_data.shape[0])

            chop_lists.append(cut)
            chop_bools.append(chop)
        if any(chop_bools):
            return TriangleChopper.perform_vertical_chop(dh, chop_bools, chop_lists)
        else:
            return dh

    @staticmethod
    def find_repeated_headers(ds):
        headers = np.array([el[pp.N_DIGITS_HEADER_PADDING + 2:] for el in ds.df_data.columns])
        sim_list = ds.df_data.astype(str).eq(headers, axis=1)
        ratios = sim_list.sum(axis=1) / sim_list.shape[1]
        cut = np.where(ratios.values > pp.MIN_HEADER_SIMILARITY)[0]
        deviating_entries = set()
        for ind in cut:
            deviating_entries.update(sim_list.columns[np.logical_not(sim_list.iloc[ind, :].values)])
        #deviating_entries = [ds.df_data.columns for ind in cut]
        #if len(deviating_entries) > 0:
        #    deviating_entries = np.hstack(deviating_entries)
        return cut, np.array(list(deviating_entries))

    @staticmethod
    def perform_vertical_chop(dh, chop_bools, chop_lists):
        new_dh = DataHolder(dh.name)
        for ind, ds in enumerate(dh):
            if chop_bools[ind]:
                cut = chop_lists[ind]
                # Don't cut too much
                if len(cut) < pp.MAX_NUM_VERTICAL_CHOPS:
                    cut = [0] + cut.tolist()
                    for i in range(len(cut) - 1):
                        temp_df_data = ds.df_data.iloc[cut[i]:cut[i + 1], :]
                        temp_df_profiles = ds.df_profiles.iloc[cut[i]:cut[i + 1], :]
                        new_ds = DataStruct(temp_df_data, temp_df_profiles, ds.name, orig_sheet_name=ds.orig_sheet_name)
                        new_dh.add_ds(new_ds)
                else:
                    new_dh.add_ds(ds)
            else:
                new_dh.add_ds(ds)
        return new_dh

    @staticmethod
    def choose_cut_list(cuts):
        assert len(cuts) > 0
        if len(cuts) > 1:
            # check if cuts are identical
            identical = [np.all(cuts[i] == cuts[i + 1] for i in range(len(cuts) - 1))]
            if np.all(identical):
                # take first one
                cut = cuts[0]
            else:
                # take the shortest one
                short_ind = np.argmin([len(el) for el in cuts])
                cut = cuts[short_ind]
        else:
            cut = cuts[0]
        return cut

    @staticmethod
    def make_vertical_cuts(in_array):
        cut_list = list()
        # # Find qualified chops (never chop chunks smaller than ~8)
        # qualified = list()
        # for ind in range(1, np.max(in_array) + 1):
        #     array = label(in_array == ind)
        #     unique, counts = np.unique(array, return_counts=True)
        #
        #
        #
        for ind in range(1, np.max(in_array) + 1):
            # get last index
            cut_list.append(len(in_array) - np.argmax(in_array[::-1] == ind))
        return np.array(cut_list)

    @staticmethod
    def chop_triangles_horizontally(dh):
        """
        checks for repeating header and splits ds:s
        :param dh: DataHolder
        :return: DataHolder
        """
        chop, chop_lists = TriangleChopper.make_occurrence_list(dh)

        if not chop:
            return dh
        else:
            new_dh = DataHolder(dh.name)
            for ind, ds in enumerate(dh):
                occurrence_list = chop_lists[ind]
                if any(occurrence_list):
                    for i in range(1, np.max(occurrence_list) + 1):
                        bools = np.logical_or(occurrence_list == 0, occurrence_list == i)
                        df_data = ds.df_data[ds.df_data.columns[bools]].copy()
                        df_profiles = ds.df_profiles[ds.df_profiles.columns[bools]].copy()
                        new_dh.add_sheet(ds.name, df_data, df_profiles, orig_sheet_name=ds.orig_sheet_name)

                else:
                    new_dh.add_ds(ds)
            return new_dh

    @staticmethod
    def make_occurrence_list(dh):
        chop_lists = list()
        chop = False
        for ds in dh:
            # make list of headers
            headers_list = np.array([head[pp.N_DIGITS_HEADER_PADDING + 1:] for head in ds.df_data.columns])
            repetitions_list = TriangleChopper.make_repetitions_list(headers_list)
            ess_list = TriangleChopper.make_ess_list(ds)
            if len(repetitions_list) > 0 and len(ess_list) == 0:
                chop = True
                occurrence_list = repetitions_list
            #elif len(repetitions_list) == 0 and len(ess_list) > 0:
            #    chop = True
            #    occurrence_list = ess_list
            elif len(repetitions_list) > 0 and len(ess_list) > 0:
                chop = True
                #TODO: make a more coherent system for list choice
                #check special case where repetitions list is choppy
                changes_list = [repetitions_list[i+1] - repetitions_list[i] for i in range(len(repetitions_list)-1)]
                n_changes = np.sum(np.array(changes_list) != 0)

                class_occupancy = [np.sum(repetitions_list == i) for i in range(1, np.max(repetitions_list) + 1)]

                if n_changes > 4:
                    occurrence_list = repetitions_list
                elif class_occupancy[0] > 4 and np.std(class_occupancy) == 0:
                    occurrence_list = repetitions_list
                else:
                    occurrence_list = np.maximum(repetitions_list, ess_list)
            else:
                occurrence_list = []
            chop_lists.append(occurrence_list)

        return chop, chop_lists

    @staticmethod
    def make_ess_list(ds):
        '''
        Get ess progression to determine content
        :param ds:
        :return:
        '''
        df_num = TypeColExtracter.extract_num_cols(ds.df_data, ds.df_profiles)
        ess_series = pd.Series(0.0, index=df_num.columns)
        non_zero_series = pd.Series(0, index=df_num.columns)
        for name, col in df_num.iteritems():
            if len(col.values[col.values != 0]) == 0:
                ess_series[name] = 0
            elif np.std(col.values[col.values != 0]) > 0:
                ess_series[name] = effectiveSampleSize(col.values[col.values != 0])
            else:
                ess_series[name] = 0
            non_zero_series[name] = (col != 0).sum()
        aug_non_zero = non_zero_series.copy()
        aug_non_zero.loc[aug_non_zero == 0] = 1
        number_ratio = ess_series / aug_non_zero
        nums = (number_ratio > pp.MIN_ESS_RATIO_VALUE_COL).astype(int)
        if nums.sum() == 0:
            return []
        non_zero_series = non_zero_series.loc[nums == 1]
        # how many numbers are over mean?
        diffs = non_zero_series.iloc[1:].values - non_zero_series.iloc[:-1].values
        # only if significant contributions are in
        if np.abs(np.sum(diffs))/np.sum(np.abs(diffs)) > 0.7:
            return []
        #w_diffs = whiten(diffs)
        #codebook, distortion = kmeans(w_diffs, 2)
        #code, distortion = vq(w_diffs, codebook)
        diff_mean = np.mean(diffs)
        above = np.where(diffs >= diff_mean)[0]
        below = np.where(diffs <= diff_mean)[0]
        if len(above)/len(below) < 0.15:
            cut_inds = above + 1
        elif len(below)/len(above) < 0.15:
            cut_inds = below + 1
        else:
            return []
        #smooth cut_inds conservatively
        cut_inds = cut_inds.tolist()
        while cut_inds[0] in range(3):
            del cut_inds[0]
            if len(cut_inds) == 0:
                return []
        while cut_inds[-1] in range(len(diffs) - 2, len(diffs) + 1):
            del cut_inds[-1]
            if len(cut_inds) == 0:
                return []
        cut_inds.append(np.iinfo(np.int32).max)
        cut_inds = [cut_inds[i] for i in range(len(cut_inds)-1) if cut_inds[i] < cut_inds[i+1] -2]
        # is sum of nums divisible
        # min_cut = [-np.mean(np.abs(diffs)), 0]
        # for i in range(2, 6):
        #     if non_zero_series.size % i == 0:
        #         cut_inds = [int((non_zero_series.size / i) * j - 1) for j in range(1, i)]
        #         # now check sum
        #         temp_sum = -np.mean(np.abs(diffs[cut_inds]))
        #         if temp_sum < min_cut[0]:
        #             min_cut[0] = temp_sum
        #             min_cut[1] = i
        # if min_cut[1] == 0:
        #     return []

        temp_series = nums.loc[nums == 1].astype(int)
        for ind in cut_inds:
            temp_series[ind:] += 1
        out = pd.Series(0, index=ds.df_data.columns)
        out += temp_series
        out = out.fillna(0).astype(int)

        return out.values


    @staticmethod
    def make_repetitions_list(in_list, min_chunk_size=False):
        in_list = in_list.astype(str)
        unique, counts = np.unique(in_list, return_counts=True)
        # criterion:
        # 1) if at least half are repeated
        # 2) not too many repetitions
        # or 3) if enough repeated elements are in!
        n_repeated = len(np.where(counts > 1)[0])
        if (len(unique) <= len(in_list) * (2 / 3) and len(unique) >= pp.MIN_N_HORI_REPEATS) or n_repeated >= pp.ACCEPTED_N_HORI_REPEATS:
            #find number of repetitions
            unique_counts = counts[counts > 1]
            n_periods = np.argmax(np.bincount(unique_counts))
            unique = unique[counts < n_periods]
            occurrence_dict = dict()
            occurrence_list = np.zeros(len(in_list), dtype=int)
            for ind, head in enumerate(in_list):
                if head not in unique:
                    if head in occurrence_dict:
                        occurrence_dict[head] += 1
                        occurrence_list[ind] = occurrence_dict[head]
                    else:
                        occurrence_dict[head] = int(1)
                        occurrence_list[ind] = int(1)
            occurrence_list = TriangleChopper.smooth_occurrence_list(occurrence_list, min_chunk_size)
            return occurrence_list
        else:
            return []

    @staticmethod
    def smooth_occurrence_list(occurrence_list, min_chunk_size=False):
        # find longest period
        for i in range(1, np.max(occurrence_list) + 1):
            array = label(occurrence_list == i)
            unique, counts = np.unique(array, return_counts=True)
            # if wanted, kill all small chunks
            if min_chunk_size:
                small_array = unique[np.where(counts < pp.MIN_VERTICAL_CHUNK_SIZE)]
                for ind in small_array:
                    occurrence_list[array == ind] = 0
            # zero always wins, since it does not have to be grouped etc
            # Remove zero and the most common component
            for ind in range(2):
                dels = np.where(counts == np.max(counts))
                unique = np.delete(unique, dels)
                counts = np.delete(counts, dels)
            for ind in unique:
                occurrence_list[array == ind] = 0

        return occurrence_list