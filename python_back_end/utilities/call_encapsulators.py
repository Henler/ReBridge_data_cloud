from unittest import TestCase
import time
from python_back_end.utilities.state_handling import DataHolder


class DataHolderCallEncapsulator():
    """
    Encapsulates calls that modifies a state holder. Does nothing with the call
    """
    @staticmethod
    def encapsulate_call(function, dh, **kwargs):
        return function(dh, **kwargs)

class DataHolderCallTimeEncapsulator():
    """
    Encapsulates calls that modifies a state holder. Times and prints the call time.
    """
    @staticmethod
    def encapsulate_call(function, dh, **kwargs):
        start = time.time()
        out = function(dh, **kwargs)
        print("Time elapsed for function: " +str(function) + " is " + str(time.time()-start))
        return out


class DataHolderCallOutputEncapsulator:
    """
    Encapsulates calls that modifies a state holder. If the call is strip_triangles or build_triangle_from_table
    (calls at the end of their respective pipelines), a pickle of the state is saved for output testing.
    """

    def __init__(self, outfile, info_dict):
        self.outfile = outfile
        self.info_dict = info_dict

    def encapsulate_call(self, function, dh, **kwargs):
        out = function(dh, **kwargs)
        if isinstance(out, DataHolder):
            dh = out
        elif isinstance(out, tuple):
            dh = out[0]
        func_name = function.__name__
        if func_name == "strip_triangles" or func_name == "build_triangle_from_table":
            dh.write_excel(self.outfile)
            dh.to_pickle_file(self.outfile + ".pickle", extra_content=self.info_dict)
        return out


class DataHolderCallTestEncapsulator(TestCase):
    """
    Encapsulates calls that modifies a state holder. Test the results after each DataHolder call against a saved state.
    """

    def __init__(self, out_path, sol_path):
        self.out_path = out_path
        self.sol_path = sol_path
        self.counter = 0

    def encapsulate_call(self, function, dh, **kwargs):
        out = function(dh, **kwargs)

        if isinstance(out, DataHolder):
            dh = out
        elif isinstance(out, tuple):
            dh = out[0]
            # Read the true solution
        sol = DataHolder.from_pickle_file(self.sol_path + dh.name + "_" + str(self.counter) + ".pickle")
        dh = dh.merge_in_original_sheets(save_sheet_names=True)
        if not dh.equals(sol):
            print(function)
            dh.write_excel(self.out_path + "candidate.xls")
            sol.write_excel(self.out_path + "solution.xls")
            self.assertTrue(dh.equals(sol))
        self.counter += 1
        return out


class DataHolderCallSaveEncapsulator:
    """
    Encapsulates calls that modifies a state holder. Saves a state as a ground truth after each call. Only use when
    it's known that the right output is produced
    """
    def __init__(self, sol_path):
        self.sol_path = sol_path
        self.counter = 0

    def encapsulate_call(self, function, dh, **kwargs):
        #print('hi')
        out = function(dh, **kwargs)
        if isinstance(out, DataHolder):
            dh = out
        elif isinstance(out, tuple):
            dh = out[0]
        merged = dh.merge_in_original_sheets(save_sheet_names=True)
        merged.to_pickle_file(self.sol_path + dh.name + "_" + str(self.counter) + ".pickle")
        self.counter += 1
        return out