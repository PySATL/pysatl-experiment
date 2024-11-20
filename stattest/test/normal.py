import math

from stattest.core.distribution import norm
import numpy as np
import scipy.stats as scipy_stats
import pandas as pd

from stattest.test import AbstractTestStatistic
from stattest.persistence.file_store.critical_value_store import CriticalValueFileStore
from stattest.test.common import KSTestStatistic, ADTestStatistic, LillieforsTest


class AbstractNormalityTestStatistic(AbstractTestStatistic):

    def __init__(self, cache=CriticalValueFileStore()):
        self.mean = 0
        self.var = 1
        self.cache = cache

    def calculate_critical_value(self, rvs_size, sl, count=1_000_000):
        keys_cr = [self.code(), str(rvs_size), str(sl)]
        x_cr = self.cache.get_with_level(keys_cr)
        if x_cr is not None:
            return x_cr

        d = self.cache.get_distribution(self.code(), rvs_size)
        if d is not None:
            ecdf = scipy_stats.ecdf(d)
            x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - sl)
            self.cache.put_with_level(keys_cr, x_cr)
            self.cache.flush()
            return x_cr

        result = np.zeros(count)

        for i in range(count):
            x = self.generate(size=rvs_size, mean=self.mean, var=self.var)
            result[i] = self.execute_statistic(x)

        result.sort()

        ecdf = scipy_stats.ecdf(result)
        x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - sl)
        self.cache.put_with_level(keys_cr, x_cr)
        self.cache.put_distribution(self.code(), rvs_size, result)
        self.cache.flush()
        return x_cr

    def test(self, rvs, alpha):
        x_cr = self.calculate_critical_value(len(rvs), alpha)
        statistic = self.execute_statistic(rvs)

        return False if statistic > x_cr else True

    def generate(self, size, mean=0, var=1):
        return norm.generate_norm(size, mean, var)


class KSNormalityTest(KSTestStatistic):

    @staticmethod
    def code():
        return 'KS_NORMALITY'

    def execute_statistic(self, rvs):
        rvs = np.sort(rvs)
        cdf_vals = scipy_stats.norm.cdf(rvs)
        return super().execute_statistic(rvs, cdf_vals)


"""""
class ChiSquareTest(AbstractNormalityTest):

    @staticmethod
    def code():
        return 'CHI2'

    def execute_statistic(self, rvs):
        rvs = np.sort(rvs)

        f_obs = np.asanyarray(rvs)
        f_obs_float = f_obs.astype(np.float64)
        f_exp = pdf_norm(rvs)
        scipy_stats.chi2_contingency()
        terms = (f_obs_float - f_exp) ** 2 / f_exp
        return terms.sum(axis=0)
"""""

# Values from Stephens, M A, "EDF Statistics for Goodness of Fit and
#             Some Comparisons", Journal of the American Statistical
#             Association, Vol. 69, Issue 347, Sept. 1974, pp 730-737
_Avals_norm = np.array([0.576, 0.656, 0.787, 0.918, 1.092])


class ADNormalityTest(ADTestStatistic):

    @staticmethod
    def code():
        return 'AD_NORMALITY'

    def execute_statistic(self, rvs):
        s = np.std(rvs, ddof=1, axis=0)
        y = np.sort(rvs)
        xbar = np.mean(rvs, axis=0)
        w = (y - xbar) / s
        logcdf = scipy_stats.distributions.norm.logcdf(w)
        logsf = scipy_stats.distributions.norm.logsf
        return super().execute_statistic(rvs, log_cdf=logcdf, log_sf=logsf, w=w)


"""
    def calculate_critical_value(self, rvs_size, alpha, count=500_000):
        # sig = [0.15, 0.10, 0.05, 0.025, 0.01].index(alpha)
        # critical = np.around(_Avals_norm / (1.0 + 4.0 / rvs_size - 25.0 / rvs_size / rvs_size), 3)
        # print(critical[sig])
        return super().calculate_critical_value(rvs_size, alpha)
"""


class SWTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'SW'

    def execute_statistic(self, rvs):
        f_obs = np.asanyarray(rvs)
        f_obs_sorted = np.sort(f_obs)
        x_mean = np.mean(f_obs)

        denominator = (f_obs - x_mean) ** 2
        denominator = denominator.sum()

        a = self.ordered_statistic(len(f_obs))
        terms = a * f_obs_sorted
        return (terms.sum() ** 2) / denominator

    @staticmethod
    def ordered_statistic(n):
        if n == 3:
            sqrt = np.sqrt(0.5)
            return np.array([sqrt, 0, -sqrt])

        m = np.array([scipy_stats.norm.ppf((i - 3 / 8) / (n + 0.25)) for i in range(1, n + 1)])

        m2 = m ** 2
        term = np.sqrt(m2.sum())
        cn = m[-1] / term
        cn1 = m[-2] / term

        p1 = [-2.706056, 4.434685, -2.071190, -0.147981, 0.221157, cn]
        u = 1 / np.sqrt(n)

        wn = np.polyval(p1, u)
        # wn = np.array([p1[0] * (u ** 5), p1[1] * (u ** 4), p1[2] * (u ** 3), p1[3] * (u ** 2), p1[4] * (u ** 1), p1[5]]).sum()
        w1 = -wn

        if n == 4 or n == 5:
            phi = (m2.sum() - 2 * m[-1] ** 2) / (1 - 2 * wn ** 2)
            phi_sqrt = np.sqrt(phi)
            result = np.array([m[k] / phi_sqrt for k in range(1, n - 1)])
            return np.concatenate([[w1], result, [wn]])

        p2 = [-3.582633, 5.682633, -1.752461, -0.293762, 0.042981, cn1]

        if n > 5:
            wn1 = np.polyval(p2, u)
            w2 = -wn1
            phi = (m2.sum() - 2 * m[-1] ** 2 - 2 * m[-2] ** 2) / (1 - 2 * wn ** 2 - 2 * wn1 ** 2)
            phi_sqrt = np.sqrt(phi)
            result = np.array([m[k] / phi_sqrt for k in range(2, n - 2)])
            return np.concatenate([[w1, w2], result, [wn1, wn]])


class CVMTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'CVM'

    def execute_statistic(self, rvs):
        n = len(rvs)

        rvs = np.sort(rvs)
        vals = np.sort(np.asarray(rvs))
        cdf_vals = scipy_stats.norm.cdf(vals)

        u = (2 * np.arange(1, n + 1) - 1) / (2 * n)
        CM = 1 / (12 * n) + np.sum((u - cdf_vals) ** 2)
        return CM


class LillieforsNormalityTest(LillieforsTest):

    @staticmethod
    def code():
        return 'LILLIE_NORMALITY'

    def execute_statistic(self, rvs):
        x = np.asarray(rvs)
        z = (x - x.mean()) / x.std(ddof=1)
        cdf_vals = scipy_stats.norm.cdf(np.sort(z))
        return super().execute_statistic(rvs, cdf_vals)


# TODO: What is it
"""
class DATest(AbstractNormalityTest):

    @staticmethod
    def code():
        return 'DA'

    def execute_statistic(self, rvs):
        x = np.asanyarray(rvs)
        y = np.sort(x)
        n = len(x)

        x_mean = np.mean(x)
        m2 = np.sum((x - x_mean) ** 2) / n
        i = np.arange(1, n + 1)
        c = (n + 1) / 2
        terms = (i - c) * y
        stat = terms.sum() / (n ** 2 * np.sqrt(m2))
        return stat
"""


class JBTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'JB'

    def execute_statistic(self, rvs):
        x = np.asarray(rvs)
        x = x.ravel()
        axis = 0

        n = x.shape[axis]
        if n == 0:
            raise ValueError('At least one observation is required.')

        mu = x.mean(axis=axis, keepdims=True)
        diffx = x - mu
        s = scipy_stats.skew(diffx, axis=axis, _no_deco=True)
        k = scipy_stats.kurtosis(diffx, axis=axis, _no_deco=True)
        statistic = n / 6 * (s ** 2 + k ** 2 / 4)
        return statistic


class SkewTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'SKEW'

    def execute_statistic(self, rvs):
        x = np.asanyarray(rvs)
        y = np.sort(x)

        return self.skew_test(y)

    @staticmethod
    def skew_test(a):
        n = len(a)
        if n < 8:
            raise ValueError(
                "skew test is not valid with less than 8 samples; %i samples"
                " were given." % int(n))
        b2 = scipy_stats.skew(a, axis=0)
        y = b2 * math.sqrt(((n + 1) * (n + 3)) / (6.0 * (n - 2)))
        beta2 = (3.0 * (n ** 2 + 27 * n - 70) * (n + 1) * (n + 3) /
                 ((n - 2.0) * (n + 5) * (n + 7) * (n + 9)))
        W2 = -1 + math.sqrt(2 * (beta2 - 1))
        delta = 1 / math.sqrt(0.5 * math.log(W2))
        alpha = math.sqrt(2.0 / (W2 - 1))
        y = np.where(y == 0, 1, y)
        Z = delta * np.log(y / alpha + np.sqrt((y / alpha) ** 2 + 1))

        return Z


class KurtosisTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'KURTOSIS'

    def execute_statistic(self, rvs):
        x = np.asanyarray(rvs)
        y = np.sort(x)

        return self.kurtosis_test(y)

    @staticmethod
    def kurtosis_test(a):
        n = len(a)
        if n < 5:
            raise ValueError(
                "kurtosistest requires at least 5 observations; %i observations"
                " were given." % int(n))
        # if n < 20:
        #    warnings.warn("kurtosistest only valid for n>=20 ... continuing "
        #                  "anyway, n=%i" % int(n),
        #                  stacklevel=2)
        b2 = scipy_stats.kurtosis(a, axis=0, fisher=False)

        E = 3.0 * (n - 1) / (n + 1)
        varb2 = 24.0 * n * (n - 2) * (n - 3) / ((n + 1) * (n + 1.) * (n + 3) * (n + 5))  # [1]_ Eq. 1
        x = (b2 - E) / np.sqrt(varb2)  # [1]_ Eq. 4
        # [1]_ Eq. 2:
        sqrtbeta1 = 6.0 * (n * n - 5 * n + 2) / ((n + 7) * (n + 9)) * np.sqrt((6.0 * (n + 3) * (n + 5)) /
                                                                              (n * (n - 2) * (n - 3)))
        # [1]_ Eq. 3:
        A = 6.0 + 8.0 / sqrtbeta1 * (2.0 / sqrtbeta1 + np.sqrt(1 + 4.0 / (sqrtbeta1 ** 2)))
        term1 = 1 - 2 / (9.0 * A)
        denom = 1 + x * np.sqrt(2 / (A - 4.0))
        term2 = np.sign(denom) * np.where(denom == 0.0, np.nan,
                                          np.power((1 - 2.0 / A) / np.abs(denom), 1 / 3.0))
        # if np.any(denom == 0):
        #    msg = ("Test statistic not defined in some cases due to division by "
        #           "zero. Return nan in that case...")
        #    warnings.warn(msg, RuntimeWarning, stacklevel=2)

        Z = (term1 - term2) / np.sqrt(2 / (9.0 * A))  # [1]_ Eq. 5

        return Z


class DAPTest(SkewTest, KurtosisTest):

    @staticmethod
    def code():
        return 'DAP'

    def execute_statistic(self, rvs):
        x = np.asanyarray(rvs)
        y = np.sort(x)

        s = self.skew_test(y)
        k = self.kurtosis_test(y)
        k2 = s * s + k * k
        return k2


# https://github.com/puzzle-in-a-mug/normtest
class FilliTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'Filli'

    def execute_statistic(self, rvs):
        uniform_order = self._uniform_order_medians(len(rvs))
        zi = self._normal_order_medians(uniform_order)
        x_data = np.sort(rvs)
        statistic = self._statistic(x_data=x_data, zi=zi)
        return statistic

    @staticmethod
    def _uniform_order_medians(sample_size):
        i = np.arange(1, sample_size + 1)
        mi = (i - 0.3175) / (sample_size + 0.365)
        mi[0] = 1 - 0.5 ** (1 / sample_size)
        mi[-1] = 0.5 ** (1 / sample_size)

        return mi

    @staticmethod
    def _normal_order_medians(mi):
        normal_ordered = scipy_stats.norm.ppf(mi)
        return normal_ordered

    @staticmethod
    def _statistic(x_data, zi):
        correl = scipy_stats.pearsonr(x_data, zi)[0]
        return correl


# https://github.com/puzzle-in-a-mug/normtest
class LooneyGulledgeTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'LG'

    def execute_statistic(self, rvs):
        # ordering
        x_data = np.sort(rvs)

        # zi
        zi = self._normal_order_statistic(
            x_data=x_data,
            weighted=False,  # TODO: False or True
        )

        # calculating the stats
        statistic = self._statistic(x_data=x_data, zi=zi)
        return statistic

    @staticmethod
    def _normal_order_statistic(x_data, weighted=False):
        # ordering
        x_data = np.sort(x_data)
        if weighted:
            df = pd.DataFrame({"x_data": x_data})
            # getting mi values
            df["Rank"] = np.arange(1, df.shape[0] + 1)
            df["Ui"] = LooneyGulledgeTest._order_statistic(
                sample_size=x_data.size,
            )
            df["Mi"] = df.groupby(["x_data"])["Ui"].transform("mean")
            normal_ordered = scipy_stats.norm.ppf(df["Mi"])
        else:
            ordered = LooneyGulledgeTest._order_statistic(
                sample_size=x_data.size,
            )
            normal_ordered = scipy_stats.norm.ppf(ordered)

        return normal_ordered

    @staticmethod
    def _statistic(x_data, zi):
        correl = scipy_stats.pearsonr(zi, x_data)[0]
        return correl

    @staticmethod
    def _order_statistic(sample_size):
        i = np.arange(1, sample_size + 1)
        cte_alpha = 3 / 8
        return (i - cte_alpha) / (sample_size - 2 * cte_alpha + 1)


# https://github.com/puzzle-in-a-mug/normtest
class RyanJoinerTest(AbstractNormalityTestStatistic):
    def __init__(self, weighted=False, cte_alpha="3/8"):
        super().__init__()
        self.weighted = weighted
        self.cte_alpha = cte_alpha

    @staticmethod
    def code():
        return 'RJ'

    def execute_statistic(self, rvs):
        # ordering
        x_data = np.sort(rvs)

        # zi
        zi = self._normal_order_statistic(
            x_data=x_data,
            weighted=self.weighted,
            cte_alpha=self.cte_alpha,
        )

        # calculating the stats
        statistic = self._statistic(x_data=x_data, zi=zi)
        return statistic

    def _normal_order_statistic(self, x_data, weighted=False, cte_alpha="3/8"):
        # ordering
        x_data = np.sort(x_data)
        if weighted:
            df = pd.DataFrame({"x_data": x_data})
            # getting mi values
            df["Rank"] = np.arange(1, df.shape[0] + 1)
            df["Ui"] = self._order_statistic(
                sample_size=x_data.size,
                cte_alpha=cte_alpha,
            )
            df["Mi"] = df.groupby(["x_data"])["Ui"].transform("mean")
            normal_ordered = scipy_stats.norm.ppf(df["Mi"])
        else:
            ordered = self._order_statistic(
                sample_size=x_data.size,
                cte_alpha=cte_alpha,
            )
            normal_ordered = scipy_stats.norm.ppf(ordered)

        return normal_ordered

    @staticmethod
    def _statistic(x_data, zi):
        return scipy_stats.pearsonr(zi, x_data)[0]

    @staticmethod
    def _order_statistic(sample_size, cte_alpha="3/8"):
        i = np.arange(1, sample_size + 1)
        if cte_alpha == "1/2":
            cte_alpha = 0.5
        elif cte_alpha == "0":
            cte_alpha = 0
        else:
            cte_alpha = 3 / 8

        return (i - cte_alpha) / (sample_size - 2 * cte_alpha + 1)


class SFTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'SF'

    def execute_statistic(self, rvs):
        n = len(rvs)
        rvs = np.sort(rvs)

        x_mean = np.mean(rvs)
        alpha = 0.375
        terms = (np.arange(1, n + 1) - alpha) / (n - 2 * alpha + 1)
        e = -scipy_stats.norm.ppf(terms)

        w = np.sum(e * rvs) ** 2 / (np.sum((rvs - x_mean) ** 2) * np.sum(e ** 2))
        return w


# https://habr.com/ru/articles/685582/
class EPTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'EP'

    def execute_statistic(self, rvs):
        n = len(rvs)
        X = np.sort(rvs)
        X_mean = np.mean(X)
        m2 = np.var(X, ddof=0)

        A = np.sqrt(2) * np.sum([np.exp(-(X[i] - X_mean) ** 2 / (4 * m2)) for i in range(n)])
        B = 0
        for k in range(1, n):
            B = B + np.sum(np.exp(-(X[:k] - X[k]) ** 2 / (2 * m2)))
        B = 2 / n * B
        t = 1 + n / np.sqrt(3) + B - A
        return t


class Hosking2Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'HOSKING2'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:

            xtmp = [0] * n
            l21, l31, l41 = 0.0, 0.0, 0.0
            mutau41, vtau31, vtau41 = 0.0, 0.0, 0.0
            for i in range(n):
                xtmp[i] = rvs[i]
            xtmp = np.sort(xtmp)
            for i in range(2, n):
                l21 += xtmp[i - 1] * self.pstarmod1(2, n, i)
                l31 += xtmp[i - 1] * self.pstarmod1(3, n, i)
                l41 += xtmp[i - 1] * self.pstarmod1(4, n, i)
            l21 = l21 / (2.0 * math.comb(n, 4))
            l31 = l31 / (3.0 * math.comb(n, 5))
            l41 = l41 / (4.0 * math.comb(n, 6))
            tau31 = l31 / l21
            tau41 = l41 / l21
            if 1 <= n <= 25:
                mutau41 = 0.067077
                vtau31 = 0.0081391
                vtau41 = 0.0042752
            if 25 < n <= 50:
                mutau41 = 0.064456
                vtau31 = 0.0034657
                vtau41 = 0.0015699
            if 50 < n:
                mutau41 = 0.063424
                vtau31 = 0.0016064
                vtau41 = 0.00068100
            return pow(tau31, 2.0) / vtau31 + pow(tau41 - mutau41, 2.0) / vtau41

        return 0

    def pstarmod1(self, r, n, i):
        res = 0.0
        for k in range(r):
            res = res + (-1.0) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 1 - 1 - k) * math.comb(n - i, 1 + k)

        return res


class Hosking1Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'HOSKING1'

    def execute_statistic(self, rvs):
        return self.stat10(rvs)

    def stat10(self, x):
        n = len(x)

        if n > 3:
            xtmp = x[:n].copy()
            xtmp.sort()
            tmp1 = n * (n - 1)
            tmp2 = tmp1 * (n - 2)
            tmp3 = tmp2 * (n - 3)
            b0 = sum(xtmp[:3]) + sum(xtmp[3:])
            b1 = 1.0 * xtmp[1] + 2.0 * xtmp[2] + sum(i * xtmp[i] for i in range(3, n))
            b2 = 2.0 * xtmp[2] + sum((i * (i - 1)) * xtmp[i] for i in range(3, n))
            b3 = sum((i * (i - 1) * (i - 2)) * xtmp[i] for i in range(3, n))
            b0 /= n
            b1 /= tmp1
            b2 /= tmp2
            b3 /= tmp3
            l2 = 2.0 * b1 - b0
            l3 = 6.0 * b2 - 6.0 * b1 + b0
            l4 = 20.0 * b3 - 30.0 * b2 + 12.0 * b1 - b0
            tau3 = l3 / l2
            tau4 = l4 / l2

            if 1 <= n <= 25:
                mutau4 = 0.12383
                vtau3 = 0.0088038
                vtau4 = 0.0049295
            elif 25 < n <= 50:
                mutau4 = 0.12321
                vtau3 = 0.0040493
                vtau4 = 0.0020802
            else:
                mutau4 = 0.12291
                vtau3 = 0.0019434
                vtau4 = 0.00095785

            statTLmom = (tau3 ** 2) / vtau3 + (tau4 - mutau4) ** 2 / vtau4
            return statTLmom


class Hosking3Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'HOSKING3'

    def execute_statistic(self, rvs):
        return self.stat12(rvs)

    def stat12(self, x):
        n = len(x)

        if n > 3:
            xtmp = x[:n]
            xtmp.sort()
            l22 = 0.0
            l32 = 0.0
            l42 = 0.0
            for i in range(2, n):
                l22 += xtmp[i - 1] * self.pstarmod2(2, n, i)
                l32 += xtmp[i - 1] * self.pstarmod2(3, n, i)
                l42 += xtmp[i - 1] * self.pstarmod2(4, n, i)
            l22 /= 2.0 * math.comb(n, 6)
            l32 /= 3.0 * math.comb(n, 7)
            l42 /= 4.0 * math.comb(n, 8)
            tau32 = l32 / l22
            tau42 = l42 / l22

            if 1 <= n <= 25:
                mutau42 = 0.044174
                vtau32 = 0.0086570
                vtau42 = 0.0042066
            elif 25 < n <= 50:
                mutau42 = 0.040389
                vtau32 = 0.0033818
                vtau42 = 0.0013301
            else:
                mutau42 = 0.039030
                vtau32 = 0.0015120
                vtau42 = 0.00054207

            statTLmom2 = (tau32 ** 2) / vtau32 + (tau42 - mutau42) ** 2 / vtau42
            return statTLmom2

    def pstarmod2(self, r, n, i):
        res = 0.0
        for k in range(r):
            res += (-1) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 2 - 1 - k) * math.comb(n - i, 2 + k)
        return res


class Hosking4Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'HOSKING4'

    def execute_statistic(self, rvs):
        return self.stat13(rvs)

    def stat13(self, x):
        n = len(x)

        if n > 3:
            xtmp = x[:n]
            xtmp.sort()
            l23 = 0.0
            l33 = 0.0
            l43 = 0.0
            for i in range(2, n):
                l23 += xtmp[i - 1] * self.pstarmod3(2, n, i)
                l33 += xtmp[i - 1] * self.pstarmod3(3, n, i)
                l43 += xtmp[i - 1] * self.pstarmod3(4, n, i)
            l23 /= 2.0 * math.comb(n, 8)
            l33 /= 3.0 * math.comb(n, 9)
            l43 /= 4.0 * math.comb(n, 10)
            tau33 = l33 / l23
            tau43 = l43 / l23

            if 1 <= n <= 25:
                mutau43 = 0.033180
                vtau33 = 0.0095765
                vtau43 = 0.0044609
            elif 25 < n <= 50:
                mutau43 = 0.028224
                vtau33 = 0.0033813
                vtau43 = 0.0011823
            else:
                mutau43 = 0.026645
                vtau33 = 0.0014547
                vtau43 = 0.00045107

            statTLmom3 = (tau33 ** 2) / vtau33 + (tau43 - mutau43) ** 2 / vtau43
            return statTLmom3

    def pstarmod3(self, r, n, i):
        res = 0.0
        for k in range(r):
            res += (-1) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 3 - 1 - k) * math.comb(n - i, 3 + k)
        return res


class ZhangWuCTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'ZWC'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            Phiz = np.zeros(n)
            meanX = np.mean(rvs)
            varX = np.var(rvs, ddof=1)
            sdX = np.sqrt(varX)
            for i in range(n):
                Phiz[i] = scipy_stats.norm.cdf((rvs[i] - meanX) / sdX)
            Phiz.sort()
            statZC = 0.0
            for i in range(1, n + 1):
                statZC += np.log((1.0 / Phiz[i - 1] - 1.0) / ((n - 0.5) / (i - 0.75) - 1.0)) ** 2
            return statZC


class ZhangWuATest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'ZWA'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            Phiz = np.zeros(n)
            meanX = np.mean(rvs)
            varX = np.var(rvs)
            sdX = np.sqrt(varX)
            for i in range(n):
                Phiz[i] = scipy_stats.norm.cdf((rvs[i] - meanX) / sdX)
            Phiz.sort()
            statZA = 0.0
            for i in range(1, n + 1):
                statZA += np.log(Phiz[i - 1]) / ((n - i) + 0.5) + np.log(1.0 - Phiz[i - 1]) / ((i - 0.5))
            statZA = -statZA
            statZA = 10.0 * statZA - 32.0
            return statZA


class GlenLeemisBarrTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'GLB'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            Phiz = np.zeros(n)
            meanX = np.mean(rvs)
            varX = np.var(rvs, ddof=1)
            sdX = np.sqrt(varX)
            for i in range(n):
                Phiz[i] = scipy_stats.norm.cdf((rvs[i] - meanX) / sdX)
            Phiz.sort()
            for i in range(1, n + 1):
                Phiz[i - 1] = scipy_stats.beta.cdf(Phiz[i - 1], i, n - i + 1)
            Phiz.sort()
            statPS = 0
            for i in range(1, n + 1):
                statPS += (2 * n + 1 - 2 * i) * np.log(Phiz[i - 1]) + (2 * i - 1) * np.log(1 - Phiz[i - 1])
            return -n - statPS / n


class DoornikHansenTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'DH'

    def execute_statistic(self, rvs):
        return self.doornik_hansen(rvs)

    def doornik_hansen(self, x):
        n = len(x)
        m2 = scipy_stats.moment(x, moment=2)
        m3 = scipy_stats.moment(x, moment=3)
        m4 = scipy_stats.moment(x, moment=4)

        b1 = m3 / (m2 ** 1.5)
        b2 = m4 / (m2 ** 2)

        z1 = self.skewness_to_z1(b1, n)
        z2 = self.kurtosis_to_z2(b1, b2, n)

        stat = z1 ** 2 + z2 ** 2
        return stat

    def skewness_to_z1(self, skew, n):
        b = 3 * ((n ** 2) + 27 * n - 70) * (n + 1) * (n + 3) / ((n - 2) * (n + 5) * (n + 7) * (n + 9))
        w2 = -1 + math.sqrt(2 * (b - 1))
        d = 1 / math.sqrt(math.log(math.sqrt(w2)))
        y = skew * math.sqrt((n + 1) * (n + 3) / (6 * (n - 2)))
        a = math.sqrt(2 / (w2 - 1))
        z = d * math.log((y / a) + math.sqrt((y / a) ** 2 + 1))
        return z

    def kurtosis_to_z2(self, skew, kurt, n):
        n2 = n ** 2
        n3 = n ** 3
        p1 = n2 + 15 * n - 4
        p2 = n2 + 27 * n - 70
        p3 = n2 + 2 * n - 5
        p4 = n3 + 37 * n2 + 11 * n - 313
        d = (n - 3) * (n + 1) * p1
        a = (n - 2) * (n + 5) * (n + 7) * p2 / (6 * d)
        c = (n - 7) * (n + 5) * (n + 7) * p3 / (6 * d)
        k = (n + 5) * (n + 7) * p4 / (12 * d)
        alpha = a + skew ** 2 * c
        q = 2 * (kurt - 1 - skew ** 2) * k
        z = (0.5 * q / alpha) ** (1 / 3) - 1 + 1 / (9 * alpha)
        z *= math.sqrt(9 * alpha)
        return z


class RobustJarqueBeraTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'RJB'

    def execute_statistic(self, rvs):
        y = np.sort(rvs)
        n = len(rvs)
        M = np.median(y)
        c = np.sqrt(math.pi / 2)
        J = (c / n) * np.sum(np.abs(rvs - M))
        m_3 = scipy_stats.moment(y, moment=3)
        m_4 = scipy_stats.moment(y, moment=4)
        RJB = (n / 6) * (m_3 / J ** 3) ** 2 + (n / 64) * (m_4 / J ** 4 - 3) ** 2
        return RJB


class BontempsMeddahi1Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'BM1'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            z = [0.0] * n
            varX = 0.0
            meanX = 0.0
            tmp3 = 0.0
            tmp4 = 0.0

            for i in range(n):
                meanX += rvs[i]
            meanX /= n

            for i in range(n):
                varX += rvs[i] ** 2
            varX = (n * (varX / n - meanX ** 2)) / (n - 1)
            sdX = math.sqrt(varX)

            for i in range(n):
                z[i] = (rvs[i] - meanX) / sdX

            for i in range(n):
                tmp3 += (z[i] ** 3 - 3 * z[i]) / math.sqrt(6)
                tmp4 += (z[i] ** 4 - 6 * z[i] ** 2 + 3) / (2 * math.sqrt(6))

            statBM34 = (tmp3 ** 2 + tmp4 ** 2) / n
            return statBM34


class BontempsMeddahi2Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'BM2'

    def execute_statistic(self, rvs):
        return self.stat15(rvs)

    def stat15(self, x):
        n = len(x)

        if n > 3:
            z = np.zeros(n)
            meanX = np.mean(x)
            varX = np.var(x, ddof=1)
            sdX = np.sqrt(varX)
            for i in range(n):
                z[i] = (x[i] - meanX) / sdX
            tmp3 = np.sum((z ** 3 - 3 * z) / np.sqrt(6))
            tmp4 = np.sum((z ** 4 - 6 * z ** 2 + 3) / (2 * np.sqrt(6)))
            tmp5 = np.sum((z ** 5 - 10 * z ** 3 + 15 * z) / (2 * np.sqrt(30)))
            tmp6 = np.sum((z ** 6 - 15 * z ** 4 + 45 * z ** 2 - 15) / (12 * np.sqrt(5)))
            statBM36 = (tmp3 ** 2 + tmp4 ** 2 + tmp5 ** 2 + tmp6 ** 2) / n
            return statBM36


class BonettSeierTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'BS'

    def execute_statistic(self, rvs):
        return self.stat17(rvs)

    def stat17(self, x):
        n = len(x)

        if n > 3:
            m2 = 0.0
            meanX = 0.0
            term = 0.0

            for i in range(n):
                meanX += x[i]

            meanX = meanX / float(n)

            for i in range(n):
                m2 += (x[i] - meanX) ** 2
                term += abs(x[i] - meanX)

            m2 = m2 / float(n)
            term = term / float(n)
            omega = 13.29 * (math.log(math.sqrt(m2)) - math.log(term))
            statTw = math.sqrt(float(n + 2)) * (omega - 3.0) / 3.54
            return statTw


class MartinezIglewiczTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'MI'

    def execute_statistic(self, rvs):
        return self.stat32(rvs)

    def stat32(self, x):
        n = len(x)

        if n > 3:
            xtmp = np.copy(x)
            xtmp.sort()
            if n % 2 == 0:
                M = (xtmp[n // 2] + xtmp[n // 2 - 1]) / 2.0
            else:
                M = xtmp[n // 2]

            aux1 = x - M
            xtmp = np.abs(aux1)
            xtmp.sort()
            if n % 2 == 0:
                A = (xtmp[n // 2] + xtmp[n // 2 - 1]) / 2.0
            else:
                A = xtmp[n // 2]
            A = 9.0 * A

            z = aux1 / A
            term1 = np.sum(aux1 ** 2 * (1 - z ** 2) ** 4)
            term2 = np.sum((1 - z ** 2) * (1 - 5 * z ** 2))
            term3 = np.sum(aux1 ** 2)

            Sb2 = (n * term1) / term2 ** 2
            statIn = (term3 / (n - 1)) / Sb2
            return statIn


class CabanaCabana1Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'CC1'

    def execute_statistic(self, rvs):
        return self.stat19(rvs)

    def stat19(self, x):
        n = len(x)

        if n > 3:
            zdata = (x - np.mean(x)) / np.std(x, ddof=1)
            meanH3 = np.sum(zdata ** 3 - 3 * zdata) / (np.sqrt(6) * np.sqrt(n))
            meanH4 = np.sum(zdata ** 4 - 6 * zdata ** 2 + 3) / (2 * np.sqrt(6) * np.sqrt(n))
            meanH5 = np.sum(zdata ** 5 - 10 * zdata ** 3 + 15 * zdata) / (2 * np.sqrt(30) * np.sqrt(n))
            meanH6 = np.sum(zdata ** 6 - 15 * zdata ** 4 + 45 * zdata ** 2 - 15) / (12 * np.sqrt(5) * np.sqrt(n))
            meanH7 = np.sum(zdata ** 7 - 21 * zdata ** 5 + 105 * zdata ** 3 - 105 * zdata) / (
                    12 * np.sqrt(35) * np.sqrt(n))
            meanH8 = np.sum(zdata ** 8 - 28 * zdata ** 6 + 210 * zdata ** 4 - 420 * zdata ** 2 + 105) / (
                    24 * np.sqrt(70) * np.sqrt(n))
            vectoraux1 = meanH4 + meanH5 * zdata / np.sqrt(2) + meanH6 * (zdata ** 2 - 1) / np.sqrt(6) + meanH7 * (
                    zdata ** 3 - 3 * zdata) / (2 * np.sqrt(6)) + meanH8 * (zdata ** 4 - 6 * zdata ** 2 + 3) / (
                                 2 * np.sqrt(30))
            statTSl = np.max(np.abs(scipy_stats.norm.cdf(zdata) * meanH3 - scipy_stats.norm.pdf(zdata) * vectoraux1))
            return statTSl


class CabanaCabana2Test(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'CC2'

    def execute_statistic(self, rvs):
        return self.stat20(rvs)

    def stat20(self, x):
        n = len(x)

        if n > 3:
            # TODO: Move variance calculation
            varX = n * np.var(x) / (n - 1)
            sdX = np.sqrt(varX)
            z = (x - np.mean(x)) / sdX
            H0 = np.zeros(n)
            H1 = np.zeros(n)
            H2 = np.zeros(n)
            H3 = np.zeros(n)
            H4 = np.zeros(n)
            H5 = np.zeros(n)
            H6 = np.zeros(n)
            H7 = np.zeros(n)
            H8 = np.zeros(n)

            H3tilde = 0
            H4tilde = 0
            H5tilde = 0
            H6tilde = 0
            H7tilde = 0
            H8tilde = 0

            for i in range(n):
                H0[i] = 1
                H1[i] = z[i]
                H2[i] = (math.pow(z[i], 2.0) - 1.0) / np.sqrt(2.0)
                H3[i] = (math.pow(z[i], 3.0) - 3.0 * z[i]) / np.sqrt(6.0)
                H4[i] = (math.pow(z[i], 4.0) - 6.0 * math.pow(z[i], 2.0) + 3.0) / (2.0 * np.sqrt(6.0))
                H5[i] = (math.pow(z[i], 5.0) - 10.0 * math.pow(z[i], 3.0) + 15.0 * z[i]) / (2.0 * np.sqrt(30.0))
                H6[i] = (math.pow(z[i], 6.0) - 15.0 * math.pow(z[i], 4.0) + 45.0 * math.pow(z[i], 2.0) - 15.0) / (
                        12.0 * np.sqrt(5.0))
                H7[i] = (math.pow(z[i], 7.0) - 21.0 * math.pow(z[i], 5.0) + 105.0 * math.pow(z[i], 3.0) - 105.0 * z[
                    i]) / (
                                12.0 * np.sqrt(35.0))
                H8[i] = (math.pow(z[i], 8.0) - 28.0 * math.pow(z[i], 6.0) + 210.0 * math.pow(z[i],
                                                                                             4.0) - 420.0 * math.pow(
                    z[i],
                    2.0) + 105.0) / (
                                24.0 * np.sqrt(70.0))

                H3tilde = H3tilde + H3[i]
                H4tilde = H4tilde + H4[i]
                H5tilde = H5tilde + H5[i]
                H6tilde = H6tilde + H6[i]
                H7tilde = H7tilde + H7[i]
                H8tilde = H8tilde + H8[i]

            H3tilde = H3tilde / np.sqrt(n)
            H4tilde = H4tilde / np.sqrt(n)
            H5tilde = H5tilde / np.sqrt(n)
            H6tilde = H6tilde / np.sqrt(n)
            H7tilde = H7tilde / np.sqrt(n)
            H8tilde = H8tilde / np.sqrt(n)

            vectoraux2 = (np.sqrt(2) * H0 + H2) * H5tilde + (np.sqrt(3 / 2) * H1 + H3) * H6tilde + (
                    np.sqrt(4 / 3) * H2 + H4) * H7tilde + (np.sqrt(5 / 4) * H3 + H5) * H8tilde + (
                                 np.sqrt(5 / 4) * H3 + H5) * H8tilde
            statTKl = np.max(np.abs(-scipy_stats.norm.pdf(z) * H3tilde + (
                    scipy_stats.norm.cdf(z) - z * scipy_stats.norm.pdf(z)) * H4tilde - scipy_stats.norm.pdf(
                z) * vectoraux2))
            return statTKl


class ChenShapiroTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'CS'

    def execute_statistic(self, rvs):
        return self.stat26(rvs)

    def stat26(self, x):
        n = len(x)

        if n > 3:
            xs = np.sort(x)
            meanX = np.mean(x)
            varX = np.var(x, ddof=1)
            M = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 0.25) - 0.375 / (n + 0.25))
            statCS = np.sum((xs[1:] - xs[:-1]) / (M[1:] - M[:-1])) / ((n - 1) * np.sqrt(varX))
            statCS = np.sqrt(n) * (1.0 - statCS)
            return statCS


class ZhangQTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'ZQ'

    def execute_statistic(self, rvs):
        return self.stat27(rvs)

    def stat27(self, x):
        n = len(x)

        if n > 3:
            u = scipy_stats.norm.ppf((np.arange(1, n + 1) - 0.375) / (n + 0.25))
            xs = np.sort(x)
            a = np.zeros(n)
            b = np.zeros(n)
            term = 0.0
            for i in range(2, n + 1):
                a[i - 1] = 1.0 / ((n - 1) * (u[i - 1] - u[0]))
                term += a[i - 1]
            a[0] = -term
            b[0] = 1.0 / ((n - 4) * (u[0] - u[4]))
            b[n - 1] = -b[0]
            b[1] = 1.0 / ((n - 4) * (u[1] - u[5]))
            b[n - 2] = -b[1]
            b[2] = 1.0 / ((n - 4) * (u[2] - u[6]))
            b[n - 3] = -b[2]
            b[3] = 1.0 / ((n - 4) * (u[3] - u[7]))
            b[n - 4] = -b[3]
            for i in range(5, n - 3):
                b[i - 1] = (1.0 / (u[i - 1] - u[i + 3]) - 1.0 / (u[i - 5] - u[i - 1])) / (n - 4)
            q1 = np.dot(a, xs)
            q2 = np.dot(b, xs)
            statQ = np.log(q1 / q2)
            return statQ


class CoinTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'COIN'

    def execute_statistic(self, rvs):
        return self.stat30(rvs)

    def stat30(self, x):
        n = len(x)

        if n > 3:
            z = [0] * n
            M = [n // 2]
            sp = [0] * M[0]
            a = [0] * n
            varX = 0.0
            meanX = 0.0
            term1 = 0.0
            term2 = 0.0
            term3 = 0.0
            term4 = 0.0
            term6 = 0.0

            for i in range(n):
                meanX += x[i]
            meanX /= n

            for i in range(n):
                varX += x[i] ** 2
            varX = (n * (varX / n - meanX ** 2)) / (n - 1)
            sdX = math.sqrt(varX)

            for i in range(n):
                z[i] = (x[i] - meanX) / sdX

            z.sort()
            self.nscor2(sp, n, M)

            if n % 2 == 0:
                for i in range(n // 2):
                    a[i] = -sp[i]
                for i in range(n // 2, n):
                    a[i] = sp[n - i - 1]
            else:
                for i in range(n // 2):
                    a[i] = -sp[i]
                a[n // 2] = 0.0
                for i in range(n // 2 + 1, n):
                    a[i] = sp[n - i - 1]

            for i in range(n):
                term1 += a[i] ** 4
                term2 += a[i] * z[i]
                term3 += a[i] ** 2
                term4 += a[i] ** 3 * z[i]
                term6 += a[i] ** 6

            statbeta32 = ((term1 * term2 - term3 * term4) / (term1 * term1 - term3 * term6)) ** 2
            return statbeta32

    def correc(self, i, n):
        c1 = [9.5, 28.7, 1.9, 0., -7., -6.2, -1.6]
        c2 = [-6195., -9569., -6728., -17614., -8278., -3570., 1075.]
        c3 = [93380., 175160., 410400., 2157600., 2.376e6, 2.065e6, 2.065e6]
        mic = 1e-6
        c14 = 1.9e-5

        if i * n == 4:
            return c14
        if i < 1 or i > 7:
            return 0
        if i != 4 and n > 20:
            return 0
        if i == 4 and n > 40:
            return 0

        an = 1. / (n * n)
        i -= 1
        return (c1[i] + an * (c2[i] + an * c3[i])) * mic

    def nscor2(self, s, n, n2):
        eps = [.419885, .450536, .456936, .468488]
        dl1 = [.112063, .12177, .239299, .215159]
        dl2 = [.080122, .111348, -.211867, -.115049]
        gam = [.474798, .469051, .208597, .259784]
        lam = [.282765, .304856, .407708, .414093]
        bb = -.283833
        d = -.106136
        b1 = .5641896

        if n2[0] > n / 2:
            raise ValueError("n2>n")
        if n <= 1:
            raise ValueError("n<=1")
        if n > 2000:
            print("Values may be inaccurate because of the size of N")

        s[0] = b1
        if n == 2:
            return

        an = n
        k = 3
        if n2[0] < k:
            k = n2[0]

        for i in range(k):
            ai = i + 1
            e1 = (ai - eps[i]) / (an + gam[i])
            e2 = e1 ** lam[i]
            s[i] = e1 + e2 * (dl1[i] + e2 * dl2[i]) / an - self.correc(i + 1, n)

        if n2[0] > k:
            for i in range(3, n2[0]):
                ai = i + 1
                e1 = (ai - eps[3]) / (an + gam[3])
                e2 = e1 ** (lam[3] + bb / (ai + d))
                s[i] = e1 + e2 * (dl1[3] + e2 * dl2[3]) / an - self.correc(i + 1, n)

        for i in range(n2[0]):
            s[i] = -scipy_stats.norm.ppf(s[i], 0., 1.)

        return


class DagostinoTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'D'

    def execute_statistic(self, rvs):
        n = len(rvs)
        if n > 3:
            xs = np.sort(rvs)  # We sort the data
            meanX = sum(xs) / n
            varX = sum(x_i ** 2 for x_i in xs) / n - meanX ** 2
            T = sum((i - 0.5 * (n + 1)) * xs[i - 1] for i in range(1, n + 1))
            D = T / ((n ** 2) * math.sqrt(varX))
            statDa = math.sqrt(n) * (D - 0.28209479) / 0.02998598

            return statDa  # Here is the test statistic value


class ZhangQStarTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'ZQS'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            # Computation of the value of the test statistic
            xs = np.sort(rvs)
            u = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 0.25) - 0.375 / (n + 0.25))

            a = np.zeros(n)
            a[1:] = 1 / ((n - 1) * (u[1:] - u[0]))
            a[0] = -a[1:].sum()

            b = np.zeros(n)
            b[0] = 1 / ((n - 4) * (u[0] - u[4]))
            b[-1] = -b[0]
            b[1] = 1 / ((n - 4) * (u[1] - u[5]))
            b[-2] = -b[1]
            b[2] = 1 / ((n - 4) * (u[2] - u[6]))
            b[-3] = -b[2]
            b[3] = 1 / ((n - 4) * (u[3] - u[7]))
            b[-4] = -b[3]
            for i in range(4, n - 4):
                b[i] = (1 / (u[i] - u[i + 4]) - 1 / (u[i - 4] - u[i])) / (n - 4)

            q1star = -np.dot(a, xs[::-1])
            q2star = -np.dot(b, xs[::-1])

            Qstar = np.log(q1star / q2star)
            return Qstar


"""
class ZhangQQStarTest(AbstractNormalityTest):

    @staticmethod
    def code():
        return 'ZQQ'

    def execute_statistic(self, rvs):
        return self.stat28(rvs)

    def stat28(self, x):
        n = len(x)

        if n > 3:
            # Computation of the value of the test statistic
            def stat27(x):
                pass

            def stat34(x):
                pass

            pvalue27 = [1.0]
            pvalue34 = [1.0]

            stat27(x)  # stat Q de Zhang

            if pvalue27[0] > 0.5:
                pval1 = 1.0 - pvalue27[0]
            else:
                pval1 = pvalue27[0]

            stat34(x)  # stat Q* de Zhang

            if pvalue34[0] > 0.5:
                pval2 = 1.0 - pvalue34[0]
            else:
                pval2 = pvalue34[0]

            stat = -2.0 * (np.log(pval1) + np.log(pval2))  # Combinaison des valeurs-p (Fisher, 1932)

            return stat  # Here is the test statistic value
"""


class SWRGTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'SWRG'

    def execute_statistic(self, rvs):
        n = len(rvs)

        if n > 3:
            # Computation of the value of the test statistic
            mi = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
            fi = scipy_stats.norm.pdf(mi)
            aux2 = 2 * mi * fi
            aux1 = np.concatenate(([0], mi[:-1] * fi[:-1]))
            aux3 = np.concatenate((mi[1:] * fi[1:], [0]))
            aux4 = aux1 - aux2 + aux3
            aistar = -((n + 1) * (n + 2)) * fi * aux4
            norm2 = np.sum(aistar ** 2)
            ai = aistar / np.sqrt(norm2)

            xs = np.sort(rvs)
            meanX = np.mean(xs)
            aux6 = np.sum((xs - meanX) ** 2)
            statWRG = np.sum(ai * xs) ** 2 / aux6

            return statWRG  # Here is the test statistic value


class GMGTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'GMG'

    def execute_statistic(self, rvs):
        return self.stat33(rvs)

    def stat33(self, x):
        n = len(x)

        if n > 3:
            import math
            xtmp = [0] * n
            varX = 0.0
            meanX = 0.0
            Jn = 0.0
            pi = 4.0 * math.atan(1.0)  # or use pi = M_PI, where M_PI is defined in math.h

            # calculate sample mean
            for i in range(n):
                meanX += x[i]
            meanX = meanX / n

            # calculate sample var and standard deviation
            for i in range(n):
                varX += (x[i] - meanX) ** 2
            varX = varX / n
            sdX = math.sqrt(varX)

            # calculate sample median
            for i in range(n):
                xtmp[i] = x[i]

            xtmp = np.sort(xtmp)  # We sort the data

            if n % 2 == 0:
                M = (xtmp[n // 2] + xtmp[n // 2 - 1]) / 2.0
            else:
                M = xtmp[n // 2]  # sample median

            # calculate statRsJ
            for i in range(n):
                Jn += abs(x[i] - M)
            Jn = math.sqrt(pi / 2.0) * Jn / n

            statRsJ = sdX / Jn

            return statRsJ  # Here is the test statistic value


""" Title: Statistique de test de Brys-Hubert-Struyf MC-LR
Ref. (book or article): Brys, G., Hubert, M. and Struyf, A. (2008), Goodness-of-fit tests based on a robust measure of 
skewness, Computational Statistics, Vol. 23, Issue 3, pp. 429-442. 
"""


class BHSTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'BHS'

    def execute_statistic(self, rvs):
        return self.stat16(rvs)

    def stat16(self, x):
        n = len(x)

        if n > 3:
            # Computation of the value of the test statistic
            x_sorted = np.sort(x)
            if n % 2 == 0:
                x1 = x_sorted[:n // 2]
                x2 = x_sorted[n // 2:]
            else:
                x1 = x_sorted[:(n // 2) + 1]
                x2 = x_sorted[(n // 2) + 1:]

            eps = [2.220446e-16, 2.225074e-308]
            iter = [1000, 0]

            print('ssss')
            w1 = self.mc_C_d(x, eps, iter)
            print('ssss1')
            w2 = self.mc_C_d(x1, eps, iter)
            w3 = self.mc_C_d(x2, eps, iter)

            omega = [0.0, 0.198828, 0.198828]
            vec = [w1 - omega[0], -w2 - omega[1], w3 - omega[2]]

            invV = np.array([
                [0.8571890822945882, -0.1051268907484579, 0.1051268907484580],
                [-0.1051268907484579, 0.3944817329840534, -0.01109532299714422],
                [0.1051268907484579, -0.01109532299714422, 0.3944817329840535]
            ])

            statTMCLR = n * np.dot(vec, np.dot(invV, vec))
            return statTMCLR  # Here is the test statistic value

    def mc_C_d(self, z, eps, iter):
        """
        NOTE:
            eps = [eps1, eps2]
            iter = [maxit, trace_lev] as input
                  = [it, converged] as output
        """
        trace_lev = iter[1]
        it = 0
        converged = True
        medc = None  # "the" result
        # DBL_MAX = 1.7976931348623158e+308
        DBL_MAX = 1.7976931348623158e+308
        Large = DBL_MAX / 4.

        n = len(z)
        if n < 3:
            medc = 0.
            iter[0] = it  # to return
            iter[1] = converged
            return medc

        # copy data before sort()ing in place, also reflecting it -- dealing with +-Inf.
        # NOTE: x[0] "empty" so we can use 1-indexing below
        x = [0.0] * (n + 1)
        for i in range(n):
            zi = z[i]
            x[i + 1] = -((Large if zi == float('inf') else (-Large if zi == -float('inf') else zi)))

        x[1:] = sorted(x[1:])  # full sort

        # xmed := median(x[1:n]) = -median(z[0:(n-1)])
        if n % 2:  # n even
            xmed = x[(n // 2) + 1]
        else:  # n odd
            ind = (n // 2)
            xmed = (x[ind] + x[ind + 1]) / 2.0

        if abs(x[1] - xmed) < eps[0] * (eps[0] + abs(xmed)):
            medc = -1.
            iter[0] = it  # to return
            iter[1] = converged
            return medc
        elif abs(x[n] - xmed) < eps[0] * (eps[0] + abs(xmed)):
            medc = 1.
            iter[0] = it  # to return
            iter[1] = converged
            return medc
        # else: median is not at the border
        if trace_lev:
            print(f"mc_C_d(z[1:{n}], trace_lev={trace_lev}): Median = {-xmed} (not at the border)")

        # center x[] wrt median --> such that then median(x[1:n]) == 0
        for i in range(1, n + 1):
            x[i] -= xmed

        # Now scale to inside [-0.5, 0.5] and flip sign such that afterwards
        # x[1] >= x[2] >= ... >= x[n]
        xden = -2 * max(-x[1], x[n])
        for i in range(1, n + 1):
            x[i] /= xden
        xmed /= xden
        if trace_lev >= 2:
            print(f" x[] has been rescaled (* 1/s) with s = {-xden}")

        j = 1
        x_eps = eps[0] * (eps[0] + abs(xmed))
        while j <= n and x[j] > x_eps:  # test relative to xmed
            j += 1
        if trace_lev >= 2:
            print(f"   x1[] := {{x | x_j > x_eps = {x_eps}}}    has {j - 1} (='j-1') entries")
        i = 1
        x2 = x[j - 1:]  # pointer -- corresponding to x2[i] = x[j]
        while j <= n and x[j] > -x_eps:  # test relative to xmed
            j += 1
            i += 1
        # now x1[] := {x | x_j > -eps} also includes the median (0)
        if trace_lev >= 2:
            print(f"'median-x' {{x | -eps < x_i <= eps}} has {i - 1} (= 'k') entries")
        h1 = j - 1  # == size of x1[] == the sum of those two sizes above
        # conceptually, x2[] := {x | x_j <= eps} (which includes the median 0)
        h2 = i + (n - j)  # == size of x2[] == maximal size of whimed() arrays

        if trace_lev:
            print(f"  now allocating 2+5 work arrays of size (1+) h2={h2} each:")
        # work arrays for whimed_i()
        acand = [0.0] * h2
        a_srt = [0.0] * h2
        iw_cand = [0] * h2
        # work arrays for the fast-median-of-table algorithm: currently still with 1-indexing
        left = [1] * (h2 + 1)
        right = [h1] * (h2 + 1)
        p = [0] * (h2 + 1)
        q = [0] * (h2 + 1)

        nr = (h1 * h2)  # <-- careful to *NOT* overflow
        knew = nr // 2 + 1
        if trace_lev >= 2:
            print(f" (h1,h2, nr, knew) = ({h1},{h2}, {nr}, {knew})")

        trial = -2.  # -Wall
        work = [0.0] * n
        iwt = [0] * n
        IsFound = False
        nl = 0
        neq = 0
        # MK: 'neq' counts the number of observations in the inside the tolerance range,
        # i.e., where left > right + 1, since we would miss those when just using 'nl-nr'.
        # This is to prevent index overflow in work[] later on.
        # left might be larger than right + 1 since we are only testing with accuracy eps_trial
        # and therefore there might be more than one observation in the `tolerance range`
        # between < and <=.
        while not IsFound and (nr - nl + neq > n) and it < iter[0]:
            print(it)
            it += 1
            j = 0
            for i in range(1, h2 + 1):
                if left[i] <= right[i]:
                    iwt[j] = right[i] - left[i] + 1
                    k = left[i] + (iwt[j] // 2)
                    work[j] = self.h_kern(x[k], x2[i - 1], k, i, h1 + 1, eps[1])
                    j += 1
            if trace_lev >= 4:
                print(" before whimed(): work and iwt, each [0:({})]".format(j - 1))
                if j >= 100:
                    for i in range(90):
                        print(f" {work[i]:8g}", end="")
                    print("\n  ... ", end="")
                    for i in range(j - 4, j):
                        print(f" {work[i]:8g}", end="")
                    print("\n", end="")
                    for i in range(90):
                        print(f" {iwt[i]:8d}", end="")
                    print("\n  ... ", end="")
                    for i in range(j - 4, j):
                        print(f" {iwt[i]:8d}", end="")
                    print("\n", end="")
                else:  # j <= 99
                    for i in range(j):
                        print(f" {work[i]:8g}", end="")
                    print("\n", end="")
                    for i in range(j):
                        print(f" {iwt[i]:8d}", end="")
                    print("\n", end="")
            trial = self.whimed_i(work, iwt, j, acand, a_srt, iw_cand)
            eps_trial = eps[0] * (eps[0] + abs(trial))
            if trace_lev >= 3:
                print(f"{' ':2s} it={it:2d}, whimed(*, n={j:6d})= {trial:8g} ", end="")

            j = 1
            for i in range(h2, 0, -1):
                while j <= h1 and self.h_kern(x[j], x2[i - 1], j, i, h1 + 1, eps[1]) - trial > eps_trial:
                    j += 1
                p[i] = j - 1

            j = h1
            sum_p = 0
            sum_q = 0
            for i in range(1, h2 + 1):
                while j >= 1 and trial - self.h_kern(x[j], x2[i - 1], j, i, h1 + 1, eps[1]) > eps_trial:
                    j -= 1
                q[i] = j + 1

                sum_p += p[i]
                sum_q += j  # = q[i]-1

            if trace_lev >= 3:
                if trace_lev == 3:
                    print(f"sum_(p,q)= ({sum_p},{sum_q})", end="")
                else:  # trace_lev >= 4
                    print(f"\n{' ':3s} p[1:{h2}]:", end="")
                    lrg = h2 >= 100
                    i_m = 95 if lrg else h2
                    for i in range(1, i_m + 1):
                        print(f" {p[i]:2d}", end="")
                    if lrg:
                        print(" ...", end="")
                    print(f" sum={sum_p:4.0f}")
                    print(f"{' ':3s} q[1:{h2}]:", end="")
                    for i in range(1, i_m + 1):
                        print(f" {q[i]:2d}", end="")
                    if lrg:
                        print(" ...", end="")
                    print(f" sum={sum_q:4.0f}")

            if knew <= sum_p:
                if trace_lev >= 3:
                    print("; sum_p >= kn")
                for i in range(1, h2 + 1):
                    right[i] = p[i]
                    if left[i] > right[i] + 1:
                        neq += left[i] - right[i] - 1
                nr = sum_p
            else:  # knew > sum_p
                IsFound = (knew <= sum_q)  # i.e. sum_p < knew <= sum_q

                if trace_lev >= 3:
                    print("; s_p < kn ?<=? s_q: {}".format("TRUE" if IsFound else "no"))
                if IsFound:
                    medc = trial
                else:  # knew > sum_q
                    for i in range(1, h2 + 1):
                        left[i] = q[i]
                        if left[i] > right[i] + 1:
                            neq += left[i] - right[i] - 1
                    nl = sum_q

        converged = IsFound or (nr - nl + neq <= n)
        if not converged:
            print(f"maximal number of iterations ({iter[0]} =? {it}) reached prematurely")
            # still:
            medc = trial

        if converged and not IsFound:  # e.g., for mc(1:4)
            j = 0
            for i in range(1, h2 + 1):
                if left[i] <= right[i]:
                    for k in range(left[i], right[i] + 1):
                        work[j] = -self.h_kern(x[k], x2[i - 1], k, i, h1 + 1, eps[1])
                        j += 1
            if trace_lev:
                print(f"  not found [it={it},  (nr,nl) = ({nr},{nl})], -> (knew-nl, j) = ({knew - nl},{j})")
            # using rPsort(work, n,k), since we don't need work[] anymore
            work[:(knew - nl)] = sorted(work[:(knew - nl)])
            medc = -work[knew - nl - 1]

        if converged and trace_lev >= 2:
            print(f"converged in {it} iterations")

        iter[0] = it  # to return
        iter[1] = converged

        return medc

    def h_kern(self, a, b, ai, bi, ab, eps):
        if np.abs(a - b) < 2.0 * eps or b > 0:
            return np.sign(ab - (ai + bi))
        else:
            return (a + b) / (a - b)

    def whimed_i(self, a, w, n, a_cand, a_srt, w_cand):
        w_tot = sum(w)
        wrest = 0

        while True:
            a_srt[:] = sorted(a)
            n2 = n // 2
            trial = a_srt[n2]

            wleft = sum(w[i] for i in range(n) if a[i] < trial)
            wmid = sum(w[i] for i in range(n) if a[i] == trial)
            wright = sum(w[i] for i in range(n) if a[i] > trial)

            kcand = 0
            if 2 * (wrest + wleft) > w_tot:
                for i in range(n):
                    if a[i] < trial:
                        a_cand[kcand] = a[i]
                        w_cand[kcand] = w[i]
                        kcand += 1
            elif 2 * (wrest + wleft + wmid) <= w_tot:
                for i in range(n):
                    if a[i] > trial:
                        a_cand[kcand] = a[i]
                        w_cand[kcand] = w[i]
                        kcand += 1
                wrest += wleft + wmid
            else:
                return trial

            n = kcand
            for i in range(n):
                a[i] = a_cand[i]
                w[i] = w_cand[i]


class SpiegelhalterTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'SH'

    def execute_statistic(self, rvs):
        return self.stat41(rvs)

    def stat41(self, x):
        n = len(x)

        if n > 3:
            statSp, varX, mean = 0.0, 0.0, 0.0
            max_val, min_val = x[0], x[0]
            for i in range(1, n):
                if x[i] > max_val:
                    max_val = x[i]
                if x[i] < min_val:
                    min_val = x[i]
            for i in range(n):
                mean += x[i]
            mean /= n
            for i in range(n):
                varX += (x[i] - mean) ** 2
            varX /= (n - 1)
            sd = math.sqrt(varX)
            u = (max_val - min_val) / sd
            g = 0.0
            for i in range(n):
                g += abs(x[i] - mean)
            g /= (sd * math.sqrt(n) * math.sqrt(n - 1))
            if n < 150:
                cn = 0.5 * math.gamma((n + 1)) ** (1 / (n - 1)) / n
            else:
                cn = (2 * math.pi) ** (1 / (2 * (n - 1))) * ((n * math.sqrt(n)) / math.e) ** (1 / (n - 1)) / (
                        2 * math.e)  # Stirling approximation

            statSp = ((cn * u) ** (-(n - 1)) + g ** (-(n - 1))) ** (1 / (n - 1))

            return statSp  # Here is the test statistic value


class DesgagneLafayeTest(AbstractNormalityTestStatistic):

    @staticmethod
    def code():
        return 'DLDMZEPD'

    def execute_statistic(self, rvs):
        return self.stat35(rvs)

    def stat35(self, x):
        n = len(x)

        if n > 3:
            # Computation of the value of the test statistic
            y = np.zeros(n)
            varpopX = 0.0
            meanX = np.mean(x)
            r1 = 0.0
            r2 = 0.0
            r3 = 0.0

            for i in range(n):
                varpopX += x[i] ** 2
            varpopX = varpopX / n - meanX ** 2
            sdX = np.sqrt(varpopX)
            for i in range(n):
                y[i] = (x[i] - meanX) / sdX

            # Formulas given in our paper p. 169
            for i in range(n):
                r1 += y[i] ** 2 * np.log(abs(y[i]))
                r2 += np.log(1.0 + abs(y[i]))
                r3 += np.log(np.log(2.71828182846 + abs(y[i])))
            r1 = 0.18240929 - 0.5 * r1 / n
            r2 = 0.5348223 - r2 / n
            r3 = 0.20981558 - r3 / n

            # Formula given in our paper p. 170
            Rn = n * ((r1 * 1259.04213344 - r2 * 32040.69569026 + r3 * 85065.77739473) * r1 + (
                    -r1 * 32040.6956903 + r2 * 918649.9005906 - r3 * 2425883.3443201) * r2 + (
                              r1 * 85065.7773947 - r2 * 2425883.3443201 + r3 * 6407749.8211208) * r3)

            return Rn  # Here is the test statistic value
