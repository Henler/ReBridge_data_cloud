from python_back_end.utilities.state_handling import DataHolder
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
import numpy as np

dh1 = DataHolder.from_pickle_file(pdir.TEMP_DIR + "from_views.pickle")
dh2 = DataHolder.from_pickle_file(pdir.TEMP_DIR + "from_backend.pickle")

for ds1, ds2 in zip(dh1, dh2):
    bools = ds1.df_data == ds2.df_data
    self_bool1 = ds1.df_data == ds1.df_data
    self_bool2 = ds2.df_data == ds2.df_data
    complement = bools == self_bool2
    p_bools = ds1.df_profiles == ds2.df_profiles

    if not np.all(bools):
        print(np.all(complement))
        print(np.all(p_bools))