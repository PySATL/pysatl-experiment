import math

from scipy.stats import distributions

from stattest.core.distribution.weibull import generate_weibull_cdf, generate_weibull_logcdf, generate_weibull_logsf
import numpy as np
from scipy.optimize import minimize_scalar
from stattest.test.models import AbstractTestStatistic
from stattest.test.common import KSTestStatistic, ADTestStatistic, LillieforsTest, CrammerVonMisesTestStatistic


class LillieforsWiebullTest(LillieforsTest):
    def __init__(self, l=1, k=5):
        super().__init__()
        self.l = l
        self.k = k

    @staticmethod
    def code():
        return 'LILLIE_WEIBULL'

    def execute_statistic(self, rvs):
        rvs_sorted = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs_sorted, l=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class CrammerVonMisesWeibullTest(CrammerVonMisesTestStatistic):
    def __init__(self, l=1, k=5):
        super().__init__()
        self.l = l
        self.k = k

    def execute_statistic(self, rvs, cdf_vals):
        rvs_sorted = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs_sorted, l=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class ADWeibullTest(ADTestStatistic):
    def __init__(self, l=1, k=5):
        super().__init__()
        self.l = l
        self.k = k

    @staticmethod
    def code():
        return 'AD_WEIBULL'

    def execute_statistic(self, rvs):
        rvs = np.log(rvs)
        y = np.sort(rvs)
        xbar, s = distributions.gumbel_l.fit(y)
        w = (y - xbar) / s
        logcdf = distributions.gumbel_l.logcdf(w)
        logsf = distributions.gumbel_l.logsf(w)

        return super().execute_statistic(rvs, log_cdf=logcdf, log_sf=logsf, w=w)


class KSWeibullTest(KSTestStatistic):

    def __init__(self, alternative='two-sided', mode='auto', l=1, k=5):
        super().__init__(alternative, mode)
        self.l = l
        self.k = k

    @staticmethod
    def code():
        return 'KS_WEIBULL'

    def execute_statistic(self, rvs):
        rvs = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs, l=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class OKTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'OK'

    # Test statistic of Ozturk and Korukoglu
    def execute_statistic(self, rvs):
        """
        On the W Test for the Extreme Value Distribution
        Aydin Öztürk
        Biometrika
        Vol. 73, No. 3 (Dec., 1986), pp. 738-740 (3 pages)

        :param rvs:
        :return:
        """
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        I = np.arange(1, n + 1)

        l = I[:n - 1]
        Sig = np.sum((2 * np.concatenate((l, [n])) - 1 - n) * y) / (0.693147 * (n - 1))
        w = np.log((n + 1) / (n - l + 1))
        Wi = np.concatenate((w, [n - np.sum(w)]))
        Wn = w * (1 + np.log(w)) - 1
        a = 0.4228 * n - np.sum(Wn)
        Wn = np.concatenate((Wn, [a]))
        b = (0.6079 * np.sum(Wn * y) - 0.2570 * np.sum(Wi * y))
        stat = b / Sig
        WPP_statistic = (stat - 1 - 0.13 / np.sqrt(n) + 1.18 / n) / (0.49 / np.sqrt(n) - 0.36 / n)

        return WPP_statistic


class SBTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'SB'

    # Test statistic of Shapiro Wilk
    def execute_statistic(self, rvs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        I = np.arange(1, n + 1)

        yb = np.mean(y)
        S2 = np.sum((y - yb) ** 2)
        l = I[:n - 1]
        w = np.log((n + 1) / (n - l + 1))
        Wi = np.concatenate((w, [n - np.sum(w)]))
        Wn = w * (1 + np.log(w)) - 1
        a = 0.4228 * n - np.sum(Wn)
        Wn = np.concatenate((Wn, [a]))
        b = (0.6079 * np.sum(Wn * y) - 0.2570 * np.sum(Wi * y)) / n
        WPP_statistic = n * b ** 2 / S2

        return WPP_statistic


class ST2TestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'ST2'

    # Smooth test statistic based on the kurtosis
    def execute_statistic(self, rvs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        x = np.sort(-y)

        s = sum((x - np.mean(x)) ** 2) / n
        b1 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
        b2 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 4) / n
        V4 = (b2 - 7.55 * b1 + 3.21) / np.sqrt(219.72 / n)
        WPP_statistic = V4 ** 2

        return WPP_statistic


class ST1TestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'ST1'

    # Smooth test statistic based on the skewness
    def execute_statistic(self, rvs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        x = np.sort(-y)

        s = sum((x - np.mean(x)) ** 2) / n
        b1 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
        V3 = (b1 - 1.139547) / np.sqrt(20 / n)
        WPP_statistic = V3 ** 2

        return WPP_statistic


class REJGTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'REJG'

    # Test statistic of Evans, Johnson and Green based on probability plot
    def execute_statistic(self, rvs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        I = np.arange(1, n + 1)

        beta_shape = self.MLEst(rvs)[1]
        m = np.log(-(np.log(1 - (I - 0.3175) / (n + 0.365)))) / beta_shape
        s = (sum((y - np.mean(y)) * m)) ** 2 / ((sum((y - np.mean(y)) ** 2)) * sum((m - np.mean(m)) ** 2))
        WPP_statistic = s ** 2

        return WPP_statistic

    def MLEst(self, x):
        if np.sum(x <= 0):
            raise ValueError("Data x is not a positive sample")

        lv = -np.log(x)
        y = np.sort(lv)

        def f1(toto, vect):
            if toto != 0:
                f1 = np.sum(vect) / len(vect)
                f1 -= np.sum(vect * np.exp(-vect * toto)) / np.sum(np.exp(-vect * toto)) - 1 / toto
            else:
                f1 = 100
            return abs(f1)

        result = minimize_scalar(f1, bounds=(0.0001, 50), args=(y,), method='bounded')
        t = result.x
        aux = np.sum(np.exp(-y * t)) / len(x)
        ksi = -(1 / t) * np.log(aux)

        y = -(y - ksi) * t
        # 'eta', 'beta', 'y'
        return (np.exp(-ksi), t, y)


class RSBTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'RSB'

    # Test statistic of Smith and Bain based on probability plot
    def execute_statistic(self, rvs):
        n = len(rvs)
        I = np.arange(1, n + 1)

        m = I / (n + 1)
        m = np.log(-np.log(1 - m))
        mb = np.mean(m)
        xb = np.mean(np.log(rvs))
        R = (sum((np.log(rvs) - xb) * (m - mb))) ** 2
        R = R / sum((np.log(rvs) - xb) ** 2)
        R = R / sum((m - mb) ** 2)
        WPP_statistic = n * (1 - R)

        return WPP_statistic


class MSFTestStatistic(AbstractTestStatistic):
    def __init__(self, l=1, k=5):
        super().__init__()
        self.l = l
        self.k = k

    @staticmethod
    def code():
        return 'MSF'

    # Mann-Scheuer-Fertig statistic only right censoring
    def execute_statistic(self, rvs):
        """
        Mann N.R., Scheuer E.M. and Fertig K.W., A new goodness-of-fit test for the two-parameter Weibull or
        extreme-value distribution, Communications in Statistics, 2, 383-400, 1973.

        :param rvs:
        :return:
        """
        m = len(rvs)
        # n = m + s + r
        A = np.sort(np.log(rvs))

        l1 = math.floor(m / 2)
        l2 = m - l1 - 1
        S = sum((A[(l1 + 2):m] - A[(l1 + 1):(m - 1)]) / (X[(l1 + 2):m] - X[(l1 + 1):(m - 1)]))
        S = S / sum((A[2:m] - A[1:(m - 1)]) / (X[2:m] - X[1:(m - 1)]))

        return S


class LOCTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'LOC'

    # Lockhart-O'Reilly-Stephens test statistic
    def execute_statistic(self, rvs):
        """
        Lockhart R.A., O'Reilly F. and Stephens M.A., Tests for the extreme-value and Weibull distributions based on
        normalized spacings, Naval Research Logistics Quarterly, 33, 413-421, 1986.

        :param rvs:
        :return:
        """
        m = len(rvs)
        A = np.sort(np.log(rvs))
        d2 = A[2:m] - A[1:(m - 1)]
        X = GoFNS(r + 1, n, m)
        mu2 = X[2:m] - X[1:(m - 1)]
        G2 = d2 / mu2

        z = []
        for i in range(1, m - 1):
            z.append(np.sum(G2[:i]) / np.sum(G2))
        z = sorted(z)
        z1 = sorted(z, reverse=True)
        I = range(1, m - 1)
        NS_statistic = -(m - 2) - (1 / (m - 2)) * np.sum((2 * np.array(I) - 1) * (np.log(z) + np.log(z1)))

        return NS_statistic


class TSTestStatistic(AbstractTestStatistic):

    @staticmethod
    def code():
        return 'TS'

    # Tiku-Singh test statistic
    def execute_statistic(self, rvs):
        """
        Tiku M.L. and Singh M., Testing the two-parameter Weibull distribution, Communications in Statistics,
        10, 907-918, 1981.

        :param rvs:
        :return:
        """
        m = len(rvs)
        A = np.sort(np.log(rvs))
        d1 = A[2:(m - 1)] - A[1:(m - 2)]
        d2 = A[2:m] - A[1:(m - 1)]
        X = GoFNS(r + 1, n, m)
        mu1 = X[2:(m - 1)] - X[1:(m - 2)]
        mu2 = X[2:m] - X[1:(m - 1)]
        G1 = d1 / mu1
        G2 = d2 / mu2

        w1 = 2 * (sum((n - s - 1 - l) * G1))
        w2 = (m - 2) * sum(G2)

        return w1 / w2
