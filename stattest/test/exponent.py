import math
from abc import ABC

import numpy as np
import scipy.special as scipy_special
from typing_extensions import override

from stattest.core.distribution import expon
from stattest.test.goodness_of_fit import AbstractGoodnessOfFitTestStatistic


class AbstractExponentialityTestStatistic(AbstractGoodnessOfFitTestStatistic, ABC):
    def __init__(self, lam=1):
        self.lam = lam

    @staticmethod
    @override
    def code():
        return (
            "EXPONENTIALITY"
            + "_"
            + super(AbstractGoodnessOfFitTestStatistic, AbstractGoodnessOfFitTestStatistic).code()
        )

    @override
    def _generate(self, size):
        return expon.generate_expon(size, self.lam)


class EPTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "EP" + "_" + super(EPTestExp, EPTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Epps and Pulley test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        ep : float
            The test statistic.
        """

        n = len(rvs)
        y = rvs / np.mean(rvs)
        ep = np.sqrt(48 * n) * np.sum(np.exp(-y) - 1 / 2) / n

        return ep


class KSTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "KS" + "_" + super(KSTestExp, KSTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Kolmogorov and Smirnov test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        ks : float
            The test statistic.
        """

        n = len(rvs)
        y = rvs / np.mean(rvs)
        z = np.sort(1 - np.exp(-y))
        j1 = np.arange(1, n + 1) / n
        m1 = np.max(j1 - z)
        j2 = (np.arange(0, n) + 1) / n
        m2 = np.max(z - j2)
        ks = max(m1, m2)  # TODO: fix mistype

        return ks


class AHSTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "AHS" + "_" + super(AHSTestExp, AHSTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Statistic of the exponentiality test based on Ahsanullah characterization.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        a : float
            The test statistic.
            :param rvs:
        """

        n = len(rvs)
        h = 0
        g = 0
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if abs(rvs[i] - rvs[j]) < rvs[k]:
                        h += 1
                    if 2 * min(rvs[i], rvs[j]) < rvs[k]:
                        g += 1
        a = (h - g) / (n**3)

        return a


class ATKTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "ATK" + "_" + super(ATKTestExp, ATKTestExp).code()

    @override
    def execute_statistic(self, rvs, p=0.99):
        """
        Atkinson test statistic for exponentiality.

        Parameters
        ----------
        p : float
            Statistic parameter.
        rvs : array_like
            Array of sample data.

        Returns
        -------
        atk : float
            The test statistic.
        """

        n = len(rvs)
        y = np.mean(rvs)
        m = np.mean(np.power(rvs, p))
        r = (m ** (1 / p)) / y
        atk = np.sqrt(n) * np.abs(r - scipy_special.gamma(1 + p) ** (1 / p))

        return atk


class COTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "CO" + "_" + super(COTestExp, COTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Cox and Oakes test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        co : float
            The test statistic.
            :param rvs:
        """

        n = len(rvs)
        y = rvs / np.mean(rvs)
        y = np.log(y) * (1 - y)
        co = np.sum(y) + n

        return co


class CVMTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "CVM" + "_" + super(CVMTestExp, CVMTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Cramer-von Mises test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        cvm : float
            The test statistic.
        """

        n = len(rvs)
        y = rvs / np.mean(rvs)
        z = np.sort(1 - np.exp(-y))
        c = (2 * np.arange(1, n + 1) - 1) / (2 * n)
        z = (z - c) ** 2
        cvm = 1 / (12 * n) + np.sum(z)

        return cvm


class DSPTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "DSP" + "_" + super(DSPTestExp, DSPTestExp).code()

    @override
    def execute_statistic(self, rvs, b=0.44):
        """
        Deshpande test statistic for exponentiality.

        Parameters
        ----------
        b : float
            Statistic parameter.
        rvs : array_like
            Array of sample data.

        Returns
        -------
        des : float
            The test statistic.
        """

        n = len(rvs)
        des = 0
        for i in range(n):
            for k in range(n):
                if (i != k) and (rvs[i] > b * rvs[k]):
                    des += 1
        des /= n * (n - 1)

        return des


class EPSTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "EPS" + "_" + super(EPSTestExp, EPSTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Epstein test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        eps : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        x = np.concatenate(([0], rvs))
        d = (np.arange(n, 0, -1)) * (x[1 : n + 1] - x[0:n])
        eps = 2 * n * (np.log(np.sum(d) / n) - (np.sum(np.log(d))) / n) / (1 + (n + 1) / (6 * n))

        return eps


class FZTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "FZ" + "_" + super(FZTestExp, FZTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Frozini test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        froz : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        rvs = np.array(rvs)
        y = np.mean(rvs)
        froz = (1 / np.sqrt(n)) * np.sum(
            np.abs(1 - np.exp(-rvs / y) - (np.arange(1, n + 1) - 0.5) / n)
        )

        return froz


class GiniTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "Gini" + "_" + super(GiniTestExp, GiniTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Gini test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        gini : float
            The test statistic.
        """

        n = len(rvs)
        a = np.arange(1, n)
        b = np.arange(n - 1, 0, -1)
        a = a * b
        x = np.sort(rvs)
        k = x[1:] - x[:-1]
        gini = np.sum(k * a) / ((n - 1) * np.sum(x))

        return gini


class GDTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "GD" + "_" + super(GDTestExp, GDTestExp).code()

    @override
    def execute_statistic(self, rvs, r=None):
        """
        Gnedenko F-test statistic for exponentiality.

        Parameters
        ----------
        r : float
            Statistic parameter.
        rvs : array_like
            Array of sample data.

        Returns
        -------
        gd : float
            The test statistic.
        """

        if r is None:
            r = round(len(rvs) / 2)
        n = len(rvs)
        x = np.sort(np.concatenate(([0], rvs)))
        d = (np.arange(n, 0, -1)) * (x[1 : n + 1] - x[0:n])
        gd = (sum(d[:r]) / r) / (sum(d[r:]) / (n - r))

        return gd


class HMTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "HM" + "_" + super(HMTestExp, HMTestExp).code()

    @override
    def execute_statistic(self, rvs, r=None):
        """
        Harris' modification of Gnedenko F-test.

        Parameters
        ----------
        r : float
            Statistic parameter.
        rvs : array_like
            Array of sample data.

        Returns
        -------
        hm : float
            The test statistic.
        """

        if r is None:
            r = round(len(rvs) / 4)
        n = len(rvs)
        x = np.sort(np.concatenate(([0], rvs)))
        d = (np.arange(n, 0, -1)) * (x[1 : n + 1] - x[:n])
        hm = ((np.sum(d[:r]) + np.sum(d[-r:])) / (2 * r)) / ((np.sum(d[r:-r])) / (n - 2 * r))

        return hm


class HG1TestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "HG1" + "_" + super(HG1TestExp, HG1TestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Hegazy-Green 1 test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        hg : float
            The test statistic.
        """

        n = len(rvs)
        x = np.sort(rvs)
        b = -np.log(1 - np.arange(1, n + 1) / (n + 1))
        hg = (n ** (-1)) * np.sum(np.abs(x - b))

        return hg


class HPTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "HP" + "_" + super(HPTestExp, HPTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Hollander-Proshan test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        hp : float
            The test statistic.
        """

        n = len(rvs)
        t = 0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if (i != j) and (i != k) and (j < k) and (rvs[i] > rvs[j] + rvs[k]):
                        t += 1
        hp = (2 / (n * (n - 1) * (n - 2))) * t

        return hp


class KMTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "KM" + "_" + super(KMTestExp, KMTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Kimber-Michael test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        km : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        y = np.mean(rvs)
        s = (2 / np.pi) * np.arcsin(np.sqrt(1 - np.exp(-(rvs / y))))
        r = (2 / np.pi) * np.arcsin(np.sqrt((np.arange(1, n + 1) - 0.5) / n))
        km = max(abs(r - s))

        return km


class KCTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "KC" + "_" + super(KCTestExp, KCTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Kochar test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        kc : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        u = np.array([(i + 1) / (n + 1) for i in range(n)])
        j = 2 * (1 - u) * (1 - np.log(1 - u)) - 1
        kc = np.sqrt(108 * n / 17) * (np.sum(j * rvs)) / np.sum(rvs)

        return kc


class LZTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "LZ" + "_" + super(LZTestExp, LZTestExp).code()

    @override
    def execute_statistic(self, rvs, p=0.5):
        """
        Lorenz test statistic for exponentiality.

        Parameters
        ----------
        p : float
            Statistic parameter.
        rvs : array_like
            Array of sample data.

        Returns
        -------
        lz : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        lz = sum(rvs[: int(n * p)]) / sum(rvs)

        return lz


class MNTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "MN" + "_" + super(MNTestExp, MNTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Moran test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        mn : float
            The test statistic.
        """

        # n = len(rvs)
        y = np.mean(rvs)
        mn = -scipy_special.digamma(1) + np.mean(np.log(rvs / y))

        return mn


class PTTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "PT" + "_" + super(PTTestExp, PTTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Pietra test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        pt : float
            The test statistic.
        """

        n = len(rvs)
        xm = np.mean(rvs)
        pt = np.sum(np.abs(rvs - xm)) / (2 * n * xm)

        return pt


class SWTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "SW" + "_" + super(SWTestExp, SWTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Shapiro-Wilk test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        sw : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        y = np.mean(rvs)
        sw = n * (y - rvs[0]) ** 2 / ((n - 1) * np.sum((rvs - y) ** 2))

        return sw


class RSTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "RS" + "_" + super(RSTestExp, RSTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Statistic of the exponentiality test based on Rossberg characterization.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        rs : float
            The test statistic.
        """

        n = len(rvs)
        sh = 0
        sg = 0
        for m in range(n):
            h = 0
            for i in range(n - 2):
                for j in range(i + 1, n - 1):
                    for k in range(j + 1, n):
                        if (
                            rvs[i]
                            + rvs[j]
                            + rvs[k]
                            - 2 * min(rvs[i], rvs[j], rvs[k])
                            - max(rvs[i], rvs[j], rvs[k])
                            < rvs[m]
                        ):
                            h += 1
            h = ((6 * math.factorial(n - 3)) / math.factorial(n)) * h
            sh += h
        for m in range(n):
            g = 0
            for i in range(n - 1):
                for j in range(i + 1, n):
                    if min(rvs[i], rvs[j]) < rvs[m]:
                        g += 1
            g = ((2 * math.factorial(n - 2)) / math.factorial(n)) * g
            sg += g
        rs = sh - sg
        rs /= n

        return rs


class WETestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "WE" + "_" + super(WETestExp, WETestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        WE test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        we : float
            The test statistic.
        """

        n = len(rvs)
        m = np.mean(rvs)
        v = np.var(rvs)
        we = (n - 1) * v / (n**2 * m**2)

        return we


class WWTestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "WW" + "_" + super(WWTestExp, WWTestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Wong and Wong test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        ww : float
            The test statistic.
        """

        # n = len(rvs)
        ww = max(rvs) / min(rvs)

        return ww


class HG2TestExp(AbstractExponentialityTestStatistic):
    @staticmethod
    @override
    def code():
        return "HG2" + "_" + super(HG2TestExp, HG2TestExp).code()

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Hegazy-Green 2 test statistic for exponentiality.

        Parameters
        ----------
        rvs : array_like
            Array of sample data.

        Returns
        -------
        hg : float
            The test statistic.
        """

        n = len(rvs)
        rvs.sort()
        b = -np.log(1 - np.arange(1, n + 1) / (n + 1))
        hg = (n ** (-1)) * np.sum((rvs - b) ** 2)

        return hg


# TODO: check all mistype warnings
