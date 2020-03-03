import numpy as np
import pandas as pd
import jsonpickle
from python_back_end.utilities.help_functions import excel_compatible_sheet_name, safe_round, right_merge_df_list
import copy
import pickle
from python_back_end.definitions import SheetTypeDefinitions
import collections


class DataStruct:
    """
    Main class for holding one sheet of data. Data is held in two pandas Data Frames one with the data and one with the
    data types (profiles).
    """

    def __init__(self, df_data, df_profiles, name, orig_sheet_name=None, roles=None, leg_id=None):
        self.df_data = df_data
        self.df_profiles = df_profiles
        self.name = name
        if orig_sheet_name is None:
            self.orig_sheet_name = name
        else:
            self.orig_sheet_name = orig_sheet_name
        self.fit_for_output = True
        if leg_id is None:
            self.id = str(id(self))
        else:
            self.id = leg_id
        if roles is None:
            self.roles = []
        else:
            self.roles = roles

    def deep_copy(self):
        return copy.deepcopy(self)

    def get_element(self, head, chrono):
        try:
            return self.df_data.at[chrono, head]
        except:
            return None

    def get_headers(self):
        return self.df_data.columns.values.tolist()

    def get_index(self):
        return self.df_data.index.values.tolist()

    def turn_serializable(self):
        self.df_data = self.df_data.to_dict(into=collections.OrderedDict)
        self.df_profiles = self.df_profiles.to_dict(into=collections.OrderedDict)

    def turn_to_dataframes(self):
        #ordered_df_data = json.loads(self.df_data, object_pairs_hook=collections.OrderedDict)
        index = next(iter(self.df_data.values())).keys()
        temp_df_data = pd.DataFrame(self.df_data, index=index, columns=self.df_data.keys())
        temp_df_data.index = temp_df_data.index.map(int)
        self.df_data = temp_df_data
        #ordered_df_profiles = json.loads(self.df_profiles, object_pairs_hook=collections.OrderedDict)
        index = next(iter(self.df_profiles.values())).keys()
        temp_df_profiles = pd.DataFrame(self.df_profiles, index=index, columns=self.df_profiles.keys())
        temp_df_profiles.index = temp_df_profiles.index.map(int)
        self.df_profiles = temp_df_profiles

    def safe_comparison(self, ds):
        """
        Compares without getting stuck on rounding errors and nans
        :param ds:
        :return:
        """
        def nan_compare(df1, df2):
            filled1 = safe_round(df1.fillna(value=0).values)
            filled2 = safe_round(df2.fillna(value=0).values)
            bools = filled1 == filled2
            return bools
        data_bools = nan_compare(self.df_data, ds.df_data)
        prof_bools = self.df_profiles.fillna(value=0).values == ds.df_profiles.fillna(value=0).values
        return data_bools, prof_bools

    def equals(self, ds):
        data_bools, prof_bools = self.safe_comparison(ds)
        equal_data = np.all(data_bools) and np.all(prof_bools)
        equal_name = self.name == ds.name and self.orig_sheet_name == ds.orig_sheet_name
        equal_meta = self.fit_for_output == ds.fit_for_output and self.roles == ds.roles
        if not equal_name:
            print("ds name mismatch")
            print("self.name: " + self.name + " ds.name: " + ds.name)
        if not equal_meta:
            print("ds meta mismatch")
        return equal_data & equal_meta & equal_name

    def nan_filled_copy(self):
        copy = self.deep_copy()
        copy.df_data = self.df_data.fillna(0)
        #copy.df_profiles = self.df_profiles.fillna(SheetTypeDefinitions.ZERO_FLOAT)
        copy.df_profiles[copy.df_data == 0] = SheetTypeDefinitions.ZERO_FLOAT
        return copy

    def col_split_ds(self):
        df_data_list = [self.df_data.loc[:, [col]] for col in self.df_data.columns]
        df_profiles_list = [self.df_profiles.loc[:, [col]] for col in self.df_profiles.columns]
        ds_list = [DataStruct(d, p, self.name, orig_sheet_name=self.orig_sheet_name) for d, p in zip(df_data_list, df_profiles_list)]
        return ds_list

    def set_fit_for_output(self, boolean):
        self.fit_for_output = boolean


class DataHolder:
    """
    Main class for holding one excel file as a collection of DataStructs. The DataStructs can be accessed in a list (no
    specific order), in a dict with ids as keys and in a dict of lists where the keys are DataStruct names (not
    necessarily unique). Has an unfinished implementation of undo through the memento pattern.
    """

    def __init__(self, name):
        self.data_dict = dict()
        self.data_struct_list = []
        self.mementos = []
        self.id_dict = dict()
        self.n = 0
        self.name = name

    def __iter__(self):
        return iter(self.data_struct_list)

    def add_sheet(self, name, df_data, df_profiles, orig_sheet_name="", roles=None, leg_id=None):
        # never add empty sheets
        if df_data.size > 0:
            ds = DataStruct(df_data, df_profiles, name, orig_sheet_name, roles, leg_id)
            self.add_ds(ds)

    def add_ds(self, ds):
        if ds.name not in self.data_dict:
            self.data_dict[ds.name] = []
        self.data_dict[ds.name].append(ds)
        self.data_struct_list.append(ds)
        self.n += 1
        assert ds.id not in self.id_dict
        self.id_dict[ds.id] = ds

    def copy_without_memory(self):
        new_dh = DataHolder(self.name)
        for ind, ds in enumerate(self.data_struct_list):
            new_dh.add_ds(ds.deep_copy())
        #for ind, df_data, df_profiles, orig_sheet_name in self.enumerate_with_orig_name():
            #new_dh.add_sheet(ds.name, ds.df_data.copy(), ds.df_profiles.copy(), orig_sheet_name=ds.orig_sheet_name, roles=ds.roles, leg_id=ds.id)
        return new_dh

    def create_memento(self):
        self.mementos.append(DataMemento(self))

    def enumerate(self):
        df_data_list = [el.df_data for el in self.data_struct_list]
        df_profiles_list = [el.df_profiles for el in self.data_struct_list]
        return zip(range(self.n), df_data_list, df_profiles_list)

    def enumerate_with_orig_name(self):
        df_data_list = [el.df_data for el in self.data_struct_list]
        df_profiles_list = [el.df_profiles for el in self.data_struct_list]
        orig_names = [el.orig_sheet_name for el in self.data_struct_list]
        return zip(range(self.n), df_data_list, df_profiles_list, orig_names)

    def update_with_ind(self, dh_ind, df_data, df_profiles):
        self.data_struct_list[dh_ind].df_data = df_data
        self.data_struct_list[dh_ind].df_profiles = df_profiles

    def serializable_copy(self):
        copy = self.copy_without_memory()
        for ds in copy.data_struct_list:
            ds.turn_serializable()
        return copy

    def data_framed_from_serializable(self):
        for ds in self.data_struct_list:
            ds.turn_to_dataframes()
        return self

    def encode(self):
        copy = self.serializable_copy()
        return jsonpickle.encode(copy)

    @staticmethod
    def decode(serial):
        decoded = jsonpickle.decode(serial)
        return decoded.data_framed_from_serializable()

    def write_excel(self, path, index=False):
        counter = 0
        used_sheet_names = set()
        with pd.ExcelWriter(path) as writer:
            for ds in self.data_struct_list:
                if (ds.orig_sheet_name is "") or (ds.orig_sheet_name in ds.name):
                    sheet_name = ds.name
                else:
                    sheet_name = ds.orig_sheet_name + "_" + ds.name
                sheet_name = excel_compatible_sheet_name(sheet_name)
                if sheet_name in used_sheet_names:
                    sheet_name = sheet_name[:-1] + str(counter)
                    counter += 1
                used_sheet_names.add(sheet_name)
                ds.df_data.to_excel(writer, sheet_name=sheet_name, index=index)
                ds.df_profiles.to_excel(writer, sheet_name=sheet_name+"_types", index=index)

    def to_pickle_file(self, path, extra_content=None):
        with open(path, "wb") as temp_file:
            if extra_content is None:
                pickle.dump(self.encode(), temp_file)
            else:
                pickle.dump({"DataHolder": self.encode(), "extra_content": extra_content}, temp_file)

    @staticmethod
    def from_pickle_file(path):
        with open(path, 'rb') as temp_file:
            serial = pickle.load(temp_file)
            dh = DataHolder.decode(serial)
            return dh

    def equals(self, dh):
        equal = True
        # check that all dictionary keys are present
        difference = set(self.data_dict.keys()).symmetric_difference(set(dh.data_dict.keys()))
        if len(difference) == 0:
            for ds1, ds2 in zip(self, dh):
                equal = ds1.equals(ds2) and equal
        else:
            print("The data holders have differently named sheets. The (symmetric)difference in names: ")
            print(difference)
            equal = False
        return equal

    def merge_in_original_sheets(self, save_sheet_names=False):
        """
        This method tries to concatenate sub-sheets back to original sheet, to make comparisons easier
        Does not conserve meta-data by now (unclear how that would be defined anyway).
        :return: DataHolder
        """
        sheet_dict = dict()
        for ds in self:
            if ds.orig_sheet_name not in sheet_dict:
                sheet_dict[ds.orig_sheet_name] = [ds]
            else:
                sheet_dict[ds.orig_sheet_name].append(ds)

        new_dh = DataHolder(self.name)
        if "" in sheet_dict:
            # in this case, orig_sheet_name is not assigned and we just use th name
            sheet_dict = self.data_dict

        for name in sheet_dict:
            df_data_list = [ds.df_data for ds in sheet_dict[name]]
            df_data = right_merge_df_list(df_data_list)
            df_profiles = right_merge_df_list([ds.df_profiles for ds in sheet_dict[name]])
            new_dh.add_sheet(name, df_data, df_profiles, orig_sheet_name=name)

        if save_sheet_names:
            data = pd.DataFrame([ds.orig_sheet_name + " " + ds.name for ds in self])
            profiles = pd.DataFrame([SheetTypeDefinitions.EMPTY_STRING]*data.size)
            new_dh.add_sheet("triangle names", data, profiles)
        return new_dh

    def join(self, dh):
        for ds in dh:
            self.add_ds(ds.deep_copy())


class DataMemento:
    def __init__(self, dh):
        self.sheet_memento_dict = dict()
        for key in dh.data_dict:
            self.sheet_memento_dict[key] = [DataStruct(struct.df_data.copy(), struct.df_profiles.copy(), key) for struct in dh.data_dict[key]]
        self.n = dh.n


class SheetStateComparer:
    class Diff:

        def __init__(self, orig, new, change):
            if orig is None:
                orig = ""
            if new is None:
                new = ""
            self.original_value = orig
            self.change = change
            self.new_value = new

    @staticmethod
    def compare_states(orig_dm, new_dm):
        # if number of sheets has changed, the comparison makes no sense
        if orig_dm.n == new_dm.n and orig_dm.sheet_memento_dict.keys() == new_dm.sheet_memento_dict.keys():
            diff_dict_list = SheetStateComparer.compare_equal_structures(orig_dm, new_dm)
        else:
            diff_dict_list = SheetStateComparer.compare_deviant_structures(orig_dm, new_dm)
        return diff_dict_list

    @staticmethod
    def compare_deviant_structures(orig_dm, new_dm):
        # To be written and tested
        return list()

    @staticmethod
    def compare_equal_structures(orig_dm, new_dm):
        diff_dict_list = list()
        for name in orig_dm.sheet_memento_dict:
            #ONLY COMPARES FIRST SHEET IN DICT FOR NOW
            orig_mem = orig_dm.sheet_memento_dict[name][0]
            new_mem = new_dm.sheet_memento_dict[name][0]
            diff_array = []
            remark_set = set()
            header_set = set(orig_mem.get_headers())
            header_set.update(new_mem.get_headers())
            num_sorted_headers = sorted([head for head in header_set])
            chrono_set = set(orig_mem.get_index())
            chrono_set.update(new_mem.get_index())
            all_chronos = sorted([chrono for chrono in chrono_set])
            #num_sorted_headers = SheetStateComparer.string_number_sort(all_headers)
            for chrono in all_chronos:
                diff_array.append([])
                for head in num_sorted_headers:
                    old = orig_mem.get_element(head, chrono)
                    new = new_mem.get_element(head, chrono)
                    case = SheetStateComparer.cases(old, new)
                    if case == "Removed and saved":
                        remark_set.add(old)
                    diff_array[-1].append(SheetStateComparer.Diff(old, new, case))

            diff_dict={
                "diff_array": diff_array,
                "headers": num_sorted_headers,
                "remarks": remark_set,
                "sheet_name": name
            }
            diff_dict_list.append(diff_dict)
            print(remark_set)
        return diff_dict_list

    @staticmethod
    def cases(old_in, new_in):
        old = old_in
        new = new_in
        if old is None and new is None:
            return "-"
        elif old is None:
            return "Added"
        elif new is None:
            if isinstance(old, str):
                if len(old) > 2:
                    return "Removed and saved"
                else:
                    return "Removed"
            else:
                return "Removed"
        elif old != new:
            try:
                if np.isnan(float(old)) and np.isnan(float(new)):
                    return "No change"
                elif round(float(old)) == round(float(new)):
                    return "No change"
                else:
                    return "Corrected"
            except:
                return "Corrected"
            # if isinstance(old, (float, np.float64)) and isinstance(new, (float, np.float64)):
            #     if round(old) != round(new):
            #         return "Corrected"
            #     else:
            #         return "No change"
            # else:
            #     return "Corrected"
        else:
            return "No change"

