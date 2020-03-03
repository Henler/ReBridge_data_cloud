import numpy as np
import scipy.linalg.blas as blas

def meanOfVecList(inlist):
    means = inlist[0]
    for i in range(1,len(inlist)):
        means+=inlist[i]
    means/=len(inlist)
    return means

def PTSRF(data):
    n = len(data[0])
    #print(n)
    #print(len(data))
    #print(data[0].mean())
    variances = [vals.std()**2 for vals in data]
    variancesMean = meanOfVecList(variances)
    means = [vals.mean() for vals in data]
    meansMean = meanOfVecList(means)
    #print(variances[0].shape)
    #print(means[0].shape)
    W = np.array(variancesMean)
    B = n * np.square(np.array((np.array(means[0])-meansMean)))
    for i in range(1,len(means)):
        #print(i)
        B += n * np.square(np.array((np.array(means[i])-meansMean)))
    #print(B.shape)
    #print(W.shape)
    varEst = (1 - 1/n) * W + 1/n*B
    return np.sqrt(varEst/W)


def effectiveSampleSize(samples, monotSensitivity=0.01):
    length = float(len(samples))

    mean = sum(samples) / length
    shiftedSamples = np.array([x - mean for x in samples], float, order="F")
    gamma = [(blas.ddot(shiftedSamples, shiftedSamples, offx=i) / length) for i in range(len(samples))]
    monot = next(i for i, g in enumerate(gamma) if g < monotSensitivity * gamma[0])
    gammaSum = sum(gamma[1:monot])
    v = (gamma[0] + 2 * gammaSum) / length
    ess = gamma[0] / float(v)
    return ess


def sampleSizeFromMatrix(inMatrix, runtimes, filenames):
    assert len(filenames) == len(runtimes)
    esss = {}
    for i in range(len(filenames)):
        esss[filenames[i]] = [runtimes[i]]

        effectiveSamples = [effectiveSampleSize(inMatrix[i][inMatrix[i].columns[n]]) for n in
                            range(len(inMatrix[0].columns))]
        esss[filenames[i]] += effectiveSamples
        esss[filenames[i]].append(min(effectiveSamples))
        esss[filenames[i]].append(min(effectiveSamples) / inMatrix[i].shape[0])
        esss[filenames[i]].append(min(effectiveSamples) / runtimes[i])
    return esss


def binMat2IntVec(inBinMat):
    binMat = inBinMat.astype(int)
    intVec = binMat[:, 0]
    for i in range(1, binMat.shape[1]):
        intVec+=binMat[:, i]*(2**i)
    return intVec