from pomegranate import *
import numpy as np


class CompoundExmixPoisson:

    def __init__(self, in_sample, frequencies):
        sample = in_sample.reshape((len(in_sample), 1))
        #print(sample.shape)
        self.model = GeneralMixtureModel.from_samples(ExponentialDistribution, n_components=2, X=np.array(sample))
        self.intensity = np.mean(frequencies)

    def compound_sample(self, n):
        incidents = np.random.poisson(self.intensity, n)
        costs = np.zeros(incidents.shape)

        for i in range(len(incidents)):
            costs[i] += np.sum(self.model.sample(incidents[i]))

        return costs

    def inner_sample(self, n):
        return self.model.sample(n)
