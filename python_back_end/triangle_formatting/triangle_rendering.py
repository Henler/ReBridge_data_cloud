import logging
from python_back_end.exceptions import *

import numpy as np

from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.program_settings import PROGRAM_STRINGS as ps
import pandas as pd
from scipy.cluster.vq import whiten, kmeans, vq


class RowParser:

    @staticmethod
    def parse_output_from_triangle_forms(trngs, dh):

        for trng in trngs:
            # Don't try and parse from an empty triangle
            # parse the headers
            # now find the appropriate headers
            # TODO: Think about whether this is reasonable to do on a per triangle basis
            connected_ds = RowParser.get_connected_ds(trng, dh)
            if connected_ds is None:
                RowParser.fill_empty_with_zeroes(trng)
            else:
                # make things one by one from the cols dic
                # parse the right headers
                RowParser.set_trng_headers(trng, connected_ds.df_profiles.iloc[0, :])
                # Now use the cols info to parse the part of the rows that is not the triangle
                col_zip = RowParser.parse_non_triangle_columns(dh, trng, connected_ds)

                RowParser.make_rows_from_col_zip(col_zip, trng, dh)

        return trngs

    @staticmethod
    def parse_non_triangle_columns(dh, trng, connected_ds):
        cols = connected_ds.df_profiles.iloc[0, :]
        col_zip = pd.DataFrame()
        for header in trng["immutable_headers"]:
            if header == "Date of loss" or header == "Year":
                if not SheetTypeDefinitions.STRING_DATE in cols.values:
                    raise RequiredColumnsNotPresent(dh)
                date_header = RowParser.select_date_col(cols, connected_ds)
                col_zip[header] = connected_ds.df_data[date_header].values.flatten()

            if header == "Loss id":
                if SheetTypeDefinitions.ID_ELEMENT in cols.values:
                    temp_header = cols[cols == SheetTypeDefinitions.ID_ELEMENT].index
                else:
                    raise RequiredColumnsNotPresent(dh)
                temp_col = connected_ds.df_data[temp_header].values.flatten()
                col_zip[header] = temp_col
        return col_zip

    @staticmethod
    def select_date_col(cols, connected_ds):
        date_headers = cols[np.logical_or(
        cols == SheetTypeDefinitions.STRING_DATE,
        cols == SheetTypeDefinitions.XL_DATE)].index
        if len(date_headers) == 1:
            date_header = date_headers[0]
        else:
            # find the columns with the most unique entries
            col_nums = list()
            str_df_data = connected_ds.df_data.astype(str)
            for name, col in str_df_data.loc[:, date_headers].iteritems():
                unique, counts = np.unique(col.values, return_counts=True)
                if len(col_nums) > 0:
                    if len(counts) > col_nums[0][1]:
                        col_nums = [(name, len(counts))]
                    elif len(counts) == col_nums[0][1]:
                        col_nums.append((name, len(counts)))
                else:
                    col_nums = [(name, len(counts))]

            if len(col_nums) == 1:

                # now only get the ones with the most counts ...
                return col_nums[0][0]
            else:
                # ...or enter the difficult selection process
                # We select using a tournament
                old_champ = col_nums[-1][0]
                for i in range(len(col_nums)-1):
                    contester = col_nums[i][0]
                    old_champ_col = str_df_data.loc[:, old_champ]
                    contester_col = str_df_data.loc[:, contester]
                    elementwise = np.zeros(len(old_champ_col))
                    for j, old, new in zip(range(len(elementwise)), old_champ_col, contester_col):
                        min_lenght = np.minimum(len(old), len(new))
                        if new[:min_lenght] < old[:min_lenght]:
                            elementwise[j] = 1
                        elif new[:min_lenght] > old[:min_lenght]:
                            elementwise[j] = -1
                    ratio = elementwise.mean()
                    if ratio > 0:
                        old_champ = contester

                date_header = old_champ
        return date_header


    @staticmethod
    def set_trng_headers(trng, cols):
        trng["headers"] = [header for header in trng['immutable_headers']]
        temp_bool = cols == SheetTypeDefinitions.TRIANGLE_ELEMENT
        temp_headers = list(temp_bool[temp_bool].index)
        trng["headers"] = trng["headers"] + temp_headers

    @staticmethod
    def fill_empty_with_zeroes(trng):
        # Loop through dictionary and 0 rows
        for row in trng["rows"]:
            row["ids"] = list()
            change_entries = np.array([header not in trng["immutable_headers"] for header in trng["headers"]])
            values = np.array(row["values"])
            values[change_entries] = 0
            row["values"] = values.tolist()

    @staticmethod
    def make_rows_from_col_zip(col_zip, trng, dh):
        trng["rows"] = list()
        for col_ind, col in col_zip.iterrows():
            for cat_key, cat_vals in trng["categories"].items():
                row_dict = {
                    "values": col.tolist() + [cat_key],
                    "ids": []
                }
                values = None

                if cat_vals["type"] == "independent":
                    # In this case, parse from connection
                    ds_list = [dh.id_dict[ds_id] for ds_id in trng["connection"][cat_key]]
                    #if trng["connection"][cat_key] is not None:
                        #ds = dh.id_dict[trng["connection"][cat_key]]
                    for ds in ds_list:
                        row_dict["ids"].append(ds.id)
                        values = RowParser.sum_or_create_values(values, ds, col_ind)

                elif cat_vals["type"] == "sum" or cat_vals["type"] == "difference":
                    # Now go over the "from"s
                    for name in cat_vals["from"]:
                        ds_list = [dh.id_dict[ds_id] for ds_id in trng["connection"][name]]
                        #if trng["connection"][name] is not None:
                        #    ds = dh.id_dict[trng["connection"][name]]
                        for ds in ds_list:
                            if cat_vals["type"] == "sum":
                                values = RowParser.sum_or_create_values(values, ds, col_ind)
                            if cat_vals["type"] == "difference":
                                values = RowParser.subtract_or_create_values(values, ds, col_ind)
                else:
                    raise ValueError("Unknown value type recieved")
                if values is not None:
                    row_dict["values"] += values.tolist()
                else:
                    row_dict["values"] += np.zeros(len(trng["headers"])-len(row_dict["values"])).tolist()
                if len(row_dict["values"]) != len(trng["headers"]):
                    logger = logging.getLogger("data_cloud_logger")
                    logger.warning("Too many elements in row: truncates.")
                    row_dict["values"] = row_dict["values"][0:len(trng["headers"])]
                trng["rows"].append(row_dict)

    @staticmethod
    def get_connected_ds(trng, dh):
        #temp_list = list()
        #temp_ind = 0
        temp_id = None
        # Don't try and parse the cols from a category that is empty
        for id in trng["connection"].values():
            if len(id) > 0:
                temp_id = id[0]
                break
        # while len(temp_list) == 0 and temp_ind < len(trng["connection"].values()):
        #     if
        #     temp_list = list(trng["connection"].values())[temp_ind]["data_struct_ids"]
        #     temp_ind += 1
        # if len(temp_list) == 0:
        #     return None
        if temp_id is None:
            return None
        else:
            ds = dh.id_dict[temp_id]
            return ds

    @staticmethod
    def sum_or_create_values(values, ds, col_ind):
        tr_els = ds.df_profiles.iloc[[col_ind]].values.flatten() == SheetTypeDefinitions.TRIANGLE_ELEMENT
        if values is None:
            values = ds.df_data.iloc[[col_ind]].values.flatten()[tr_els]
        else:
            values += ds.df_data.iloc[[col_ind]].values.flatten()[tr_els]
        return values

    @staticmethod
    def subtract_or_create_values(values, ds, col_ind):
        tr_els = ds.df_profiles.iloc[[col_ind]].values.flatten() == SheetTypeDefinitions.TRIANGLE_ELEMENT
        if values is None:
            values = ds.df_data.iloc[[col_ind]].values.flatten()[tr_els]
        else:
            values -= ds.df_data.iloc[[col_ind]].values.flatten()[tr_els]
        return values

    @staticmethod
    def turn_cols_pretty(cols):
        pretty_cols = list()
        for ind, col in enumerate(cols):
            temp_str = DateColIdentifier.match(col, return_match=True)
            if temp_str is None:
                pretty_cols.append(ind)
            else:
                pretty_cols.append(temp_str)
        return pretty_cols

    @staticmethod
    def set_card_ids(trngs, dh):
        # check how many ids there are
        id_set = set()
        
        for trng in trngs:
            id_set.add(trng["group_id"])

        orig_sheet_names = {ds.orig_sheet_name for ds in dh}
        if len(id_set) == 1:
            # Only one output
            for ds in dh:
                ds.card_id = 0
        elif len(id_set) == len(orig_sheet_names):
            # one output per sheet
            mappings = dict()
            idx = 0
            for ds in dh:
                if ds.orig_sheet_name not in mappings:
                    mappings[ds.orig_sheet_name] = idx
                    idx += 1
                ds.card_id = mappings[ds.orig_sheet_name] % len(id_set)
        else:
            # No f---ing clue...
            # ...cluster with position!
            x_positions = np.zeros(len(dh.data_struct_list))
            for i, ds in enumerate(dh):
                x_positions[i] = np.mean([int(el[:pp.N_DIGITS_HEADER_PADDING]) for el in ds.df_data.columns])
            y_positions = np.array([np.mean(ds.df_data.index) for ds in dh])
            if np.std(x_positions) > 0:

                positions = np.transpose(np.vstack((x_positions, y_positions)))
            else:
                positions = y_positions
            positions = whiten(positions)
            codebook, distortion = kmeans(positions, len(id_set))
            code, distortion = vq(positions, codebook)
            for card_id, ds in zip(code, dh):
                ds.card_id = card_id

        return dh, list(id_set), list(orig_sheet_names)

    @staticmethod
    def make_changes(dh, trngs, change):
        for trng in trngs:
            if dh.id_dict[change['id']].card_id == trng['group_id']:

                # first remove old occurrences
                for con_key in trng['connection']:
                    if change['id'] in trng['connection'][con_key]:
                        trng['connection'][con_key].remove(change['id'])
                # Then add the new occurence
                if change['value'] in trng['categories']:
                    trng['connection'][change['value']].append(change['id'])

                # possibly change the category types
                if ps.CAT_PAID_NAME in trng['categories']:
                    # we have the case when we make an assignment to a not independent class
                    # what are the possible dependencies?
                    none_connections = [key for key in trng['connection'] if len(trng['connection'][key]) == 0]
                    if len(none_connections) == 1:
                        for key, cat_dicts in trng['categories'].items():
                            if key == none_connections[0]:
                                cat_dicts['from'] = sorted([key for key in trng['connection'] if len(trng['connection'][key]) > 0])
                                if none_connections[0] != ps.CAT_INCURRED_NAME:
                                    cat_dicts['type'] = 'difference'
                                else:
                                    cat_dicts['type'] = 'sum'
                            else:
                                cat_dicts['from'] = []
                                cat_dicts['type'] = 'independent'
                    if len(none_connections) == 0:
                        for key, cat_dicts in trng['categories'].items():
                            cat_dicts['from'] = []
                            cat_dicts['type'] = 'independent'

                    if len(none_connections) == 2:
                        if ps.CAT_INCURRED_NAME in none_connections:
                            for key, cat_dicts in trng['categories'].items():
                                if key == ps.CAT_INCURRED_NAME:
                                    cat_dicts['from'] = sorted(
                                        [key for key in trng['connection'] if len(trng['connection'][key]) > 0])
                                    cat_dicts['type'] = 'sum'
                                else:
                                    cat_dicts['from'] = []
                                    cat_dicts['type'] = 'independent'
                        else:
                            for key, cat_dicts in trng['categories'].items():
                                cat_dicts['from'] = []
                                cat_dicts['type'] = 'independent'



                # make a check
                for key in trng['categories']:
                    if trng['categories'][key]['type'] != 'independent' and key in trng['connection']:
                        if len(trng['connection'][key]) > 0:
                            raise ValueError("Dependent categories should not have a connected id")