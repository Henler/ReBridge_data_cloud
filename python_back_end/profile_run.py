from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.utilities.sheet_io import ExcelLoader
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.triangle_formatting.triangle_pipeline import TrianglePipeline
import pandas as pd
from python_back_end.logConfig import LOGGING
import logging.config
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=4973, stdoutToServer=True, stderrToServer=True)
logging.config.dictConfig(LOGGING)
"""
    Mini program intended for profiling of the code.
    """


def main(file, settings):

    print(file)
    sr_list, file_name = ExcelLoader.load_excel(file)
    dh = DataHolder(file_name)
    for sr in sr_list:
        dh.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                     pd.DataFrame(columns=sr.headers, data=sr.xls_types), orig_sheet_name=sr.sheet_name)
    dummy, new_dh = TrianglePipeline.triangle_pipeline_dh(dh, tri_type=settings["tri_type"], n_outputs=settings["n_outputs"])
    temp_path = pdir.RESOURCES_DIR + "/temp/"
    new_dh.write_excel(temp_path + file_name)


if __name__ == '__main__':
    settings = {"tri_type": "single", "n_outputs": 1}

    main("SOME_FILE_NAME", settings)
