from unittest import TestCase
import unittest
from python_back_end.triangle_formatting.triangle_templater import TriangleTemplater
from python_back_end.triangle_formatting.sub_triangler import SubTriangler
from python_back_end.triangle_formatting.triangle_stripper import TriangleStripper
from python_back_end.triangle_formatting.triangle_utils import *
from python_back_end.triangle_formatting.triangle_rendering import *
from python_back_end.triangle_formatting.header_finder import *
from python_back_end.triangle_formatting.hole_filler import DateFiller
from python_back_end.data_cleaning.cleaning_utils import *
from python_back_end.triangle_formatting.hole_filler import StringFiller
from python_back_end.triangle_table_formatting.col_type_identifier import ColTypeIdentifier
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter
import warnings
import traceback
import sys
from python_back_end.utilities.help_functions import mad, sum_unique, equals_recursively
from python_back_end.utilities.state_handling import DataHolder, SheetStateComparer, DataStruct
from pandas.util.testing import assert_frame_equal
import numpy as np
import pandas as pd
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.utilities.sheet_io import ExcelLoader, SheetWriter
from python_back_end.logConfig import LOGGING
import logging.config
import copy


logging.config.dictConfig(LOGGING)


def warn_with_traceback(message, category, filename, lineno, file=None, line=None):

    log = file if hasattr(file, 'write') else sys.stderr
    traceback.print_stack(file=log)
    log.write(warnings.formatwarning(message, category, filename, lineno, line))


warnings.showwarning = warn_with_traceback


class DateColIdentifierTest(TestCase):

    def test_regex(self):
        dci = DateColIdentifier()
        array = pd.Series(["brum", "b200c", "b 2001", "1999", "-2010v", "2031kkk", "Feb", "gfeb", "2023", "12023", "f2023", "20234"])
        out = dci.date_form(array)
        self.assertTrue(all(out==np.array([2, 0, 1, 1, 1, 0, 1, 2, 1, 0, 1, 1])))

    def test_identify_month_cols(self):
        data = pd.DataFrame([[0, 12, 48, 24, 24, 36, 25, 72, 0, 36, 36],
                             [0, 1, 3, 5, 4, 4, 12, 12, 19, 23, np.nan],
                             ["", "", "", "", "", "", "", "", "", "", ""]])
        profiles = pd.DataFrame([[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                             [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                             [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])
        mat = profiles.T.copy()
        mat.loc[:, :] = 0
        ds = DataStruct(data.T, profiles.T, 'test')
        m_cols = DateColIdentifier.identify_month_cols(ds, mat)
        truth = pd.Series([True, False, False])
        self.assertTrue(m_cols.equals(truth))





class StringFillerTest(TestCase):

    def test_fill_hollow_str_cols(self):
        dh = DataHolder("test")
        df_data = pd.DataFrame(data={'col1': [1, "", "", "j", "", "", "6", "", "b",
                                              "g", "", "", "j", "", "", "6", "", "b", "", ""],
                                     '1992': ["", "", "", "j", "", "", "6", "", "b",
                                              "g", "", "", "j", "", "", "6", "", "b", "g", "hrumpff"]})

        df_profiles = pd.DataFrame(data={'col1': [2, 0, 0, 1, 0, 0, 1, 0, 1,
                                                  1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],

                                         '1992': [0, 0, 0, 1, 0, 0, 1, 0, 1,
                                                  1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1]})
        dh.add_sheet("test", df_data, df_profiles)
        StringFiller.fill_hollow_str_cols(dh)
        dh_sol = DataHolder("test")
        df_data_sol = pd.DataFrame(data={'col1': [1, 1, 1, "j", "j", "j", "6", "6", "b",
                                              "g", "g", "g", "j", "j", "j", "6", "6", "b", "b", "b"],
                                     '1992': ["", "", "", "j", "j", "j", "6", "6", "b",
                                              "g", "g", "g", "j", "j", "j", "6", "6", "b", "g", "hrumpff"]})

        df_profiles_sol = pd.DataFrame(data={'col1': [2, 2, 2, 1, 1, 1, 1, 1, 1,
                                                  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],

                                         '1992': [0, 0, 0, 1, 1, 1, 1, 1, 1,
                                                  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]})

        dh_sol.add_sheet("test", df_data_sol, df_profiles_sol)
        self.assertTrue(dh.equals(dh_sol))




class SubTrianglerTest(TestCase):

    def setUp(self):
        self.names = ["first", "second"]
        self.dh = DataHolder("test")
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["3", "4"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
        self.dh.add_sheet(self.names[0], d1, d2)
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["1", "1"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [1, 1]})
        self.dh.add_sheet(self.names[0], d1, d2)
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["15", "16"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [15, 16]})
        self.dh.add_sheet(self.names[1], d1, d2)


    def test_component_finder(self):
        # make a list of similar and dissimilar strings
        strings = ["asdfgh", "sdfgh", "qwert", "asdgh", "qwerty", "asdfgh"]
        match_dict = SubTriangler.component_finder(strings)
        test_set1 = set(["asdfgh", "sdfgh", "asdgh", "asdfgh"])
        test_set2 = set(["qwert", "qwerty"])
        self.assertEqual(test_set1, set(match_dict["sdfgh"]))
        self.assertEqual(test_set2, set(match_dict["qwert"]))



class DataHolderTest(TestCase):

    def setUp(self):
        self.names = ["first", "second"]
        self.dh = DataHolder("test")
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["3", "4"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
        self.dh.add_sheet(self.names[0], d1, d2, orig_sheet_name="1")
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["1", "1"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [1, 1]})
        self.dh.add_sheet(self.names[0], d1, d2, orig_sheet_name="2")
        d1 = pd.DataFrame(data={'col1': ["1", "2"], 'col2': ["15", "16"]})
        d2 = pd.DataFrame(data={'col1': [1, 2], 'col2': [15, 16]})
        self.dh.add_sheet(self.names[1], d1, d2, orig_sheet_name="2")

    def test_set_card_ids(self):
        trngs = []
        trngs.append({"group_id": "one"})
        trngs.append({"group_id": "two"})
        RowParser.set_card_ids(trngs, self.dh)
        # print(self.dh)
        true_ids = [0, 1, 1]
        for ds, ind in zip(self.dh.data_struct_list, true_ids):
            self.assertEqual(ds.card_id, ind)

    def test_updating(self):

        for dh_ind, df_data, df_profiles in self.dh.enumerate():
            if dh_ind == 0:
                df_data.loc[0, "col2"] = "5"
                df_profiles.loc[0, "col2"] = 5

            if dh_ind == 1:
                df_data.loc[0, "col1"] = "5"
                df_profiles.loc[0, "col1"] = 5

            if dh_ind == 2:
                df_data.loc[1, "col1"] = "19"
                df_profiles.loc[1, "col1"] = 19

            self.dh.update_with_ind(dh_ind, df_data, df_profiles)

        assert_frame_equal(self.dh.data_dict[self.names[0]][0].df_data, self.dh.data_struct_list[0].df_data)
        assert_frame_equal(self.dh.data_dict[self.names[0]][1].df_data, self.dh.data_struct_list[1].df_data)
        assert_frame_equal(self.dh.data_dict[self.names[1]][0].df_data, self.dh.data_struct_list[2].df_data)

        assert_frame_equal(self.dh.data_dict[self.names[0]][0].df_profiles, self.dh.data_struct_list[0].df_profiles)
        assert_frame_equal(self.dh.data_dict[self.names[0]][1].df_profiles, self.dh.data_struct_list[1].df_profiles)
        assert_frame_equal(self.dh.data_dict[self.names[1]][0].df_profiles, self.dh.data_struct_list[2].df_profiles)
        for key in self.dh.data_dict:
            for d_struct in self.dh.data_dict[key]:
                self.assertEqual(key, d_struct.name)

        for ds in self.dh.data_struct_list:
            self.assertEqual(ds, self.dh.id_dict[ds.id])


    def test_mementos(self):

        self.dh.create_memento()
        for dh_ind, df_data, df_profiles in self.dh.enumerate():
            if dh_ind == 0:
                df_data.loc[0, "col2"] = "5"
                df_profiles.loc[0, "col2"] = 5

            if dh_ind == 1:
                df_data.loc[0, "col1"] = "5"
                df_profiles.loc[0, "col1"] = 5

            if dh_ind == 2:
                df_data.loc[1, "col1"] = "19"
                df_profiles.loc[1, "col1"] = 19

            self.dh.update_with_ind(dh_ind, df_data, df_profiles)

        self.dh.create_memento()

        diff_dict_list = SheetStateComparer.compare_states(self.dh.mementos[0], self.dh.mementos[1])
        #for diff_dict in diff_dict_list:
            #pass#diff_
        for i in range(2):
            for j in range(2):
                el = diff_dict_list[0]["diff_array"][i][j]
                if i == 0 and j == 1:
                    self.assertEqual(el.change, "Corrected")
                else:
                    self.assertEqual(el.change, "No change")

    def test_serialization(self):
        self.dh.data_struct_list[0].roles.append("Claims Paid")
        self.dh.data_struct_list[0].df_data.sort_values("col1", ascending=False, inplace=True)
        serialized = self.dh.encode()
        data_framed = DataHolder.decode(serialized)

        assert_frame_equal(self.dh.data_struct_list[0].df_data, data_framed.data_struct_list[0].df_data)
        assert_frame_equal(self.dh.data_struct_list[1].df_data, data_framed.data_struct_list[1].df_data)
        assert_frame_equal(self.dh.data_struct_list[2].df_data, data_framed.data_struct_list[2].df_data)

        assert_frame_equal(self.dh.data_struct_list[0].df_profiles, data_framed.data_struct_list[0].df_profiles)
        assert_frame_equal(self.dh.data_struct_list[1].df_profiles, data_framed.data_struct_list[1].df_profiles)
        assert_frame_equal(self.dh.data_struct_list[2].df_profiles, data_framed.data_struct_list[2].df_profiles)
        self.assertEqual(data_framed.data_struct_list[0].roles[0], "Claims Paid")
        # Test conservation of ids
        for ind in range(len(self.dh.data_struct_list)):
            self.assertEqual(data_framed.data_struct_list[ind].id, self.dh.data_struct_list[ind].id)


class InputMatcherTest(TestCase):

    def setUp(self):
        # self.trngs = [{'headers': ["Year", "unit"],
        #                               'categories': [
        #                                   {'name': 'Claim - Incurred',
        #                                    'type': 'sum',
        #                                    'from': [ps.CAT_PAID_NAME, ps.CAT_RESERVED_NAME]},
        #                                   {'name': ps.CAT_PAID_NAME,
        #                                    'type': 'independent',
        #                                    'from': []},
        #                                   {'name': ps.CAT_RESERVED_NAME,
        #                                    'type': 'independent',
        #                                    'from': []}
        #                               ],
        #                 "group_id": 0,
        #                "type": "aggregate"
        #                               },
        #                             {'headers': ["Year", "unit"],
        #                              'categories': [
        #                                  {'name': ps.CAT_PREMIUM_NAME,
        #                                   'type': 'independent',
        #                                   'from': []}],
        #                              "group_id": 0,
        #                              "type": "aggregate"
        #                              }]
        #info_dict = {'tri_type': 'aggregate', 'n_outputs': 1}
        #print(info_dict)
        #user_defined_triangles = OutputTriangleParser.generate_output_triangles(info_dict)

        self.names = ["Premium_", "Premium", "Total Outstanding 2004", "Paid", "Total Incurred"]
        self.dh = DataHolder("test")
        self.dh.add_sheet(self.names[0], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[1], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[2], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[3], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[4], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))

    # def testFitForOutput(self):
    #     dh = DataHolder("test")
    #     data = pd.DataFrame(data={'001. col2': [0, 0], '002. 1991': [0, 0]})
    #     prof = pd.DataFrame(data={'001. col2': [9, 9], '002. 1991': [9, 9]})
    #     dh.add_sheet("test", data, prof)
    #     data = pd.DataFrame(data={'001. col2': ["", 0], '002. 1991': [0, 0]})
    #     prof = pd.DataFrame(data={'001. col2': [9, 9], '002. 1991': [9, 9]})
    #     dh.add_sheet("test", data, prof)
    #     data = pd.DataFrame(data={'001. col3': [0, 0], '002. 1991': [0, 0]})
    #     prof = pd.DataFrame(data={'001. col3': [9, 9], '002. 1991': [9, 9]})
    #     dh.add_sheet("test", data, prof)
    #     data = pd.DataFrame(data={'001. col2': [0, 0], '002. 1991': [0, 0]})
    #     prof = pd.DataFrame(data={'001. col2': [9, 9], '002. 1991': [9, 9]})
    #     dh.add_sheet("test", data, prof)
    #     card_ids = [0, 0, 0, 1]
    #     for ds, id in zip(dh, card_ids):
    #         ds.card_id = id
    #     InputMatcher.set_fit_for_output(dh)
    #     solution = [True, False, False, True]
    #     for ds, sol in zip(dh, solution):
    #         self.assertEqual(ds.fit_for_output, sol)

    def testDistrMatching(self):
        test_distr = np.array([1,1,1,1,1,2,2,2,2,3,3,3,4,4,5])
        test_distr = test_distr/mad(test_distr)
        test_distr = test_distr - np.mean(test_distr)
        distr = {
            ps.CAT_RESERVED_NAME: test_distr
        }
        dh = DataHolder("test")
        dh.add_sheet(self.names[0], pd.DataFrame(data=[1, 1, 1, 1, 2, 2, 2, 3, 3, 4]), pd.DataFrame(data=[SheetTypeDefinitions.TRIANGLE_ELEMENT]*10))
        dh.add_sheet(self.names[0], pd.DataFrame(data=[5, 9, 3, 7, 18]), pd.DataFrame(data=[SheetTypeDefinitions.TRIANGLE_ELEMENT]*5))
        matches = list()
        for id in dh.id_dict:
            matches.append(InputMatcher.compare_with_distribution(id, ps.CAT_RESERVED_NAME, dh, distr))
        # First entry is more similar to the reference, therefore, first match should be better
        self.assertTrue(matches[0] > matches[1])

    def test_headers_are_padded(self):
        n_padded = 11
        headers = [str(num + 1).zfill(pp.N_DIGITS_HEADER_PADDING) + ". " + ps.HEADER_PLACE_HOLDER for num in range(n_padded)]
        headers.append("date001.2")
        bools = InputMatcher.headers_are_padded(headers)
        truth = [True for i in range(n_padded)]
        truth.append(False)
        self.assertTrue(np.all(np.array(truth) == np.array(bools)))


class TriangleStripperTest(TestCase):


    # def testEvaluateColHeaders(self):
    #     data = pd.DataFrame(data={'001. col1': ["", "", 0], '002. col2': [0, 0, 0], '003. 1991': [0, 0, 0], '004. 1992': [1, 0, 0]})
    #     prof = pd.DataFrame(data={'001. col1': [1, 1, 6], '002. col2': [6, 6, 6], '003. 1991': [6, 6, 6], '004. 1992': [2, 6, 6]})
    #     cols = TriangleStripper.evaulate_col_headers(DataStruct(data, prof, "test"), test_min_cols=True)
    #     cols = cols[cols == 1].index
    #     self.assertTrue(cols[0] == '003. 1991')
    #     self.assertTrue(cols[1] == '004. 1992')

    # def testIdentifyTriangleHeaders(self):
    #     dh = DataHolder("test")
    #     data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [0, 0, 0], '1991': [0, 0, 0], '1992': [1, 0, 0]})
    #     prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992': [2, 6, 6]})
    #     dh.add_sheet("test", data, prof)
    #     data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [0, 0, 0], '1991': [0, 0, 0], '1992': [1, 0, 0]})
    #     prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992': [2, 6, 6]})
    #     dh.add_sheet("test", data, prof)
    #     data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [0, 0, 0], '1991': [0, 0, 0], '1992-': [1, 0, 0]})
    #     prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992-': [2, 6, 6]})
    #     dh.add_sheet("test", data, prof)
    #     tr_col_dict = TriangleStripper.identify_triangle_cols(dh, test_min_cols=True)
    #     self.assertEqual(list(tr_col_dict.values())[0].values.tolist(),[False, False, True, True])
    #     self.assertEqual(list(tr_col_dict.values())[1].values.tolist(), [False, False, True, True])

    def testIdentifyDateCols(self):
        data = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992'+ps.TRANSFORMED_DATE_COL_NAME: [1, 6, 6]})
        ds = DataStruct(data, data, "test")
        cols = DateColIdentifier.identify_marked_date_cols(ds)
        cols = cols[cols].index
        self.assertTrue(cols[0] == '1992'+ps.TRANSFORMED_DATE_COL_NAME)

        data = pd.DataFrame(data={'col1': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6],
                                  'col2': ["1994 Brum", "Hä", 2015, "1994 Brum", "mjua", 2015, "1994 Brum", "1999", 2015],
                                  '1991': [6, 6, 6, 6, 6, 6, 6, 6, 6]})
        ds = DataStruct(data, data, "test")
        cols = DateColIdentifier.identify_marked_date_cols(ds)
        cols = cols[cols].index
        self.assertTrue(cols[0] == 'col2')

    def testRightAdjust(self):
        data = pd.DataFrame(data={'col1': ["one", "two", "three"], 'col2': [1, 1, 1], 'col3': [1, 0, 0], 'col4': [1, 0, 0]})
        profiles = pd.DataFrame(data={'col1': [1, 1, 1], 'col2': [9, 9, 9], 'col3': [9, 9, 9], 'col4': [9, 9, 9]})
        ds = DataStruct(data, profiles, "test")
        tr_cols = pd.Series([False, True, True, True], index=["col1", "col2", "col3", "col4"])
        TriangleStripper.right_adjust(ds, tr_cols)
        data_solution = pd.DataFrame(data={'col1': ["one", "two", "three"], 'col2': [1, 0, 0], 'col3': [1, 1, 0], 'col4': [1, 0, 1]})

        self.assertTrue(ds.df_data.equals(data_solution))

    def testTurnTriangle(self):
        dh = DataHolder("test")
        data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [0, 0, 2], '1991': [0, 0, 0], '1992': [1, 0, 0]})
        prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992': [2, 6, 6]})
        dh.add_sheet("test", data, prof)
        data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [1, 1, 0], '1991': [0, 0, 0], '1992': [1, 0, 0]})
        prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992': [2, 6, 6]})
        dh.add_sheet("test", data, prof)
        data = pd.DataFrame(data={'col1': ["", "", 0], 'col2': [3, 1, 0], '1991': [0, 0, 0], '1992-': [1, 0, 0]})
        prof = pd.DataFrame(data={'col1': [1, 1, 6], 'col2': [6, 6, 6], '1991': [6, 6, 6], '1992-': [2, 6, 6]})
        dh.add_sheet("test", data, prof)
        tr_cols_dict = {tuple(dh.data_struct_list[0].df_data.columns) + dh.data_struct_list[0].df_data.shape:
                pd.Series([False, True, True, True], index=dh.data_struct_list[0].df_data.columns),
                        tuple(dh.data_struct_list[2].df_data.columns) + dh.data_struct_list[0].df_data.shape:
                            pd.Series([False, True, True, True], index=dh.data_struct_list[2].df_data.columns)
        }
        dh_copy = dh.copy_without_memory()
        TriangleStripper.turn_triangle(dh, tr_cols_dict, alt_min_score=0.6)

        for ds in dh_copy.data_struct_list:
            tr_cols = tr_cols_dict[tuple(ds.df_data.columns) + ds.df_data.shape]
            tri_part = ds.df_data[tr_cols.index[tr_cols]].values
            ds.df_data[tr_cols.index[tr_cols]] = np.transpose(tri_part)

        for ds, ds_copy in zip(dh.data_struct_list, dh_copy.data_struct_list):
            self.assertTrue(ds.df_data.equals(ds_copy.df_data))
            self.assertTrue(ds.df_profiles.equals(ds_copy.df_profiles))




class FindHeadersTest(TestCase):

    def testFindTriangleHeaders(self):
        names = ["First", "Second"]
        dh = DataHolder("test")
        d1 = pd.DataFrame(data={'col1' + ps.HEADER_PLACE_HOLDER: ["1", "2", 1],
                                'col2' + ps.HEADER_PLACE_HOLDER: [3, "2", "3b"],
                                'col3' + ps.HEADER_PLACE_HOLDER: ["brum2", "4", 4],
                                'col4' + ps.HEADER_PLACE_HOLDER: [24, "4", "brum25"],
                                })
        d2 = d1.copy()
        d2.iloc[:, :]=1

        dh.add_sheet(names[0], d1, d2)
        dh = TriangleHeaderFinder.find_triangle_headers(dh, test_settings=True)
        headers = list(dh.data_struct_list[0].df_data.columns)
        self.assertEqual(headers, ["col11", "col23", "col3brum2", "col424"])


class NumColExtracterTest(TestCase):

    def testExtractNumCols(self):
        df_data = pd.DataFrame(data={'col1': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6],
                                  'col2': [1994, 43, 2015, 1994, 7, 2015, 1994, 1999, 2015],
                                  '1991': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6],
                                  '1992': ["g", "r", "h", "j", "t", "f", "6", "p", "6"],
                                  '1993': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6]})

        df_profiles = pd.DataFrame(data={'col1': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                  'col2': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                  '1991': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                  '1992': [1, 1, 1, 1, 1, 1, 1, 1, 1],
                                  '1993': [2, 2, 2, 2, 2, 2, 2, 2, 2]})

        num_cols = TypeColExtracter.extract_num_cols(df_data, df_profiles)
        headers = list(num_cols.columns)
        self.assertEqual(headers, ['col1', 'col2', '1991', '1993'])



class TriangleHeaderFinderTest(TestCase):

    def testRemoveStrayRows(self):
        df_data = pd.DataFrame(data={'col1': ["1", "", "1991", "1992", "2007", "rew", "1993", "1994", "1995x"],
                                     'col2': [43, 1994, 2015, 1994, 7, 2015, 1994, 1999, 2015],
                                     '1991': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6],
                                     '1992': ["g", "r", "h", "j", "t", "f", "6", "p", "6"],
                                     '1993': ["1", "1993", "6", "1993", "", "rew", "1993", "1994", ""]})

        df_profiles = pd.DataFrame(data={'col1': [1, 1, 1, 1, 1, 1, 1, 1, 1],
                                         'col2': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         '1991': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         '1992': [1, 1, 1, 1, 1, 1, 1, 1, 1],
                                         '1993': [1, 1, 1, 1, 1, 1, 1, 1, 1]})
        ds = DataStruct(df_data, df_profiles, 'test')

        TriangleHeaderFinder.remove_stray_rows(ds,0)
        solution = pd.DataFrame(data={'col1': ["", "1991", "1992", "2007", "rew", "1993", "1994", "1995x"],
                                     'col2': [1994, 2015, 1994, 7, 2015, 1994, 1999, 2015],
                                     '1991': [1, 6, 1993, 1, 6, 1993, 1, 6],
                                     '1992': ["r", "h", "j", "t", "f", "6", "p", "6"],
                                     '1993': ["1993", "6", "1993", "", "rew", "1993", "1994", ""]},
                                index=[1, 2, 3, 4, 5, 6, 7, 8])
        self.assertTrue(ds.df_data.equals(solution))


class RowParserTest(TestCase):

    def test_select_date_col(self):
        df_data = pd.DataFrame(
            {"string_dates": ["1995", 2007, "1998", 513, "2013"],
             "string_dates_empty": ["", "", "", "", ""],
             "xls_date": ["1995-06-03", "2007-06-03", "1999-06-03", "2001-06-03", "2015-06-03"],
             "bs": ["b", "s", "i", "s", "n"]
        }
        )
        str_d = SheetTypeDefinitions.STRING_DATE
        xl_d = SheetTypeDefinitions.XL_DATE
        string_t = SheetTypeDefinitions.STRING
        df_profiles = pd.DataFrame(
            {"string_dates": [str_d, str_d, str_d, str_d, str_d],
             "string_dates_empty": [str_d, str_d, str_d, str_d, str_d],
             "xls_date": [xl_d, xl_d, xl_d, xl_d, xl_d],
             "bs": [string_t, string_t, string_t, string_t, string_t]
             }
        )
        connected_ds = DataStruct(df_data, df_profiles, "test")
        cols = connected_ds.df_profiles.iloc[0, :]
        date_header = RowParser.select_date_col(cols, connected_ds)
        self.assertEqual(date_header, 'string_dates')



class ColTypeIdentifierTest(TestCase):

    def test_col_identification(self):
        df_data = pd.DataFrame(data={'col1': ["1", "", "1991", "1992", "2007", "rew", "1993", "1994", "1995x"],
                                     'col2': [43, 1994, 2015, 1994, 7, 2015, 1994, 1999, 2015],
                                     '1991': [1993, 1, 6, 1993, 1, 6, 1993, 1, 6],
                                     '1992': ["g", "r", "h", "j", "t", "f", "6", "p", "6"],
                                     '1993': ["1", "1993", "6", "1993", "", "rew", "1993", "1994", ""]})

        df_profiles = pd.DataFrame(data={'col1': [1, 1, 1, 1, 1, 1, 1, 1, 1],
                                         'col2': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         '1991': [2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         '1992': [1, 1, 1, 1, 1, 1, 1, 1, 1],
                                         '1993': [1, 1, 1, 1, 1, 1, 1, 1, 1]})
        dh = DataHolder('test')
        dh.add_sheet('test', df_data, df_profiles)
        dh = DateFiller.identify_and_gen_date_cols(dh, replace_col=False)
        dh = ColTypeIdentifier.identify_col_types(dh)
        profiles = dh.data_struct_list[0].df_profiles
        self.assertTrue(profiles.iloc[1,1], SheetTypeDefinitions.STRING_DATE)
        self.assertTrue(profiles.iloc[0, 2], SheetTypeDefinitions.TRIANGLE_ELEMENT)
        self.assertTrue(profiles.iloc[0, 3], SheetTypeDefinitions.ID_ELEMENT)

class HelpFunctionTester(TestCase):

    def test_sum_unique(self):
        headers = ['scrooge', "alan", "alan", "scrooge", "alan"]
        vals = np.array([17, 1, 2, 3, 5])
        res_headers = np.array(["alan", "scrooge"])
        res_vals = np.array([8, 20])
        unique, summed = sum_unique(headers, vals)
        self.assertTrue(np.all(unique == res_headers))
        self.assertTrue(np.all(res_vals == summed))



if __name__ == '__main__':
    unittest.main()