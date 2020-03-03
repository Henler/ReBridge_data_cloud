import numpy as np
import xlrd
import xlwt
from xlutils.copy import copy
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.definitions import SheetTypeDefinitions
import time
from jpype import JClass
import subprocess
import json
import os
import time


class SheetReader:

    def __init__(self):
        self.row_vals = []
        self.xls_types = []
        self.headers = []
        self.sheet_name = ""
        self.status = "OUT_OF_BOUNDS"
        self.meta = set()

    @staticmethod
    def read_sheets(filename):
        #start = time.time()
        if os.name == 'nt':
            stream = subprocess.check_output(['java', '-jar', pdir.OUTER_SCOPE + "third_party/executable/executable.jar", filename])
            time.sleep(1)
        else:
            stream = subprocess.check_output([pdir.OUTER_SCOPE + "/third_party/executable/executable.jar", filename])
        #print(time.time() - start)
        native = json.loads(stream.decode('utf-8','ignore'))
        #print(time.time() - start)
        sr_list = [SheetReader.sheet_reader_from_dict(el) for el in native]
        #print(time.time() - start)
        return sr_list

    @staticmethod
    def sheet_reader_from_dict(dict):
        sr = SheetReader()
        sr.row_vals = np.array(dict["Vals"]).astype(object)
        sr.xls_types = np.array(dict["Types"]).astype(int)
        bools = sr.xls_types == SheetTypeDefinitions.FLOAT
        if np.sum(bools) > 0:
            v_float = np.vectorize(float)
            sr.row_vals[bools] = v_float(sr.row_vals[bools])
        sr.sheet_name = dict["Name"]
        if len(sr.row_vals) > 0:
            sr.status = "VERIFIED"
            ncols = len(sr.row_vals[0]) -1
            sr.headers = [str(num + 1).zfill(pp.N_DIGITS_HEADER_PADDING) + ". " + ps.HEADER_PLACE_HOLDER for num in range(ncols)]
            sr.headers.append(str(ncols + 1).zfill(pp.N_DIGITS_HEADER_PADDING) + ". " + ps.ORDER_COL_NAME)
        return sr


class SheetWriter:

    @staticmethod
    def write_sheet(sh, headers, array):
        for i in range(len(headers)):
            sh.write(0, i, headers[i])
        for i in range(len(array)):
            if isinstance(array[i], list):
                for j in range(len(array[i])):
                    sh.write(i+1, j, array[i][j])
            elif isinstance(array[i], dict):
                for j in range(len(array[i]['values'])):
                    sh.write(i+1, j, array[i]['values'][j])

    @staticmethod
    def trngs_to_excel(trngs, out_name="temp.xls"):
        book = xlwt.Workbook()
        SheetWriter.write_trngs_content(book, trngs)
        with open(pdir.TEMP_DIR + out_name, 'wb') as f:
            book.save(f)

    @staticmethod
    def trngs_to_existing_excel(trngs, filename):

        wb = copy(xlrd.open_workbook(filename))
        SheetWriter.write_trngs_content(wb, trngs)
        if filename.endswith('x'):
            wb.save(filename[:-1])
        else:
            wb.save(filename)

    @staticmethod
    def write_trngs_content(book, trngs):
        # Make sheet names
        sheet_names = list()
        for num, trng in enumerate(trngs):
            if len(trng['categories']) == 3:
                sheet_names.append(str(num+1) + " - Claims")
            else:
                sheet_names.append(str(num + 1) + " - Premiums")
        for num, trng in enumerate(trngs):
            conversion_dict = book._Workbook__worksheet_idx_from_name
            if sheet_names[num].lower() in conversion_dict:
                sh = book.get_sheet(conversion_dict[sheet_names[num].lower()])
            else:
                sh = book.add_sheet(sheet_names[num], cell_overwrite_ok=True)
            SheetWriter.write_sheet(sh, trng['headers'], trng['rows'])

class ExcelLoader:

    @staticmethod
    def load_excel(filename):
        sr_list = SheetReader.read_sheets(filename)

        return sr_list, filename.split("/")[-1]

