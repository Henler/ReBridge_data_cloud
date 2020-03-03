import numpy as np


class GasserDistribution:

    def c_from_table(self, scale):
        # Now do the Swiss Re classification
        # conversion factor CHF to SEK 9.3
        conv = 9.3
        if scale < 2e5 * conv:
            c = 1.5
        elif scale < 4e5 * conv:
            c = 2
        elif scale < 1e6 * conv:
            c = 3
        elif 1e6 * conv <= scale:
            c = 4
        else:
            print(scale)

        return c

    def exposure_curves(self, x, c=None, scale=1):
        if c is None:
            c = self.c_from_table(scale)
        y = x / scale
        b = np.exp(3.1 - 0.15*(1+c)*c)
        g = np.exp((0.78 + 0.12*c)*c)
        # print("b is: " + str(b) + " and g is: " + str(g))
        val = np.log(((g - 1) * b + (1 - g * b) * b ** y) / (1 - b)) / np.log(g * b)
        return val

    def cdf(self, x, c=None, scale=1):
        if c is None:
            c = self.c_from_table(scale)
        y = x / scale
        b = np.exp(3.1 - 0.15 * (1 + c) * c)
        g = np.exp((0.78 + 0.12 * c) * c)
        val = 1 - (1 - b) / ((g - 1) * b ** (1 - y) + (1 - g * b))
        return val

    def sf(self, x, c=None, scale=1):
        return 1 - self.cdf(x, c=c, scale=scale)

    def inverse_cdf(self, x, c=None, scale=1):
        if c is None:
            c = self.c_from_table(scale)
        b = np.exp(3.1 - 0.15 * (1 + c) * c)
        g = np.exp((0.78 + 0.12 * c) * c)
        gamma = (1 - b) / ((1 - x) * (g - 1)) - (1 - g * b)/(g - 1)
        val = 1 - np.log(gamma)/np.log(b)
        return val * scale

    def pdf(self, x, c=None, scale=1):
        if c is None:
            c = self.c_from_table(scale)
        y = x / scale
        b = np.exp(3.1 - 0.15 * (1 + c) * c)
        g = np.exp((0.78 + 0.12 * c) * c)
        val = ((b - 1) * (g - 1) * np.log(b) * b ** (1 -y)) / ((g - 1) * b ** (1 - y) + (1 - g * b)) ** 2
        return val / scale

    def rvs(self, c=None, size=1, scale=1):
        if c is None:
            c = self.c_from_table(scale)
        else:
            # only scalar valued c supported
            assert len(c) == 1
        g = np.exp((0.78 + 0.12 * c) * c)

        # sample with inverse method
        uni = np.random.uniform(size=size)
        outs = np.ones(size)
        outs[uni < 1-1/g] = self.inverse_cdf(uni[uni < 1-1/g], c=c)
        outs = outs * scale
        return outs



