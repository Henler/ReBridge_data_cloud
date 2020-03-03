from django.test import TestCase

from mysite.triangle_formatting.rendering import RowParser
from .models import DataSheet
from python_back_end.data_cleaning.cleaning_utils import TagMatcher
from python_back_end.triangle_formatting.triangle_utils import *
from .services.sheet_manager import SheetManager
from python_back_end.utilities.sheet_io import SheetReader
from python_back_end.utilities.state_handling import DataHolder
import pandas as pd
from python_back_end.program_settings import PROGRAM_STRINGS as ps


class TagMatchTest(TestCase):

    def setUp(self) -> None:
        self.filename = "./table_cleaning/resources/test_headers.xlsx"
        self.sheet_name = "many_headers"
        self.ds = DataSheet(sheet_name="test_sheet")
        self.ds.save()
        sr = SheetReader()
        sr.read_sheet_from_name([self.filename], self.sheet_name)
        self.ds.read_entries(sr.headers, sr.row_vals, sr.xls_types)

    def testMatching(self):
        sm = SheetManager(self.ds)
        headers = sm.get_sheet_headers()
        #print(headers)
        tm = TagMatcher()
        tags = tm.match_headers(headers)


class InputMatcherTest(TestCase):

    def setUp(self):
        self.trngs = [{'headers': ["Year", "unit"],
                                      'categories': [
                                          {'name': 'Claim - Incurred',
                                           'type': 'sum',
                                           'from': [ps.CAT_PAID_NAME, ps.CAT_RESERVED_NAME]},
                                          {'name': ps.CAT_PAID_NAME,
                                           'type': 'independent',
                                           'from': []},
                                          {'name': ps.CAT_RESERVED_NAME,
                                           'type': 'independent',
                                           'from': []}
                                      ],
                        "group_id": 0,
                       "type": "single loss"
                                      },
                                    {'headers': ["Year", "unit"],
                                     'categories': [
                                         {'name': ps.CAT_PREMIUM_NAME,
                                          'type': 'independent',
                                          'from': []}],
                                     "group_id": 0,
                                     "type": "single loss"
                                     }]

        self.names = ["Premium_", "Premium", "Total Outstanding 2004", "Paid", "Total Incurred"]
        self.dh = DataHolder()
        self.dh.add_sheet(self.names[0], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[1], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[2], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[3], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))
        self.dh.add_sheet(self.names[4], pd.DataFrame(data=[0]), pd.DataFrame(data=[0]))

    def testTextualMatching(self):
        self.dh, dummy, dummy = RowParser.set_card_ids(self.trngs, self.dh)
        InputMatcher.match_triangles_to_output(self.trngs, self.dh)
        self.assertEqual(self.dh.id_dict[self.trngs[0]["connection"][ps.CAT_PAID_NAME]["data_struct_ids"][0]].name, self.names[3])
        self.assertEqual(self.dh.id_dict[self.trngs[0]["connection"][ps.CAT_RESERVED_NAME]["data_struct_ids"][0]].name, self.names[2])
        self.assertEqual(self.dh.id_dict[self.trngs[1]["connection"][ps.CAT_PREMIUM_NAME]["data_struct_ids"][0]].name, self.names[1])


