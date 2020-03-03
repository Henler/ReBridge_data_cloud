import xlrd
import numpy as np
import matplotlib.pyplot as plt
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.triangle_formatting.triangle_utils import InputMatcher
from python_back_end.utilities.help_functions import mad
import pickle


class TriangleDistributionMaker:

    def __init__(self):
        self.distr_dict = dict()


    def read_triangles_from_xls(self):
        path = pdir.RESOURCES_DIR + '/Target_distributions/'
        files_dict = {
            ps.CAT_RESERVED_NAME: 'Claims_res_distributions.xls',
            ps.CAT_PAID_NAME: 'Claims_paid_distributions.xls',
            ps.CAT_PREMIUM_NAME: 'Premium_distributions.xls'
        }
        # Read the distributions
        for key in files_dict:
            xls = xlrd.open_workbook(path+files_dict[key])
            self.distr_dict[key] = None
            sheet_names = xls.sheet_names()
            for sheet_ind in range(len(sheet_names)):
                triang = None
                sheet = xls.sheet_by_index(sheet_ind)
                #Read col_wise
                for i in range(sheet.ncols):
                    col = np.array([r.value for r in sheet.col(i) if r.value is not ""])
                    if triang is None:
                        triang = col
                    else:
                        triang= np.hstack((triang, col))
                # take log of triang
                triang = triang[triang > 0]
                #triang = np.log(triang)
                #normalize mad to 1

                triang = triang/mad(triang)
                triang = triang - np.mean(triang)
                #triang = triang / np.std(triang)
                if self.distr_dict[key] is None:
                    self.distr_dict[key] = triang
                else:
                    self.distr_dict[key] = np.hstack((self.distr_dict[key],triang))
            #print(TriangleDistributionMaker.mad(triang))
        out_dict = dict()
        # now plot everything
        for key in self.distr_dict:
            fig, ax = plt.subplots()
            out_dict[key] = ax.hist(self.distr_dict[key], bins=InputMatcher.BINS)
            fig.savefig(pdir.TEMP_DIR+key+"_distributions.pdf")

        with open(pdir.RESOURCES_DIR + "/distribution_dict.pickle", 'wb') as handle:
            pickle.dump(self.distr_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    tdm = TriangleDistributionMaker()
    tdm.read_triangles_from_xls()