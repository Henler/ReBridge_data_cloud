import numpy as np
import pandas as pd
from skimage.measure import label
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
from python_back_end.definitions import SheetTypeDefinitions
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.triangle_formatting.header_finder import TriangleHeaderFinder
from python_back_end.utilities.help_functions import strict_index
from python_back_end.utilities.state_handling import DataHolder


class TriangleFinder:

    @staticmethod
    def find_triangles(dh, **kwargs):
        return_meta = False
        if 'return_meta' in kwargs:
            return_meta = kwargs['return_meta']

        triangle_dh = DataHolder(dh.name)
        rest_dh = DataHolder(dh.name + '_non-triangular')
        #bool_array = np.zeros(triangle_dh.n, dtype=bool)
        for dh_ind, ds in enumerate(dh.data_struct_list):
            df_data, df_profiles = ds.df_data, ds.df_profiles
            # now select triangles in som smart way
            bool = TriangleFinder.is_triangle(ds, **kwargs)
            if bool:
                TriangleFinder.add_triangle_to_dh(ds, triangle_dh)
            else:
                rest_dh.add_sheet(ds.name, df_data, df_profiles, orig_sheet_name=ds.orig_sheet_name)
        # Now get the triangle similiar data structs
        triangle_similar = TriangleFinder.find_triangles_by_similarity(triangle_dh, rest_dh)
        if len(triangle_similar) > 0:
            rest_copy = rest_dh.copy_without_memory()
            rest_dh = DataHolder(rest_copy.name)
            for ds in rest_copy:
                if ds.id in triangle_similar:
                    TriangleFinder.add_triangle_to_dh(ds, triangle_dh)
                else:
                    rest_dh.add_sheet(ds.name, ds.df_data, ds.df_profiles, orig_sheet_name=ds.orig_sheet_name)
        if return_meta:
            return triangle_dh, rest_dh
        else:
            return triangle_dh

    @staticmethod
    def add_triangle_to_dh(ds, triangle_dh):
        df_data_temp = ds.df_data.fillna(0.0)
        df_profiles_temp = ds.df_profiles.loc[df_data_temp.index, df_data_temp.columns]
        df_zeros = df_data_temp == 0.0
        # Doing this in numpy since pandas is bitchin' on windows
        profiles_array = df_profiles_temp.values
        profiles_array[df_zeros.values] = SheetTypeDefinitions.ZERO_FLOAT
        df_profiles_temp = pd.DataFrame(profiles_array, columns=df_profiles_temp.columns, index=df_profiles_temp.index)
        triangle_dh.add_sheet(ds.name, df_data_temp, df_profiles_temp, orig_sheet_name=ds.orig_sheet_name)

    @staticmethod
    def find_triangles_by_similarity(triangle_dh, rest_dh):
        # Double loop and check similarity
        if triangle_dh.n == 0 or rest_dh.n == 0:
            return []

        #avoid double work by first locating all headers
        header_dict = dict()
        for rest_ds in rest_dh:
            rest_headers, dummy = TriangleHeaderFinder.find_ds_headers(rest_ds)
            header_dict[rest_ds.id] = set(rest_headers)

        for tri_ds in triangle_dh:
            tri_headers, dummy = TriangleHeaderFinder.find_ds_headers(tri_ds)
            header_dict[tri_ds.id] = set(tri_headers)

        triangle_similar = list()
        for rest_ds in rest_dh:
            for tri_ds in triangle_dh:

                shape_sim = np.exp(-np.linalg.norm(np.array(tri_ds.df_data.shape) - np.array(rest_ds.df_data.shape)))
                if len(header_dict[rest_ds.id]) < 4 or len(header_dict[tri_ds.id]) < 4:
                    header_sim = 0
                else:
                    all_headers = header_dict[tri_ds.id].union(header_dict[rest_ds.id])
                    intersection_headers = header_dict[tri_ds.id].intersection(header_dict[rest_ds.id])
                    header_sim = np.exp(-(len(all_headers) - len(intersection_headers)))
                sim = header_sim * shape_sim
                if sim > pp.MIN_TRIANGLE_SIMILARITY:
                    if rest_ds.id not in triangle_similar:
                        triangle_similar.append(rest_ds.id)
        return triangle_similar

    @staticmethod
    def is_triangle(ds, **kwargs):
        df = ds.df_data
        yield_float = False
        test_settings = False
        if 'yield_float' in kwargs:
            yield_float = kwargs['yield_float']
        if 'test_settings' in kwargs:
            test_settings = kwargs['test_settings']
        if df.shape[0] <= pp.MIN_ROWS_TRIANGLE and not test_settings:
            if yield_float:
                return 0
            else:
                return False
        else:
            ds_copy = ds.nan_filled_copy()
            df_data, df_profiles = ds_copy.df_data, ds_copy.df_profiles,
            zeroed = TypeColExtracter.extract_num_cols(df_data, df_profiles)
            if zeroed.shape[0] <= pp.MIN_ROWS_TRIANGLE and not test_settings:
                if yield_float:
                    return 0
                else:
                    return False
            else:
                non_zeros_sum = (zeroed != 0).values.sum()
                rows = zeroed.shape[0]
                cols = zeroed.shape[1]

                if non_zeros_sum == 0 or rows == 0 or cols ==0:
                    index = 0
                else:
                    left = TriangleFinder.gen_left_triangle(rows, cols)
                    right = TriangleFinder.gen_right_triangle(rows, cols)
                    left_sum = np.logical_and(zeroed != 0, left).values.sum()
                    right_sum = np.logical_and(zeroed != 0, right).values.sum()
                    index = np.maximum(left_sum, right_sum)/non_zeros_sum
                if yield_float:
                    return index
                else:
                    return index >= pp.TRIANGLE_THRESHOLD

    @staticmethod
    def gen_left_triangle(rows, cols):
        sequence = np.concatenate(([0], np.rint(np.linspace(0, cols-1, rows-1))))
        sequence = np.array(sequence, dtype=int)
        lower_right = np.array([[True] * (cols - i) + [False] * i for i in sequence])
        return lower_right

    @staticmethod
    def gen_right_triangle(rows, cols):
        tr = TriangleFinder.gen_left_triangle(rows, cols)
        if tr.ndim == 2:
            return np.fliplr(tr)
        else:
            return tr
