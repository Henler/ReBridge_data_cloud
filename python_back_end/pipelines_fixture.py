from unittest import TestCase
import unittest
from python_back_end.data_cleaning.cleaning_pipeline import CleaningPipeline
from python_back_end.triangle_formatting.triangle_pipeline import TrianglePipeline
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.utilities.call_encapsulators import *
from python_back_end.utilities.sheet_io import ExcelLoader
from python_back_end.utilities.help_functions import safe_round
import numpy as np
import os
import pandas as pd
import xlrd
import xlwt
from xlutils.copy import copy
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
import warnings
import traceback
import sys


def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    """
    Promts all warnings to throw errors.
    :param message:
    :param category:
    :param filename:
    :param lineno:
    :param file:
    :param line:
    :return:
    """

    log = file if hasattr(file, 'write') else sys.stderr
    traceback.print_stack(file=log)
    log.write(warnings.formatwarning(message, category, filename, lineno, line))


warnings.showwarning = warn_with_traceback


class ToDiscComparer:

    @staticmethod
    def true_with_delayed_error(bool, file_name, test_obj):
        """
        Enables testing through a list of fixtures without stopping at the first error
        :param bool:
        :param file_name:
        :param test_obj:
        :return:

        """
        try:
            test_obj.assertTrue(bool)
            return True
        except AssertionError as e:
            error_message = file_name + " " + str(e)
            print(error_message)
            test_obj.verificationErrors.append(error_message)
            return False

    @staticmethod
    def compare_to_disc(test_obj, file_name, dh):
        """
        Compares the test obj to a stored file.
        :param test_obj:
        :param file_name:
        :param dh:
        :return:
        """
        temp_path = pdir.RESOURCES_DIR + "/temp/"
        dh.merge_in_original_sheets(save_sheet_names=True).write_excel(temp_path + file_name)
        #check if the target exists
        if not os.path.isfile(pdir.RESOURCES_DIR + "/test/" + file_name):
            print("The file " + pdir.RESOURCES_DIR + "/test/" + file_name + " does not exist")
            test_obj.assertTrue(False)
        else:

            # Now test for equality
            truth_sr_list, dummy = ExcelLoader.load_excel(pdir.RESOURCES_DIR + "/test/" + file_name)
            temp_sr_list, dummy = ExcelLoader.load_excel(pdir.RESOURCES_DIR + "/temp/" + file_name)
            if not ToDiscComparer.true_with_delayed_error(temp_sr_list, file_name, test_obj):
                return
            if not ToDiscComparer.true_with_delayed_error(truth_sr_list, file_name, test_obj):
                return
            if not ToDiscComparer.true_with_delayed_error(len(truth_sr_list) == len(temp_sr_list), file_name, test_obj):
                return

            # make all comparisons and test afterwards
            boolean_dict = dict()
            for truth_sr, temp_sr in zip(truth_sr_list, temp_sr_list):
                # compare values, first round what we can
                test_obj.assertEqual(truth_sr.sheet_name, temp_sr.sheet_name)
                #print(temp_sr.sheet_name)
                truth_array = safe_round(np.array(truth_sr.row_vals))
                temp_array = safe_round(np.array(temp_sr.row_vals))
                try: test_obj.assertEqual(temp_array.shape, truth_array.shape)
                except AssertionError as e:
                    error_message = file_name + " " + str(e)
                    print(error_message)
                    test_obj.verificationErrors.append(error_message)
                    return
                boolean_dict[temp_sr.sheet_name] = truth_array == temp_array
            error_style = xlwt.easyxf('pattern: pattern solid, fore_colour red; font: colour white, bold True;')
            # Now test
            book = xlrd.open_workbook(pdir.RESOURCES_DIR + "/temp/" + file_name)
            names = book.sheet_names()
            cp = copy(book)
            already_printed = False
            for key in boolean_dict:
                if not boolean_dict[key].all():

                    if not already_printed:
                        print(file_name)
                        already_printed = True
                    sheet = cp.get_sheet(names.index(key))
                    #get indices of falses
                    indices = np.transpose((boolean_dict[key] == False).nonzero())
                    for index in indices:
                        orig_val = book.sheet_by_index(names.index(key)).cell(index[0], index[1]).value
                        sheet.write(index[0], index[1], orig_val, style=error_style)
            cp.save(pdir.RESOURCES_DIR + "/temp/" + file_name)
            for key in boolean_dict:
                try: test_obj.assertTrue(boolean_dict[key].all())
                except AssertionError as e:
                    error_message = file_name + " " + str(e)
                    print(error_message)
                    test_obj.verificationErrors.append(error_message)
    @staticmethod
    def run_test_per_file_name(in_obj, in_tup, form):
        """
        Performs a fixture test for one file. The encapsulators determine the scope of the test.
        :param in_obj:
        :param in_tup:
        :param form:
        :return:
        """
        if not pp.LOG_SVM_FEATURES:
            print(in_tup)
        sr_list, file_name = ExcelLoader.load_excel(pdir.RESOURCES_DIR + "/raw_test_files/" + in_tup[0])
        dh = DataHolder(file_name.split(".")[0])
        for sr in sr_list:
            dh.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                         pd.DataFrame(columns=sr.headers, data=sr.xls_types), orig_sheet_name=sr.sheet_name)
        #Choose encapsulator class to determine test scope
        #dhce = DataHolderCallTestEncapsulator(pdir.RESOURCES_DIR + '/temp/pickles/', pdir.RESOURCES_DIR + '/test/pickles/')
        #dhce = DataHolderCallSaveEncapsulator(pdir.RESOURCES_DIR + '/test/pickles/')
        #dhce = DataHolderCallOutputEncapsulator(pdir.RESOURCES_DIR + '/left_triangles/' + in_tup[0], in_tup[1])
        dhce = DataHolderCallEncapsulator()
        #dhce = DataHolderCallTimeEncapsulator()
        if form == "triangle_table":
            dummy, dh = TrianglePipeline.table_triangle_pipeline_dh(dh, dhce)
        elif form == "triangle":
            dummy, dh = TrianglePipeline.triangle_pipeline_dh(dh, dhce, tri_type=in_tup[1]["tri_type"], n_outputs=in_tup[1]["n_outputs"])
        elif form == "cleaning":
            dummy, dh = CleaningPipeline.clean_data_dh(dh)
        ToDiscComparer.compare_to_disc(in_obj, file_name, dh)


class PipelineTest(TestCase):

    def setUp(self):
        self.verificationErrors = []

    def testTrianglePipeline(self):
        """
        Provides a list of fixtures to test
        :return:
        """
        inputs = [
            #Add xls or xlsx example files here
            ]


        for in_tup in inputs:
            ToDiscComparer.run_test_per_file_name(self, in_tup, "triangle")

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)




if __name__ == '__main__':
    unittest.main()