from multiprocessing import Pool
import sys
import numpy as np

class DebuggablePool:

    def __init__(self, n_cores):
        gettrace = getattr(sys, 'gettrace', None)
        if gettrace():
            print("Without pool")
            self.pool = None
        else:
            #print("With pool")
            self.pool = Pool(n_cores)

    def map(self, func, iterable):
        if self.pool is None:
            temp = [el for el in map(func, iterable)]
            return temp
        else:
            return self.pool.map(func, iterable)

    def close(self):
        if self.pool is not None:
            self.pool.close()
