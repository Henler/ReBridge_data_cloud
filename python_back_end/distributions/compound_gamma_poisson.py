import numpy as np
from scipy.stats import gamma


class CompoundGammaPoisson:

    def __init__(self, sample, frequencies):

        self.shape, dummy_loc, self.scale = gamma.fit(sample, floc=0)
        self.intensity = np.mean(frequencies)

    def compound_sample(self, n):
        incidents = np.random.poisson(self.intensity, n)
        costs = np.zeros(incidents.shape)

        for i in range(len(incidents)):
            costs[i] += np.sum(np.random.gamma(self.shape, self.scale, incidents[i]))

        return costs

    def inner_sample(self, n):
        return np.random.gamma(self.shape, self.scale, n)



