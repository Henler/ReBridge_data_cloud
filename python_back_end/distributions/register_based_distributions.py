import numpy as np
from scipy.stats import poisson
from scipy.optimize import fmin_cobyla, minimize
from collections.abc import Iterable
from scipy.cluster.vq import vq, kmeans, whiten
UB = 1e0
EPS = 1e-6

class RegisterBased:

    def __init__(self, pd, frequencies, limits):

        self.inner_pd = pd
        self.intensity = np.mean(frequencies)
        self.limits = limits
        self.obj_n = len(self.limits)
        self.epsilon = 1e-7

    def sample(self, N, pars=None):
        if pars is None:
            pars = np.ones(self.par_num)
        # s = pars[0]
        scale_factor = 1
        weights = self.weights_from_features(pars)
        samples = [[] for i in range(N)]
        aggregated = np.zeros(N)
        for i in range(N):

            for j in range(self.obj_n):
                num = poisson.rvs(self.intensity * weights[j])
                if num > 0:
                    temp_num = self.inner_pd.rvs(scale=self.limits[j]*scale_factor, size=[num])
                    temp_num = np.minimum(temp_num, self.limits[j])
                    samples[i] += temp_num.tolist()
            aggregated[i] = np.sum(samples[i])

        return samples, aggregated

    def negloglike(self, pars, xs):
        if np.isnan(pars).any():
            return float("nan")
        if not isinstance(xs, Iterable):
            xs = np.array([xs])
        if type(xs) is not np.ndarray:
            xs = np.array(xs)
        # s = pars[0]
        fudge_factor = 0.1
        scale_factor = 1
        weights = self.weights_from_features(pars)

        temp = np.zeros(xs.size)
        for j in range(self.obj_n):
            small_xs = xs < self.limits[j]
            medium_xs = np.logical_and(self.limits[j] <= xs, xs < self.limits[j] + self.limits[j]*fudge_factor)
            temp[small_xs] += self.inner_pd.pdf(xs[small_xs],  scale=scale_factor*self.limits[j])*weights[j]
            #booleans = medium_xs == True
            if medium_xs.any():
                survival = self.inner_pd.sf(self.limits[j], scale=scale_factor * self.limits[j])
                temp[medium_xs] += survival/(self.limits[j]*fudge_factor)*weights[j]
            # if x < self.limits[j]:
            #     temp += self.inner_pd.pdf(x, s, scale=scale_factor*self.limits[j])
            # elif self.limits[j] <= x < self.limits[j] + self.limits[j]*fudge_factor:
            #     survival = self.inner_pd.sf(self.limits[j], s, scale=scale_factor*self.limits[j])
            #     temp += survival/(self.limits[j]*fudge_factor)

        if (temp == 0).any():
            return float("inf")

        logval = np.sum(np.log(temp))

        outval = -logval

        print(outval, pars)
        return outval

    def lb(self, x):
        return np.array(x) - EPS

    def ub(self, x):
        return UB - np.sum(x)

    def optimize_par(self, xs, start_pars=None):
        if start_pars is None:
            start_pars = np.ones(self.par_num)

        return fmin_cobyla(self.negloglike, start_pars, [self.lb, self.ub], args=[xs], consargs=(), rhoend=0.01, catol=EPS, rhobeg=0.1)

    def weights_from_features(self, pars):
        assert len(pars) == self.obj_n -1
        #feature_means = self.features - np.mean(self.features, axis=0)
        #feature_means /= np.std(feature_means)
        last_weight = UB-np.sum(pars)
        weights = np.array(pars.tolist() + [last_weight])
        weights = np.maximum(weights, 0)
        assert (weights >= 0).all()
        #excerpt = UB * len(pars) - np.sum(pars)
        #weights = np.exp(np.dot(self.features, pars))
        #weights = np.exp(np.dot(feature_means, pars))# + np.pi/2
        return weights / np.sum(weights)


