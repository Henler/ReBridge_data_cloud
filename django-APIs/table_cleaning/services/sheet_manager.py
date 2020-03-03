import logging
import xlwt
import numpy as np
from django.db import transaction
import pandas as pd
from ..models import KeyVal, Entry
from python_back_end.data_cleaning.cleaning_utils import ErrorFinder, TagMatcher
from python_back_end.utilities.sheet_io import SheetWriter


class SheetManager:

    def __init__(self, sheet):
        self.sheet = sheet
        # For now, the logs field is only used when sending managers to front end
        self.logs = []
        self.logger = logging.getLogger("data_cloud_logger")


    def get_sheet_array(self):
        array = list()
        for entry in self.sheet.entry_set.order_by("chrono"):
            array.append([kv.value for kv in entry.keyval_set.select_subclasses().order_by("key")])
        return array

    def get_sheet_col_array(self):
        array = list()
        headers = self.get_sheet_headers()

        for header in headers:
            array.append(np.array([kv.value for kv in self.sheet.keyval_set.select_subclasses().filter(key=header).order_by("chrono")]))
        return array

    def get_sheet_array_snippet(self):
        array = list()
        for entry in self.sheet.entry_set.order_by("chrono")[:3]:
            array.append([kv.value for kv in entry.keyval_set.select_subclasses().order_by("key")])
        return array

    def get_row_by_index(self, ind):
        array = [kv.value for kv in self.sheet.keyval_set.select_subclasses().filter(chrono=ind).order_by("key")]
        return array

    # def get_col_by_header(self, header):
    #     array = [kv.value for kv in self.sheet.keyval_set.select_subclasses().filter(key=header).order_by("chrono")]
    #     return array

    def get_sheet_headers(self):
        entry = self.sheet.entry_set.first()
        return [kv.key for kv in entry.keyval_set.select_subclasses().order_by("key")]

    def get_sheet_tags(self):
        entry = self.sheet.entry_set.first()
        tag_tuple = self.sheet.keyval_set.first().TAG_OPTIONS
        tag_dict = dict()
        for tup in tag_tuple:
            tag_dict[tup[0]] = tup[1]
        tag_array = [tag_dict[kv.tag] for kv in entry.keyval_set.order_by("key")]
        return tag_array

    def get_sheet_short_tags(self):
        entry = self.sheet.entry_set.first()
        tag_array = [kv.tag for kv in entry.keyval_set.order_by("key")]
        return tag_array

    def get_sheet_profiles(self):
        array = []
        for entry in self.sheet.entry_set.order_by("chrono"):
            array.append([kv.xls_type for kv in entry.keyval_set.order_by("key")])
        return array

    def get_sheet_chronos(self):
        chronos = [kv.chrono for kv in self.sheet.entry_set.order_by("chrono")]
        return chronos



    def remove_rows(self, rows):
        array = [self.get_row_by_index(ind) for ind in rows]
        with transaction.atomic():
            for row in rows:
                self.sheet.entry_set.get(chrono=row).delete()
        if rows:
            log_dict = {
                "log": "Removed rows: " + str(len(rows)),
                "detailed_log": array
            }
            self.logger.info(log_dict)

    def remove_cols(self, col_list):
        if not len(col_list) == 0:
            for head in col_list:
                kvs = self.sheet.keyval_set.filter(key=head).order_by("chrono")
                for kv in kvs:
                    kv.delete()

    def add_cols_from_dict(self, dict, tag="UN"):
        sep = ", "
        if not len(dict.keys()) == 0:

            entries = self.sheet.entry_set.order_by("chrono")
            for key in dict.keys():
                for ent, val in zip(entries, dict[key]):
                    ent.add_keyval(key, val, KeyVal.STRING_DATE)
            log_dict = {
                "log": "Added date cols: " + sep.join(dict.keys()),
                "detailed_log": list(dict.values())
            }
            self.logger.info(log_dict)

    def get_rowwise_patterns(self):
        sep = ", "
        ef = ErrorFinder()
        col_array = self.get_sheet_col_array()
        profiles = self.get_sheet_profiles()
        headers = np.array(self.get_sheet_headers())
        ret = ef.find_rowwise_additive_patterns(col_array, profiles)
        corrections = dict()
        if ret["periodic"]:
            if ret["errors_found"]:
                error_headers = sep.join(headers[ret["errors_found"]].tolist())
                loglist = list()
                loglist.append(ret["periodic_col"][0])
                for err, cor in zip(ret["error_cols"], ret["indicator_cols"]):
                    loglist.append(err.tolist())
                    loglist.append(cor.tolist())
                error_dict = {
                    "log": "Vertical summation errors were found and corrected in the cols: " + error_headers,
                    "detailed_log": loglist
                }
                self.logger.info(error_dict)
                for col_ind, col in zip(ret["errors_found"],ret["corrected_cols"]):
                    corrections[headers[col_ind]] = col.tolist()

        return corrections

    def get_colwise_patterns(self):
        sep = ", "
        ef = ErrorFinder()
        array = self.get_sheet_array()
        profiles = self.get_sheet_profiles()
        headers = self.get_sheet_headers()
        chronos = self.get_sheet_chronos()
        ret = ef.find_colwise_additive_patterns(array, profiles, chronos)
        corrections = dict()
        if ret["errors_found"]:
            error_dict = {
                "log": "Horizontal summation errors were found and corrected in the rows: ", #+ sep.join((np.array(ret["error_rows_found"])+1).tolist()),
                "detailed_log": ret["old_rows"]
            }
            self.logger.info(error_dict)
            for col_ind, col in zip(ret["errors_found"], ret["corrected_cols"]):
                corrections[headers[col_ind]] = col.tolist()
        return corrections

    def replace_cols(self, col_dict):
        if not len(col_dict.keys()) == 0:
            for key in col_dict.keys():
                kvs = self.sheet.keyval_set.select_subclasses().filter(key=key).order_by("chrono")
                for kv, val in zip(kvs, col_dict[key]):
                    kv.value = val
                    kv.save()

    def set_tags_from_headers(self):
        headers = self.get_sheet_headers()
        tm = TagMatcher()
        tags = tm.match_headers(headers)
        for header, tag in zip(headers, tags):
            keyvals = self.sheet.keyval_set.filter(key=header).order_by("chrono")
            with transaction.atomic():
                for keyval in keyvals:
                    keyval.tag = tag
                    keyval.save()


    def get_pandas_sheet(self):
        df = pd.DataFrame(data=self.get_sheet_array(), index=self.get_sheet_chronos(), columns=self.get_sheet_headers())
        return df

    def get_pandas_profiles(self):
        df = pd.DataFrame(data=self.get_sheet_profiles(), index=self.get_sheet_chronos(), columns=self.get_sheet_headers())
        return df

    @staticmethod
    def set_sql_to_memento(sm, mem):
        # delete everything!
        sm.sheet.entry_set.all().delete()
        row_vals = mem.df_data.values
        xls_types = mem.df_profiles.values
        chronos = mem.df_profiles.index.values
        headers = mem.df_profiles.columns.values
        with transaction.atomic():
            for row, type_row, chrono in zip(row_vals, xls_types, chronos):
                entry = Entry()
                entry.data_sheet_id = sm.sheet.id
                entry.chrono = chrono
                chrono += 1
                entry.save()
                entry.put(headers, row, xls_types=type_row)
            sm.sheet.save()

    def write_excel(self, filename):

        book = xlwt.Workbook()
        sh1 = book.add_sheet(self.sheet.sheet_name + " headers")
        headers = self.get_sheet_headers()
        array = self.get_sheet_array()
        SheetWriter.write_sheet(sh1, headers, array)
        sh2 = book.add_sheet(self.sheet.sheet_name + " tags")
        headers = self.get_sheet_headers()
        tags = self.get_sheet_tags()
        headers = [head + " : " + tag for tag, head in zip(tags, headers)]
        SheetWriter.write_sheet(sh2, headers, array)
        sh3 = book.add_sheet(self.sheet.sheet_name + " types")
        headers = self.get_sheet_headers()
        type_array = self.get_sheet_profiles()
        SheetWriter.write_sheet(sh3, headers, type_array)
        book.save(filename)