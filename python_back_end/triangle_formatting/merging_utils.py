import copy
import pickle
import jsonpickle
import numpy as np
import pandas as pd
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.triangle_formatting.header_finder import TriangleHeaderFinder
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
import logging
from python_back_end.utilities.help_functions import ExhaustiveSubsetMaker
from python_back_end.triangle_formatting.triangle_finder import TriangleFinder
from python_back_end.utilities.state_handling import DataHolder, DataStruct
from python_back_end.exceptions import *


class HorizontalMerger:
    """
    Merges some DataStructs appearing in one excel-sheet horizontally, depending on a number of metrics.
    A horizontal merge may include a vertical merge in case one DataStruct is merged horizontally with a set of
    vertically stacked DataStructs.
    """

    @staticmethod
    def horizontal_merge(dh):
        left_merges = HorizontalMerger.identify_merge_potential(dh)
        right_merges = HorizontalMerger.identify_merge_potential(dh, direction="right")
        # merge left and right to one dict
        if len(left_merges) + len(right_merges) == 0:
            return dh
        merges = copy.deepcopy(left_merges)
        for key, val in zip(right_merges.keys(), right_merges.values()):
            if key in merges:
                merges[key].update(val)
            else:
                merges[key] = val
        distances = HorizontalMerger.horizontal_merge_distances(dh, merges)
        if distances[0][0] > pp.MAX_HORIZONTAL_MERGE_DISTANCE:
            # do nothing!
            return dh
        else:
            new_dh = HorizontalMerger.perform_horizontal_merge(dh, distances)
            return new_dh

    @staticmethod
    def perform_horizontal_merge(dh, distances):
        new_dh = DataHolder(dh.name)
        # make a greedy merge
        merged_set = set()
        for part in distances:
            if part[0] > pp.MAX_HORIZONTAL_MERGE_DISTANCE:
                break
            merge = [part[1]] + part[2]
            if len(set(merge).intersection(merged_set)) == 0:
                if len(part[2]) > 1:
                    # Merge vertically!
                    df_data_list = [dh.id_dict[df_id].df_data for df_id in part[2]]
                    df_profiles_list = [dh.id_dict[df_id].df_profiles for df_id in part[2]]
                    df_data = pd.concat(df_data_list, axis=0, sort=True)
                    df_profiles = pd.concat(df_profiles_list, axis=0, sort=True)
                else:
                    df_data = dh.id_dict[part[2][0]].df_data
                    df_profiles = dh.id_dict[part[2][0]].df_profiles
                df_data = pd.concat([dh.id_dict[part[1]].df_data, df_data], axis=1, sort=True)
                df_profiles = pd.concat([dh.id_dict[part[1]].df_profiles, df_profiles], axis=1, sort=True)
                df_data = df_data.reindex(sorted(df_data.columns), axis=1)
                df_profiles = df_profiles.reindex(sorted(df_profiles.columns), axis=1)
                merged_set.update(merge)
                new_dh.add_sheet(dh.id_dict[merge[0]].name, df_data, df_profiles,
                                 orig_sheet_name=dh.id_dict[merge[0]].orig_sheet_name)
        # add the remaining
        for id_key in dh.id_dict:
            if id_key not in merged_set:
                new_dh.add_sheet(dh.id_dict[id_key].name, dh.id_dict[id_key].df_data,
                                 dh.id_dict[id_key].df_profiles,
                                 orig_sheet_name=dh.id_dict[id_key].orig_sheet_name)
        return new_dh

    @staticmethod
    def horizontal_merge_distances(dh, merges):
        distances = list()
        for key in merges:
            for val in merges[key]:
                # First make the index distance (the most important one)
                index_score = HorizontalMerger.index_score(dh, key, val)
                coherence_score = HorizontalMerger.coherent_cols_score(dh, val)
                triangle_score = HorizontalMerger.double_triangle_score(dh, key, val)
                distance = 1 - (index_score * coherence_score * triangle_score)
                distances.append([distance, key, [el for el in val]])
        # sort with first index
        distances.sort(key=lambda tup: tup[0])
        return distances

    @staticmethod
    def double_triangle_score(dh, key, val):
        if len(val) > 1:
            return 0
        key_ds = dh.id_dict[key]
        val_ds = dh.id_dict[val[0]]
        key_headers, dummy = TriangleHeaderFinder.find_ds_headers(key_ds)
        key_headers = set(key_headers.values.flatten().tolist())
        val_headers, dummy = TriangleHeaderFinder.find_ds_headers(val_ds)
        val_headers = set(val_headers.values.flatten().tolist())
        score = 1 - len(key_headers.intersection(val_headers))/np.minimum(len(val_headers), len(key_headers))
        return score

    @staticmethod
    def index_score(dh, key, val):
        key_indices = dh.id_dict[key].df_data.index
        n_id = len(key_indices)
        key_indices = (key_indices[0], key_indices[-1])
        val_indices = np.array([item for el in val for item in dh.id_dict[el].df_data.index])
        val_indices = (np.min(val_indices), np.max(val_indices))
        index_distance = np.abs(key_indices[0] - val_indices[0]) + np.abs(key_indices[1] - val_indices[1])
        index_distance /= np.sqrt(n_id)
        index_score = np.exp(-index_distance)
        return index_score

    @staticmethod
    def coherent_cols_score(dh, val):
        if len(val) == 1:
            return 1
        else:
            # check the coherence of the cols
            col_sets = [set(dh.id_dict[el].df_data.columns) for el in val]
            all = col_sets[0].copy()
            for col_set in col_sets[1:]:
                all.update(col_set)
            distance = 0
            for col_set in col_sets:
                distance += len(all.difference(col_set))
            distance /= np.sqrt(len(all))
            score = np.exp(-distance)
            return score

    @staticmethod
    def identify_merge_potential(dh, direction="left", transpose=False):
        """
        Method that identify possible horizontal merges in a direction. Can detect vertical merges using transpose. Does not perform any merges.
        :param dh: A DataHolder object
        :param direction: Default (left) means that we start at each DataStruct and check if we can merge it horizontally with one or more DataStructs that are to the left.
        :param transpose: Default (False) means that we look for horizontal merges. With true, we look for vertical merges.
        :return merges: A dictionary of potential merges, where each key is a DataStruct id and each value a set of tuples of DataStruct ids.
        """
        # find all mergeable ranges on the index side
        if transpose:
            dh = dh.copy_without_memory()
            for ds in dh.data_struct_list:
                ds.df_data = ds.df_data.T

        merges = dict()
        for ds_list in dh.data_dict.values():
            # make a matrix of ids to find spatial correspondence
            # get full width and height
            index_set = set()
            columns_set = set()
            for ds in ds_list:
                index_set.update(ds.df_data.index)
                columns_set.update(ds.df_data.columns)
            spatial_ids = pd.DataFrame(0, columns=sorted(list(columns_set)), index=sorted(list(index_set)))
            for ds in ds_list:
                spatial_ids.loc[ds.df_data.index, ds.df_data.columns] = ds.id

            for ds in ds_list:
                merge = set()
                # This set remembers the indices for which we've already ran into barriers
                met_indices = set()
                index_set = set(ds.df_data.index)
                if direction == "left":
                    dir_col = ds.df_data.columns[0]
                    dir_col_ind = list(spatial_ids.columns).index(dir_col) - 1
                    condition = dir_col_ind >= 0 and len(index_set) > 0
                elif direction == "right":
                    dir_col = ds.df_data.columns[-1]
                    dir_col_ind = list(spatial_ids.columns).index(dir_col) + 1
                    condition = dir_col_ind < spatial_ids.shape[1] and len(index_set) > 0
                while condition:
                    next = spatial_ids.loc[list(index_set), spatial_ids.columns[dir_col_ind]]
                    not_null = next != 0
                    next_indices = next[not_null].index
                    index_set = index_set.difference(next_indices)
                    # next met ids are the ids that we cannot incorporate since they are behind barriers
                    next_met_ids = spatial_ids.loc[list(met_indices), spatial_ids.columns[dir_col_ind]]

                    next_unmet_ids = set(next[not_null].values).difference(next_met_ids)

                    merge.update(next_unmet_ids)

                    met_indices.update(next_indices)
                    if direction == "left":
                        dir_col_ind -= 1
                        condition = dir_col_ind >= 0 and len(index_set) > 0
                    elif direction == "right":
                        dir_col_ind += 1
                        condition = dir_col_ind < spatial_ids.shape[1] and len(index_set) > 0
                if len(merge) > 0:
                    merges[ds.id] = set()
                    # make all combinations of merge
                    subsets = ExhaustiveSubsetMaker.sub_sets(merge)[1:]
                    for set_list in subsets:
                        tup = tuple(sorted(set_list))
                        merges[ds.id].add(tup)
        return merges


class VerticalMerger:
    clf = None
    with open(pdir.RESOURCES_DIR + '/svm_learning_data/vertical_svm.pickle', 'rb') as temp_file:
        clf = jsonpickle.decode(pickle.load(temp_file))

    @staticmethod
    def vertical_merge(dh, **kwargs):
        merges = HorizontalMerger.identify_merge_potential(dh, direction="right", transpose=True)
        if len(merges) == 0:
            return dh
        distances = VerticalMerger.vertical_merge_distances(dh, merges, **kwargs)
        if distances[0][0] < 0:
            # do nothing!
            return dh
        else:
            # make a greedy merge
            new_dh = VerticalMerger.greedy_merge(dh, distances)
            if new_dh.n == dh.n:
                return new_dh
            else:
                return VerticalMerger.vertical_merge(new_dh)

    @staticmethod
    def greedy_merge(dh, distances):
        merges_list = list()
        for part in distances:
            if part[0] < 0:
                break
            merge = [part[1]] + part[2]
            if len(part[2]) > 1:
                raise NotImplementedCaseException(dh)
            else:
                # make merges list, first check if key is the last element in an existing merge
                key_taken = np.array([merge[0] in el[:-1] for el in merges_list])
                val_taken = np.array([merge[-1] in el[1:] for el in merges_list])
                if not (any(key_taken) or any(val_taken)):
                    key_last = np.array([merge[0] == el[-1] for el in merges_list])
                    val_first = np.array([merge[-1] == el[0] for el in merges_list])
                    if np.sum(key_last) > 1 or np.sum(val_first) > 1:
                        raise ValueError
                    # now try the four natural cases
                    elif np.sum(key_last) == 1 and np.sum(val_first) == 0:
                        pre_ind = np.where(key_last)[0][0]
                        merges_list[pre_ind].append(merge[-1])

                    elif np.sum(key_last) == 0 and np.sum(val_first) == 1:
                        post_ind = np.where(val_first)[0][0]
                        merges_list[post_ind].insert(0, merge[0])
                    elif np.sum(key_last) == 1 and np.sum(val_first) == 1:
                        pre_list = merges_list[np.where(key_last)[0][0]]
                        post_list = merges_list[np.where(val_first)[0][0]]
                        temp_list = pre_list + post_list
                        merges_list.remove(pre_list)
                        merges_list.remove(post_list)
                        merges_list.append(temp_list)
                    else:
                        # add a new merge to the merges list
                        merges_list.append(merge)
        set_merges = set()
        for merge in merges_list:
            set_merges.update(merge)
        for key in dh.id_dict:
            if key not in set_merges:
                merges_list.append([key])

        new_dh = VerticalMerger.merge_with_merges_list(dh, merges_list)
        return new_dh

    @staticmethod
    def vertical_merge_distances(dh, merges, **kwargs):
        svm_logger = None
        if "svm_logger" in kwargs:
            svm_logger = kwargs["svm_logger"]
        # Check many aspects
        # How can dfs be merged and achieve maximal overlap in data types (done)?
        # in headers? (done)
        # in length? (removed, since two similar to headers)
        # in category names
        # distance matrix: Probability that i is directly over j

        distances = list()
        for key in merges:
            # Only consider simple 1+1 merges
            for val in merges[key]:
                if len(val) == 1:
                    val = val[0]
                    len_score, l_unaltered = VerticalMerger.len_score(dh, key, val)
                    header_score, h_unaltered = VerticalMerger.header_score(dh, key, val)
                    type_score, t_unaltered = VerticalMerger.type_score(dh, key, val)
                    category_score, c_unaltered = VerticalMerger.category_score(dh, key, val)
                    triangle_score, tr_unaltered = VerticalMerger.triangle_score(dh, key, val)
                    distance = 1 - np.prod([len_score, header_score, type_score, category_score, triangle_score])

                    temp = [[l_unaltered, h_unaltered, t_unaltered, c_unaltered, tr_unaltered]]
                    #print(VerticalMerger.clf.decision_function(temp))
                    distances.append([VerticalMerger.clf.decision_function(temp), key, [val]])
                    if svm_logger is not None:
                        outcome = int(distance <= pp.MAX_VERTICAL_MERGE_DISTANCE)
                        metric_list = [l_unaltered, h_unaltered, t_unaltered, c_unaltered, tr_unaltered]
                        svm_logger.info(', '.join(str(m) for m in metric_list))


        # sort with first index
        distances.sort(key=lambda tup: tup[0], reverse=True)
        return distances

    @staticmethod
    def triangle_score(dh, key, val):
        ds_key = dh.id_dict[key]
        ds_val = dh.id_dict[val]
        concat_data = pd.concat([ds_key.df_data, ds_val.df_data], sort=True)
        concat_prof = pd.concat([ds_key.df_profiles, ds_val.df_profiles], sort=True)
        concat_ds = DataStruct(concat_data, concat_prof, "temp")

        ind1 = TriangleFinder.is_triangle(ds_key, yield_float=True)
        ind2 = TriangleFinder.is_triangle(ds_val, yield_float=True)
        ind3 = TriangleFinder.is_triangle(concat_ds, yield_float=True)
        total = (ind1+ind2)/2 - ind3
        return np.exp(-total), ind1+ind2

    @staticmethod
    def len_score(dh, key, val):
        key_ds = dh.id_dict[key]
        val_ds = dh.id_dict[val]
        # Check if headers parses to string
        key_headers = list(key_ds.df_data.columns)
        val_headers = list(val_ds.df_data.columns)
        if(key_headers[0][0:pp.N_DIGITS_HEADER_PADDING].isdigit()):
            start_diff = np.abs(
                int(key_headers[0][0:pp.N_DIGITS_HEADER_PADDING]) - int(val_headers[0][0:pp.N_DIGITS_HEADER_PADDING])) - 1
            start_diff = np.maximum(start_diff, 0)
            end_diff = np.abs(
                int(key_headers[-1][0:pp.N_DIGITS_HEADER_PADDING]) - int(val_headers[-1][0:pp.N_DIGITS_HEADER_PADDING])) - 1
            end_diff = np.maximum(end_diff, 0)
            dist = np.exp(-(start_diff + end_diff) / 2)
            return dist, start_diff + end_diff
        else:
            return pp.DISTANCE_UNDEFINED_DEFAULT, pp.DISTANCE_UNDEFINED_DEFAULT


    @staticmethod
    def header_score(dh, key, val):
        i_set = set(dh.id_dict[key].df_data.columns)
        j_set = set(dh.id_dict[val].df_data.columns)
        dist = np.exp(-len(j_set.difference(i_set)) / 2)
        return dist, len(j_set.difference(i_set))

    @staticmethod
    def type_score(dh, key, val):
        i_prof = np.mean(dh.id_dict[key].df_profiles.values, axis=0)
        i_len = len(i_prof)
        j_prof = np.mean(dh.id_dict[val].df_profiles.values, axis=0)
        j_len = len(j_prof)
        if i_len != j_len:
            if i_len > j_len:
                longer = i_prof
                shorter = j_prof
            elif i_len < j_len:
                longer = j_prof
                shorter = i_prof
            diff_list = [np.linalg.norm(longer[k:len(shorter) + k] - shorter) for k in
                         range(len(longer) - len(shorter) + 1)]
            diff = np.min(diff_list) / np.sqrt(len(shorter))
        else:
            diff = np.linalg.norm(i_prof - j_prof)
        # it can fall out baldy also in well mannered cases, therefore large constant
        dist = np.exp(-diff/5)
        return dist, diff

    @staticmethod
    def category_score(dh, key, val):
        i_str_cols = TypeColExtracter.extract_string_cols(dh.id_dict[key])
        j_str_cols = TypeColExtracter.extract_string_cols(dh.id_dict[val])
        if i_str_cols.size > 0 and j_str_cols.size > 0:
            i_str_set = set(
                np.array([dh.id_dict[key].df_data[col].values for col in i_str_cols.columns]).flatten())

            j_str_set = set(np.array(
                [dh.id_dict[val].df_data[col].values for col in j_str_cols.columns]).flatten())
            diff = j_str_set.symmetric_difference(i_str_set)
            union = j_str_set.union(i_str_set)
            # remove objects that aren't equal to themselves
            diff = {x for x in diff if x == x}
            dist = np.exp(-len(diff) / 4)
            return dist, len(diff)/len(union)
        else:
            return 0.5, 0.5

    @staticmethod
    def reduce_dist_matrix(total_distance):
        ax0 = np.min(total_distance, axis=0)
        ax1 = np.min(total_distance, axis=1)
        inds = np.arange(0, len(ax0), dtype=int)
        incoming_set = set(inds[ax0 < pp.MAX_VERTICAL_MERGE_DISTANCE])
        outgoing_set = set(inds[ax1 < pp.MAX_VERTICAL_MERGE_DISTANCE])
        # source_set = outgoing_set.difference(incoming_set)
        # sink_set = incoming_set.difference(outgoing_set)
        viable = sorted(list(incoming_set.union(outgoing_set)))
        #back_trans = {key: val for val, key in enumerate(viable)}
        if len(viable) > 0:
            graph = total_distance[viable, :]
            graph = graph[:, viable]
            return graph, viable, list(set(inds).difference(viable))
        else:
            return [], viable, inds

    @staticmethod
    def merge_with_merges_list(dh, merges):
        new_dh = DataHolder(dh.name)
        for merge in merges:
            profiles = None
            data = None
            name_set = set()
            for ind in merge:

                ds = dh.id_dict[ind]
                name_set.update([ds.name])
                if profiles is None:
                    profiles = ds.df_profiles.copy()
                    data = ds.df_data.copy()
                else:
                    temp_profiles = ds.df_profiles.copy()
                    temp_data = ds.df_data.copy()
                    # TODO: generalize to other positions then the first position
                    #if profiles.shape[1] > temp_profiles.shape[1]:
                    #    for header in profiles.columns[temp_profiles.shape[1]:]:
                    #        temp_profiles[header] = SheetTypeDefinitions.ZERO_FLOAT
                    #        temp_data[header] = 0.0
                    profiles = pd.concat([profiles, temp_profiles], sort=True)
                    profiles.fillna(SheetTypeDefinitions.ZERO_FLOAT, inplace=True)
                    data = pd.concat([data, temp_data], sort=True)
            new_dh.add_sheet("_".join(list(name_set)), data, profiles, orig_sheet_name=ds.orig_sheet_name)
        return new_dh


class SheetMerger:
    pass
