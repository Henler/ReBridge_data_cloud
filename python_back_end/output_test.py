from unittest import TestCase
import unittest
import os
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
import pickle
from python_back_end.triangle_formatting.triangle_rendering import RowParser
from python_back_end.triangle_formatting.triangle_utils import InputMatcher
from python_back_end.triangle_formatting.triangle_templater import TriangleTemplater
from python_back_end.utilities.sheet_io import SheetWriter


class OutputTester(TestCase):

    def test_output(self):
        path = pdir.RESOURCES_DIR + "left_triangles/outtake/"
        #path = pdir.RESOURCES_DIR + "left_triangles/"
        for file in os.listdir(path):
            if file.endswith(".pickle"):
                print(file)
                with open(path + file, 'rb') as f:
                    read_data = pickle.load(f)
                dh = DataHolder.decode(read_data["DataHolder"])
                info_dict = read_data["extra_content"]
                print(info_dict)
                user_defined_triangles = OutputTriangleParser.generate_output_triangles(info_dict)
                data_holder, group_ids, sheet_names = RowParser.set_card_ids(user_defined_triangles, dh)
                user_defined_triangles = InputMatcher.match_triangles_to_output(user_defined_triangles, data_holder)
                user_defined_triangles = RowParser.parse_output_from_triangle_forms(user_defined_triangles,
                                                                                    data_holder)
                head, sep, tail = file.partition(".xls")
                SheetWriter.trngs_to_excel(user_defined_triangles, head + sep)


class OutputTriangleParser:

    @staticmethod
    def generate_output_triangles(info_dict):
        if info_dict["tri_type"] == "single":
            user_defined_triangles = TriangleTemplater.get_single_loss_triangle_template()
        elif info_dict["tri_type"] == "aggregate":
            format_dict = {"Claims": 1, "Premiums": 1}
            user_defined_triangles = TriangleTemplater.get_aggregate_loss_triangle_template(format_dict)
        else:
            raise Exception("key error in info dict")

        return TriangleTemplater.create_triangle_template_with_group_ids(user_defined_triangles, info_dict['n_outputs'])


if __name__ == '__main__':
    unittest.main()