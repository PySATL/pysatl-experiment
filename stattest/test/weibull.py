from abc import ABC

import numpy as np
from numpy import histogram
from scipy.optimize import minimize_scalar
from scipy.special import gamma
from scipy.stats import distributions
from typing_extensions import override

from stattest.core.distribution.weibull import generate_weibull_cdf
from stattest.test.common import (
    ADTestStatistic,
    Chi2TestStatistic,
    CrammerVonMisesTestStatistic,
    KSTestStatistic,
    LillieforsTest,
    MinToshiyukiTestStatistic,
)
from stattest.test.models import AbstractTestStatistic


class AbstractWeibullTestStatistic(AbstractTestStatistic, ABC):
    def __init__(self, a=1, k=1):
        self.l = a
        self.k = k

    @staticmethod
    @override
    def code():
        return "WEIBULL"


class MinToshiyukiWeibullTestStatistic(AbstractWeibullTestStatistic, MinToshiyukiTestStatistic):
    @override
    def code(self):
        return f"MT_{super().code()}"

    @override
    def execute_statistic(self, rvs):
        rvs = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs, a=self.l, k=self.k)
        return super().execute_statistic(cdf_vals)


class Chi2PearsonWiebullTest(AbstractWeibullTestStatistic, Chi2TestStatistic):
    @override
    def code(self):
        return f"CHI2_PEARSON_{super().code()}"

    @override
    def execute_statistic(self, rvs, **kwargs):
        rvs_sorted = np.sort(rvs)
        n = len(rvs)
        (observed, bin_edges) = histogram(rvs_sorted, bins=int(np.ceil(np.sqrt(n))))
        observed = observed / n
        expected = generate_weibull_cdf(bin_edges, a=self.l, k=self.k)
        expected = np.diff(expected)
        return super().execute_statistic(observed, expected, 1)


class LillieforsWiebullTest(AbstractWeibullTestStatistic, LillieforsTest):
    @override
    def code(self):
        return f"LILLIE_{super().code()}"

    @override
    def execute_statistic(self, rvs, **kwargs):
        rvs_sorted = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs_sorted, a=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class CrammerVonMisesWeibullTest(AbstractWeibullTestStatistic, CrammerVonMisesTestStatistic):
    @override
    def code(self):
        return f"CVM_{super().code()}"

    def execute_statistic(self, rvs):
        rvs_sorted = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs_sorted, a=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class ADWeibullTest(AbstractWeibullTestStatistic, ADTestStatistic):
    @override
    def code(self):
        return f"AD_{super().code()}"

    @override
    def execute_statistic(self, rvs, **kwargs):
        rvs = np.log(rvs)
        y = np.sort(rvs)
        xbar, s = distributions.gumbel_l.fit(y)
        w = (y - xbar) / s
        logcdf = distributions.gumbel_l.logcdf(w)
        logsf = distributions.gumbel_l.logsf(w)

        return super().execute_statistic(rvs, log_cdf=logcdf, log_sf=logsf, w=w)


class KSWeibullTest(AbstractWeibullTestStatistic, KSTestStatistic):
    @override
    def __init__(self, alternative="two-sided", mode="auto", a=1, k=5):
        AbstractWeibullTestStatistic.__init__(self, None)
        KSTestStatistic.__init__(self, alternative, mode)

        self.l = a
        self.k = k

    @override
    def code(self):
        return f"KS_{super().code()}"

    @override
    def execute_statistic(self, rvs, **kwargs):
        rvs = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs, a=self.l, k=self.k)
        return super().execute_statistic(rvs, cdf_vals)


class SBTestStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"SB_{super().code()}"

    # Test statistic of Shapiro Wilk
    @override
    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        interval = np.arange(1, n + 1)

        yb = np.mean(y)
        S2 = np.sum((y - yb) ** 2)
        _l = interval[: n - 1]
        w = np.log((n + 1) / (n - _l + 1))
        Wi = np.concatenate((w, [n - np.sum(w)]))
        Wn = w * (1 + np.log(w)) - 1
        a = 0.4228 * n - np.sum(Wn)
        Wn = np.concatenate((Wn, [a]))
        b = (0.6079 * np.sum(Wn * y) - 0.2570 * np.sum(Wi * y)) / n
        WPP_statistic = n * b**2 / S2

        return WPP_statistic


class ST2TestStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"ST2_{super().code()}"

    # Smooth test statistic based on the kurtosis
    @override
    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        x = np.sort(-y)

        s = sum((x - np.mean(x)) ** 2) / n
        b1 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
        b2 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 4) / n
        V4 = (b2 - 7.55 * b1 + 3.21) / np.sqrt(219.72 / n)
        WPP_statistic = V4**2

        return WPP_statistic


class ST1TestStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"ST1_{super().code()}"

    # Smooth test statistic based on the skewness
    @override
    def execute_statistic(self, rvs, *kwargs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        x = np.sort(-y)

        s = sum((x - np.mean(x)) ** 2) / n
        b1 = sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
        V3 = (b1 - 1.139547) / np.sqrt(20 / n)
        WPP_statistic = V3**2

        return WPP_statistic


class REJGTestStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"REJG_{super().code()}"

    # Test statistic of Evans, Johnson and Green based on probability plot
    @override
    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        lv = np.log(rvs)
        y = np.sort(lv)
        interval = np.arange(1, n + 1)

        beta_shape = self.MLEst(rvs)[1]
        m = np.log(-(np.log(1 - (interval - 0.3175) / (n + 0.365)))) / beta_shape
        s = (sum((y - np.mean(y)) * m)) ** 2 / (
            (sum((y - np.mean(y)) ** 2)) * sum((m - np.mean(m)) ** 2)
        )
        WPP_statistic = s**2

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

        result = minimize_scalar(f1, bounds=(0.0001, 50), args=(y,), method="bounded")
        t = result.x
        aux = np.sum(np.exp(-y * t)) / len(x)
        ksi = -(1 / t) * np.log(aux)

        y = -(y - ksi) * t
        # 'eta', 'beta', 'y'
        return (np.exp(-ksi), t, y)


class RSBTestStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"RSB_{super().code()}"

    # Test statistic of Smith and Bain based on probability plot
    @override
    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        interval = np.arange(1, n + 1)

        m = interval / (n + 1)
        m = np.log(-np.log(1 - m))
        mb = np.mean(m)
        xb = np.mean(np.log(rvs))
        R = (sum((np.log(rvs) - xb) * (m - mb))) ** 2
        R = R / sum((np.log(rvs) - xb) ** 2)
        R = R / sum((m - mb) ** 2)
        WPP_statistic = n * (1 - R)

        return WPP_statistic


class WeibullNormalizeSpaceTestStatistic(AbstractWeibullTestStatistic):
    @staticmethod
    def GoFNS(t, n, m):
        res = np.zeros(m)
        for i in range(m):
            p_r = (t + i) / (n + 1)
            q_r = 1 - p_r
            Q_r = np.log(-np.log(1 - p_r))
            d_Q_r = -1 / ((1 - p_r) * np.log(1 - p_r))
            d2_Q_r = d_Q_r / q_r - d_Q_r * d_Q_r
            d3_Q_r = d2_Q_r / q_r + d_Q_r / (q_r * q_r) - 2 * (d_Q_r * d2_Q_r)
            d4_Q_r = d3_Q_r / q_r + 2 * d2_Q_r / (q_r * q_r)
            d4_Q_r += 2 * d_Q_r / (q_r * q_r * q_r) - 2 * (d2_Q_r * d2_Q_r + d_Q_r * d3_Q_r)
            res[i] = Q_r + (p_r * q_r / (2 * (n + 2))) * d2_Q_r
            res[i] += (
                q_r
                * p_r
                / ((n + 2) * (n + 2))
                * (1 / 3 * (q_r - p_r) * d3_Q_r + 1 / 8 * p_r * q_r * d4_Q_r)
            )
        return res

    @override
    def execute_statistic(self, rvs, type_):
        m = len(rvs)
        s = 0  # can be defined
        r = 0  # can be defined
        n = m + s + r
        A = np.sort(np.log(rvs))
        d1 = A[1 : (m - 1)] - A[: (m - 2)]
        d2 = A[1:m] - A[: (m - 1)]
        X = TSWeibullTestStatistic.GoFNS(r + 1, n, m)
        mu1 = X[1 : (m - 1)] - X[: (m - 2)]
        mu2 = X[1:m] - X[: (m - 1)]
        a = np.arange(r + 1, n - s - 1)

        G1 = d1 / mu1
        G2 = d2 / mu2

        w1 = 2 * (np.sum((n - s - 1 - a) * G1))
        w2 = (m - 2) * np.sum(G2)

        NS_statistic = 0
        if type_ == "TS_WEIBULL":
            NS_statistic = w1 / w2
        elif type_ == "LOS_WEIBULL":
            z = []
            for i in range(1, m - 1):
                z.append(np.sum(G2[:i]) / np.sum(G2))
            z = sorted(z)
            z1 = sorted(z, reverse=True)
            interval = range(1, m - 1)
            NS_statistic = -(m - 2) - (1 / (m - 2)) * np.sum(
                (2 * np.array(interval) - 1) * (np.log(z) + np.log(1 - np.array(z1)))
            )
        elif type_ == "MSF_WEIBULL":
            if s != 0:
                raise ValueError("the test is only applied for right censoring")
            l1 = m // 2
            # l2 = m - l1 - 1
            S = np.sum((A[(l1 + 1) : m] - A[l1 : (m - 1)]) / (X[(l1 + 1) : m] - X[l1 : (m - 1)]))
            S = S / np.sum((A[1:m] - A[: (m - 1)]) / (X[1:m] - X[: (m - 1)]))
            NS_statistic = S

        return NS_statistic


class TSWeibullTestStatistic(WeibullNormalizeSpaceTestStatistic):
    @override
    def code(self):
        return f"TS_{super().code()}"

    # Tiku-Singh test statistic

    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Tiku M.L. and Singh M., Testing the two-parameter Weibull distribution, Communications in
        Statistics, 10, 907-918, 1981.

        :param rvs:
        :return:

        Parameters
        ----------
        **kwargs
        """
        return super().execute_statistic(rvs, self.code())


class LOSWeibullTestStatistic(WeibullNormalizeSpaceTestStatistic):
    @override
    def code(self):
        return f"LOS_{super().code()}"

    # Lockhart-O'Reilly-Stephens test statistic
    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Lockhart R.A., O'Reilly F. and Stephens M.A., Tests for the extreme-value and Weibull
        distributions based on normalized spacings, Naval Research Logistics Quarterly, 33, 413-421,
        1986.

        :param rvs:
        :return:

        Parameters
        ----------
        **kwargs
        """

        return super().execute_statistic(rvs, self.code())


class MSFWeibullTestStatistic(WeibullNormalizeSpaceTestStatistic):
    @override
    def code(self):
        return f"MSF_{super().code()}"

    # Lockhart-O'Reilly-Stephens test statistic
    @override
    def execute_statistic(self, rvs, **kwargs):
        """
        Mann N.R., Scheuer E.M. and Fertig K.W., A new goodness-of-fit test for the two-parameter
        Weibull or extreme-value distribution, Communications in Statistics, 2, 383-400, 1973.

        :param rvs:
        :return:

        Parameters
        ----------
        **kwargs
        """

        return super().execute_statistic(rvs, self.code())


class WPPWeibullTestStatistic(AbstractWeibullTestStatistic):
    @staticmethod
    def MLEst(x):
        if np.min(x) <= 0:
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

        result = minimize_scalar(f1, bounds=(0.0001, 50), args=(y,), method="bounded")
        t = result.x
        aux = np.sum(np.exp(-y * t)) / len(x)
        ksi = -(1 / t) * np.log(aux)

        y = -(y - ksi) * t
        return {"eta": np.exp(-ksi), "beta": t, "y": y}

    # Family of the test statistics based on the probability plot and
    # shapiro-Wilk type tests
    @staticmethod
    @override
    def execute_statistic(x, type_):
        n = len(x)
        lv = np.log(x)
        y = np.sort(lv)
        interval = np.arange(1, n + 1)

        WPP_statistic = 0
        if type_ == "OK_WEIBULL":
            a = interval[:-1]
            Sig = np.sum((2 * np.concatenate((a, [n])) - 1 - n) * y) / (np.log(2) * (n - 1))
            w = np.log((n + 1) / (n - a + 1))
            Wi = np.concatenate((w, [n - np.sum(w)]))
            Wn = w * (1 + np.log(w)) - 1
            a = 0.4228 * n - np.sum(Wn)
            Wn = np.concatenate((Wn, [a]))
            b = 0.6079 * np.sum(Wn * y) - 0.2570 * np.sum(Wi * y)
            stat = b / Sig
            WPP_statistic = (stat - 1 - 0.13 / np.sqrt(n) + 1.18 / n) / (
                0.49 / np.sqrt(n) - 0.36 / n
            )

        elif type_ == "SB_WEIBULL":
            yb = np.mean(y)
            S2 = np.sum((y - yb) ** 2)
            a = interval[:-1]
            w = np.log((n + 1) / (n - a + 1))
            Wi = np.concatenate((w, [n - np.sum(w)]))
            Wn = w * (1 + np.log(w)) - 1
            a = 0.4228 * n - np.sum(Wn)
            Wn = np.concatenate((Wn, [a]))
            b = (0.6079 * np.sum(Wn * y) - 0.2570 * np.sum(Wi * y)) / n
            WPP_statistic = n * b**2 / S2

        elif type_ == "RSB_WEIBULL":
            m = interval / (n + 1)
            m = np.log(-np.log(1 - m))
            mb = np.mean(m)
            xb = np.mean(np.log(x))
            R = (np.sum((np.log(x) - xb) * (m - mb))) ** 2
            R /= np.sum((np.log(x) - xb) ** 2)
            R /= np.sum((m - mb) ** 2)
            WPP_statistic = n * (1 - R)

        elif type_ == "REJG_WEIBULL":
            beta_shape = WPPWeibullTestStatistic.MLEst(x)["beta"]
            m = np.log(-(np.log(1 - (interval - 0.3175) / (n + 0.365)))) / beta_shape
            s = (np.sum((y - np.mean(y)) * m)) ** 2 / (
                np.sum((y - np.mean(y)) ** 2) * np.sum((m - np.mean(m)) ** 2)
            )
            WPP_statistic = s**2

        elif type_ == "SPP_WEIBULL":
            y = WPPWeibullTestStatistic.MLEst(x)["y"]
            r = 2 / np.pi * np.arcsin(np.sqrt((interval - 0.5) / n))
            s = 2 / np.pi * np.arcsin(np.sqrt(1 - np.exp(-np.exp(y))))
            WPP_statistic = np.max(np.abs(r - s))

        elif type_ == "ST1_WEIBULL":
            x = np.sort(-y)
            s = np.sum((x - np.mean(x)) ** 2) / n
            b1 = np.sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
            V3 = (b1 - 1.139547) / np.sqrt(20 / n)
            WPP_statistic = V3**2

        elif type_ == "ST2_WEIBULL":
            x = np.sort(-y)
            s = np.sum((x - np.mean(x)) ** 2) / n
            b1 = np.sum(((x - np.mean(x)) / np.sqrt(s)) ** 3) / n
            b2 = np.sum(((x - np.mean(x)) / np.sqrt(s)) ** 4) / n
            V4 = (b2 - 7.55 * b1 + 3.21) / np.sqrt(219.72 / n)
            WPP_statistic = V4**2

        return WPP_statistic


class OKWeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"OK_{super().code()}"

    # Test statistic of Ozturk and Korukoglu
    @override
    def execute_statistic(self, rvs):
        """
        On the W Test for the Extreme Value Distribution
        Aydin Öztürk
        Biometrika
        Vol. 73, No. 3 (Dec., 1986), pp. 738-740 (3 pages)

        :param rvs:
        :return:
        """

        return super().execute_statistic(rvs, self.code())


class SBWeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"SB_{super().code()}"

    # Test statistic of Shapiro Wilk
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


class RSBWeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"RSB_{super().code()}"

    # Test statistic of Smith and Bain based on probability plot
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


class ST2WeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"ST2_{super().code()}"

    # Smooth test statistic based on the kurtosis
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


class ST1WeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"ST1_{super().code()}"

    # Smooth test statistic based on the skewness
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


class REJGWeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"REJG_{super().code()}"

    # Test statistic of Evans, Johnson and Green based on probability plot
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


class SPPWeibullTestStatistic(WPPWeibullTestStatistic):
    @override
    def code(self):
        return f"SPP_{super().code()}"

    # Test statistic based on stabilized probability plot
    @override
    def execute_statistic(self, rvs):
        return super().execute_statistic(rvs, self.code())


# TODO: fix signatures


class MDTest(AbstractWeibullTestStatistic):
    """title:
    25 Oct 2011 Goodness-of-ﬁt tests for weibull populations onthe basis of records
    Mahdi Doostparast
    Department of Statistics, School of Mathematical Sciences,Ferdowsi University of Mashhad
    P. O. Box 91775-1159, Mashhad, Iran"""

    @override
    def code(self):
        return f"MD_{super().code()}"

    @override
    def execute_statistic(self, rvs):
        rvs_sorted = np.sort(rvs)
        n = len(rvs_sorted)
        emp_cdf = np.arange(1, n + 1) / n

        F_0 = generate_weibull_cdf(rvs_sorted, a=self.l, k=self.k)

        term1 = np.sum(
            [(emp_cdf[i - 1] - 1) ** 2 * (np.log(F_0[i]) - np.log(F_0[i - 1])) for i in range(1, n)]
        )

        term2 = np.sum([(emp_cdf[i - 1] - 1) * (F_0[i] - F_0[i - 1]) for i in range(1, n)])

        MD_statistic = n * (term1 + 2 * term2 + 0.5)

        return MD_statistic


class WatsonTest(CrammerVonMisesWeibullTest):
    """Modified Cramer Statitstic
    https://ru.wikipedia.org/wiki/Критерий_согласия_Ватсона"""

    @override
    def code(self):
        return f"W_{super().code()}"

    @override
    def execute_statistic(self, rvs):
        rvs_sorted = np.sort(rvs)
        cdf_vals = generate_weibull_cdf(rvs_sorted, a=self.l, k=self.k)
        n = len(rvs)

        cramer_statistic = super().execute_statistic(rvs)
        correction_term = n * (np.mean(cdf_vals) - 0.5) ** 2

        watson_statistic = cramer_statistic - correction_term

        return watson_statistic


class LiaoShimokawaTest(AbstractWeibullTestStatistic):
    """Test statistic of Liao-Shimokawa
    https://www.researchgate.net/profile/Min-Liao-8/publication
    /243043005_A_new_goodness-of-fit_test_for_Type-I_extreme-value_and_2-parameter_Weibull_distributions_with_estimated_parameters/
    links/57b77e2708ae14f440ba3487/
    A-new-goodness-of-fit-test-for-Type-I-extreme-value-and-2-parameter-Weibull-distributions-with-estimated-parameters.pdf"""

    @override
    def code(self):
        return f"LS_{super().code()}"

    @override
    def execute_statistic(self, rvs):
        n = len(rvs)
        rvs_sorted = np.sort(rvs)

        empirical_cdf = np.arange(1, n + 1) / n
        theoretical_cdf = generate_weibull_cdf(rvs_sorted, a=self.l, k=self.k)

        epsilon = 1e-10  # Small constant to avoid divide by zero

        deviations = np.maximum(
            empirical_cdf - theoretical_cdf, theoretical_cdf - (np.arange(0, n) / n)
        )
        deviations /= np.sqrt(theoretical_cdf * (1 - theoretical_cdf + epsilon))

        ls_statistic = np.sum(deviations) / np.sqrt(n)
        return ls_statistic


class KullbackLeiblerStatistic(AbstractWeibullTestStatistic):
    @override
    def code(self):
        return f"KL_{super().code()}"

    @override
    def execute_statistic(self, rvs, m=None):
        """
        Test statistic based on Kullback-Leibler information
        """
        n = len(rvs)
        m = n // 2 if m is None else m

        log_rvs = np.log(np.sort(rvs))

        H_mn = np.mean(
            [
                np.log((n / (2 * m)) * (log_rvs[min(n - 1, i + m)] - log_rvs[max(0, i - m)]))
                for i in range(n)
            ]
        )

        term2 = np.mean(log_rvs)

        term3 = np.mean(np.exp(log_rvs))

        KL_statistic = -H_mn - term2 + term3

        return KL_statistic


class LTStatistic(AbstractWeibullTestStatistic):
    """
    Family of the test statistics based on the Laplace transform
    Recommended to use for small data
    """

    def execute_statistic(self, rvs, m=100, a=-5, _type="LT3_WEIBULL"):
        n = len(rvs)

        if _type == "LT2_WEIBULL":
            t_values = np.linspace(-m, -1, num=m) / m

        elif _type == "LT3_WEIBULL":
            t_values = np.linspace(-2.5, 0.49, m)

        else:
            raise ValueError("type must be LT2_WEIBULL / LT3_WEIBULL")

        exp_matrix = np.exp(-np.outer(rvs, t_values))

        col_sums = np.sum(exp_matrix, axis=0)

        lt_sum = np.sum(
            np.exp(-np.exp(a * t_values) + a * t_values) * (gamma(1 - t_values) - col_sums / n) ** 2
        )

        LT_stat = n * lt_sum

        return LT_stat


class LT2Statistic(LTStatistic):
    @override
    def code(self):
        return f"LT2_{super().code()}"

    def execute_statistic(self, rvs, m=100, a=-5):
        return super().execute_statistic(rvs, m, a, self.code())


class LT3Statistic(LTStatistic):
    @override
    def code(self):
        return f"LT3_{super().code()}"

    def execute_statistic(self, rvs, m=100, a=-5):
        return super().execute_statistic(rvs, m, a, self.code())


class CabanaQuirozStatistic(AbstractWeibullTestStatistic):
    # Test statistic of Cabana and Quiroz

    @override
    def code(self):
        return f"CQ*_{super().code()}"

    def execute_statistic(self, rvs):
        s1 = -0.1
        s2 = 0.02
        v1 = 1.59
        v2 = 0.53
        v12 = 0.91

        n = len(rvs)

        e1 = np.exp(-rvs * s1)
        e2 = np.exp(-rvs * s2)

        mean_e1 = np.mean(e1)
        mean_e2 = np.mean(e2)
        vn1 = np.sqrt(n) * (mean_e1 - gamma(1 - s1))
        vn2 = np.sqrt(n) * (mean_e2 - gamma(1 - s2))

        Qn = 1 / (v1 * v2 - v12**2)

        CQ_statistic = Qn * (v2 * vn1**2 - 2 * vn1 * vn2 * v12 + v1 * vn2**2)

        return CQ_statistic


# Example:
# if __name__ == '__main__':

#     tests = [MinToshiyukiWeibullTestStatistic(),MDTest(),
#             LiaoShimokawaTest(), KullbackLeiblerStatistic(),
#             LT2Statistic(), LT3Statistic(), CabanaQuirozStatistic(),
#             WatsonTest(), LillieforsWiebullTest(),
#             Chi2PearsonWiebullTest(), CrammerVonMisesWeibullTest(),
#             ADWeibullTest(), KSWeibullTest(),
#             SBTestStatistic(), ST2TestStatistic(), ST1TestStatistic(),
#             REJGTestStatistic(), RSBTestStatistic(),
#             TSWeibullTestStatistic(), LOSWeibullTestStatistic(),
#             MSFWeibullTestStatistic(), OKWeibullTestStatistic(),
#             SBWeibullTestStatistic(), RSBWeibullTestStatistic(),
#             ST2WeibullTestStatistic(), ST1WeibullTestStatistic(),
#             REJGWeibullTestStatistic(), SPPWeibullTestStatistic()]
#     data = np.random.weibull(1.5, size=100)  # Пример выборки
#     for x in tests:
#         print(x.execute_statistic(data), x.code())
