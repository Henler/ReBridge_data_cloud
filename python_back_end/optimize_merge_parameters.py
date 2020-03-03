from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.utilities.sheet_io import ExcelLoader
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.triangle_formatting.triangle_utils import SheetPreProcessor
from python_back_end.triangle_formatting.merging_utils import HorizontalMerger, VerticalMerger
import pickle
import pandas as pd
import time
import numpy as np


class MergePararametersOptimizer:

    @staticmethod
    def setup():
        """
        This function does:
        1. read and separate sheets to check
        2. read correctly merged data frames from pickle
        :return:
        """
        pass

    @staticmethod
    def evaluate(raw_dh_dict, sol_dict):
        """
        :param settings_struct:
        :param raw_dh_dict:
        :param sol_dh_dict:
        :return: fit_score (negative number of failed merges)
        :return: gap_score (sum of absolute separations to dividers)
        """
        for key in raw_dh_dict:
            raw_dh_dict[key] = HorizontalMerger.horizontal_merge(raw_dh_dict[key])
        comparison_dict = MergePararametersOptimizer.make_ind_col_dict(raw_dh_dict)

        # now go through the dictionaries and check the difference
        assert comparison_dict.keys() == sol_dict.keys()
        for file_key in comparison_dict:
            for tuple_key in sol_dict[file_key]:
                if tuple_key in comparison_dict[file_key]:
                    comparison_dict[file_key][tuple_key] -= sol_dict[file_key][tuple_key]
                else:
                    comparison_dict[file_key][tuple_key] = -sol_dict[file_key][tuple_key]
        # get remaining wrongs
        errors = 0
        for key in comparison_dict:
            for num in comparison_dict[key].values():
                errors += np.abs(num)
        print(errors)



    @staticmethod
    def make_ind_col_dict(sol_dh_dict):
        out_dict = dict()
        for key in sol_dh_dict:
            out_dict[key] = dict()
            for ds in sol_dh_dict[key]:
                finger_p = tuple(ds.df_data.columns) + tuple(ds.df_data.index)
                if finger_p in out_dict[key]:
                    out_dict[key][finger_p] += 1
                else:
                    out_dict[key][finger_p] = 1
        return out_dict

    @staticmethod
    def make_sol_dict():
        """
        Run present pipeline and save the merge results
        :return:
        """
        file_names = ["FORMAT3_Copy of KommuneMTPLforTriangle.xls",
            "C Triangulations analysis R2017 GC20161109.xls",
            "EVOLUTION 2017 _ M+F - Triangles cat nat brut net.xls",
            "Bsp8 _ Dreiecke aus GCNA für CU1.4.1.xls",
            "Analysis MTPL MOD.xls",
            "Bsp6 _ Dreiecke aus GCNA für CU1.4.1.xls",
            "FORMAT6_sinistres.xls",
            "FORMAT1_LOSSES-MTPL-OVER-500-GROUP-2005_modified.xls"]
        solutions_dict = dict()
        raw_dict = dict()
        for file_name in file_names:
            sr_list, file_name = ExcelLoader.load_excel(pdir.RESOURCES_DIR + "/raw_test_files/" + file_name)
            dh = DataHolder()
            for sr in sr_list:
                dh.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                             pd.DataFrame(columns=sr.headers, data=sr.xls_types), orig_sheet_name=sr.sheet_name)

            dh = SheetPreProcessor.separate_components(dh)
            raw_dict[file_name] = dh.encode()
            dh = HorizontalMerger.horizontal_merge(dh)
            #temp_path = pdir.RESOURCES_DIR + "/temp/"
            #dh.write_excel(temp_path + file_name)
            solutions_dict[file_name] = dh
        solutions_dict = MergePararametersOptimizer.make_ind_col_dict(solutions_dict)
        with open(pdir.RESOURCES_DIR + "/test/merge_solutions.obj", "wb") as temp_file:
            pickle.dump(solutions_dict, temp_file)
        with open(pdir.RESOURCES_DIR + "/test/raw_test.obj", "wb") as temp_file:
            pickle.dump(raw_dict, temp_file)


if __name__ == '__main__':
    MergePararametersOptimizer.make_sol_dict()
    with open(pdir.RESOURCES_DIR + "/test/raw_test.obj", "rb") as temp_file:
        raw_dh = pickle.load(temp_file)
    raw_dh = {key: DataHolder.decode(raw_dh[key]) for key in raw_dh}

    with open(pdir.RESOURCES_DIR + "/test/merge_solutions.obj", "rb") as temp_file:
        solution_dh = pickle.load(temp_file)
    solution_dh = {key: solution_dh[key] for key in solution_dh}
    start = time.time()
    MergePararametersOptimizer.evaluate(raw_dh, solution_dh)
    end = time.time()
    print(end - start)