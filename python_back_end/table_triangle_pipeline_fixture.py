from unittest import TestCase
import unittest
from python_back_end.pipelines_fixture import ToDiscComparer


class TriangleTablePipelineTest(TestCase):

    def testTableTrianglePipeline(self):
        inputs = [
            #Add xls or xlsx example files here
                  ]

        for in_tup in inputs:
            ToDiscComparer.run_test_per_file_name(self, in_tup, "triangle_table")

if __name__ == '__main__':
    unittest.main()
