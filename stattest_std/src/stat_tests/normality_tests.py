import math
from typing import override

from stattest_ext.src.core.distribution.norm import pdf_norm
from stattest_std.src.stat_tests.goodness_test import GoodnessOfFitTest
from stattest_std.src.cache_services.cache import MonteCarloCacheService

from stattest_ext.src.core.distribution import norm  # TODO: move to other package
import numpy as np
import scipy.stats as scipy_stats
import pandas as pd


class NormalityTest(GoodnessOfFitTest):

    def __init__(self, cache=MonteCarloCacheService()):
        super().__init__(cache)

        self.mean = 0
        self.var = 1

    @staticmethod
    @override
    def code():
        return super(NormalityTest, NormalityTest).code() + '_norm'

    @override
    def __generate_statistic(self, rvs_size, alpha, keys_cr, count):  # TODO: move statistic generation to ext_package
        result = np.zeros(count)

        for i in range(count):
            x = self.generate(size=rvs_size, mean=self.mean, var=self.var)
            result[i] = self.execute_statistic(x)

        result.sort()

        ecdf = scipy_stats.ecdf(result)
        x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
        self.cache.put_with_level(keys_cr, x_cr)
        self.cache.put_distribution(self.code(), rvs_size, result)
        self.cache.flush()
        return x_cr

    @override
    def generate(self, size, mean=0, var=1):
        return norm.generate_norm(size, mean, var)


# TODO: make common ??
class KSTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'KS' + super(KSTest, KSTest).code()

    def execute_statistic(self, rvs, alternative='two-sided', mode='auto'):
        """
        Title: The Kolmogorov-Smirnov statistic for the Laplace distribution Ref. (book or article): Puig,
        P. and Stephens, M. A. (2000). Tests of fit for the Laplace distribution, with applications. Technometrics
        42, 417-424.

        :param alternative: {'two-sided', 'less', 'greater'}, optional
        :param mode: {'auto', 'exact', 'approx', 'asymp'}, optional
        Defines the distribution used for calculating the p-value.
        The following options are available (default is 'auto'):

          * 'auto' : selects one of the other options.
          * 'exact' : uses the exact distribution of test statistic.
          * 'approx' : approximates the two-sided probability with twice
            the one-sided probability
          * 'asymp': uses asymptotic distribution of test statistic
        :param rvs: unsorted vector
        :return:
        """
        rvs = np.sort(rvs)
        cdf_vals = scipy_stats.norm.cdf(rvs)
        n = len(rvs)

        d_minus, _ = KSTest.__compute_dminus(cdf_vals, rvs)

        if alternative == 'greater':
            d_plus, d_location = KSTest.__compute_dplus(cdf_vals, rvs)
            return d_plus  # KStestResult(Dplus, distributions.ksone.sf(Dplus, N),
            # statistic_location=d_location, statistic_sign=1)
        if alternative == 'less':
            d_minus, d_location = KSTest.__compute_dminus(cdf_vals, rvs)
            return d_minus  # KStestResult(Dminus, distributions.ksone.sf(Dminus, N),
            # statistic_location=d_location, statistic_sign=-1)

        # alternative == 'two-sided':
        d_plus, d_plus_location = KSTest.__compute_dplus(cdf_vals, rvs)
        d_minus, d_minus_location = KSTest.__compute_dminus(cdf_vals, rvs)
        if d_plus > d_minus:
            d = d_plus
            d_location = d_plus_location
            d_sign = 1
        else:
            d = d_minus
            d_location = d_minus_location
            d_sign = -1

        if mode == 'auto':  # Always select exact
            mode = 'exact'
        if mode == 'exact':
            prob = scipy_stats.distributions.kstwo.sf(d, n)
        elif mode == 'asymp':
            prob = scipy_stats.distributions.kstwobign.sf(d * np.sqrt(n))
        else:
            # mode == 'approx'
            prob = 2 * scipy_stats.distributions.ksone.sf(d, n)
        # print('PROB', prob)
        prob = np.clip(prob, 0, 1)
        return d

    def calculate_critical_value(self, rvs_size, alpha, count=500_000):
        return scipy_stats.distributions.kstwo.ppf(1 - alpha, rvs_size)

    @staticmethod
    def __compute_dplus(cdf_vals, rvs):
        n = len(cdf_vals)
        d_plus = (np.arange(1.0, n + 1) / n - cdf_vals)
        a_max = d_plus.argmax()
        loc_max = rvs[a_max]
        return d_plus[a_max], loc_max

    @staticmethod
    def __compute_dminus(cdf_vals, rvs):
        n = len(cdf_vals)
        d_minus = (cdf_vals - np.arange(0.0, n) / n)
        a_max = d_minus.argmax()
        loc_max = rvs[a_max]
        return d_minus[a_max], loc_max


class ChiSquareTest(NormalityTest):  # TODO: check test correctness

    @staticmethod
    @override
    def code():
        return 'CHI2' + super(ChiSquareTest, ChiSquareTest).code()

    def execute_statistic(self, rvs, **kwargs):
        rvs = np.sort(rvs)

        f_obs = np.asanyarray(rvs)
        f_obs_float = f_obs.astype(np.float64)
        f_exp = pdf_norm(rvs)  # TODO: remove link to ext package
        scipy_stats.chi2_contingency()  # TODO: fix warning!!
        terms = (f_obs_float - f_exp) ** 2 / f_exp
        return terms.sum(axis=0)


class ADTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'AD' + super(ADTest, ADTest).code()

    def execute_statistic(self, rvs, **kwargs):
        """
        Title: The Anderson-Darling test Ref. (book or article): See package nortest and also Table 4.9 p. 127 in M.
        A. Stephens, “Tests Based on EDF Statistics,” In: R. B. D’Agostino and M. A. Stephens, Eds., Goodness-of-Fit
        Techniques, Marcel Dekker, New York, 1986, pp. 97-193.

        :param rvs:
        :return:

        Parameters
        ----------
        **kwargs
        """
        n = len(rvs)

        s = np.std(rvs, ddof=1, axis=0)
        y = np.sort(rvs)
        xbar = np.mean(rvs, axis=0)
        w = (y - xbar) / s
        log_cdf = scipy_stats.distributions.norm.logcdf(w)
        log_sf = scipy_stats.distributions.norm.logsf(w)

        i = np.arange(1, n + 1)
        a2 = -n - np.sum((2 * i - 1.0) / n * (log_cdf + log_sf[::-1]), axis=0)
        return a2

    def calculate_critical_value(self, rvs_size, alpha, count=500_000):  # TODO: check correctness
        # # Values from Stephens, M A, "EDF Statistics for Goodness of Fit and
        # #             Some Comparisons", Journal of the American Statistical
        # #             Association, Vol. 69, Issue 347, Sept. 1974, pp 730-737
        # _avals_norm = np.array([0.576, 0.656, 0.787, 0.918, 1.092])

        # sig = [0.15, 0.10, 0.05, 0.025, 0.01].index(alpha)
        # critical = np.around(_avals_norm / (1.0 + 4.0 / rvs_size - 25.0 / rvs_size / rvs_size), 3)
        # print(critical[sig])
        return super().calculate_critical_value(rvs_size, alpha)


class SWTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SW' + super(SWTest, SWTest).code()

    def execute_statistic(self, rvs, **kwargs):
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
        # wn = np.array([p1[0] * (u ** 5), p1[1] * (u ** 4),
        # p1[2] * (u ** 3), p1[3] * (u ** 2), p1[4] * (u ** 1), p1[5]]).sum()
        w1 = -wn

        if n == 4 or n == 5:
            phi = (m2.sum() - 2 * m[-1] ** 2) / (1 - 2 * wn ** 2)
            phi_sqrt = np.sqrt(phi)
            result = np.array([m[k] / phi_sqrt for k in range(1, n - 1)])
            return np.concatenate([[w1], result, [wn]])  # TODO: ???

        p2 = [-3.582633, 5.682633, -1.752461, -0.293762, 0.042981, cn1]

        if n > 5:
            wn1 = np.polyval(p2, u)
            w2 = -wn1
            phi = (m2.sum() - 2 * m[-1] ** 2 - 2 * m[-2] ** 2) / (1 - 2 * wn ** 2 - 2 * wn1 ** 2)
            phi_sqrt = np.sqrt(phi)
            result = np.array([m[k] / phi_sqrt for k in range(2, n - 2)])
            return np.concatenate([[w1, w2], result, [wn1, wn]])  # TODO: ???


class SWMTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SWM' + super(SWMTest, SWMTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        rvs = np.sort(rvs)
        vals = np.sort(np.asarray(rvs))
        cdf_vals = scipy_stats.norm.cdf(vals)

        u = (2 * np.arange(1, n + 1) - 1) / (2 * n)
        cm = 1 / (12 * n) + np.sum((u - cdf_vals) ** 2)
        return cm


class LillieforsTest(KSTest):

    @staticmethod
    @override
    def code():
        return 'LILLIE' + super(LillieforsTest, LillieforsTest).code()

    def execute_statistic(self, rvs, **kwargs):
        x = np.asarray(rvs)
        z = (x - x.mean()) / x.std(ddof=1)

        d_ks = super().execute_statistic(z)

        return d_ks


class DATest(NormalityTest):  # TODO: check for correctness

    @staticmethod
    @override
    def code():
        return 'DA' + super(DATest, DATest).code()

    def execute_statistic(self, rvs, **kwargs):
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


class JBTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'JB' + super(JBTest, JBTest).code()

    def execute_statistic(self, rvs, **kwargs):
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


class SkewTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SKEW' + super(SkewTest, SkewTest).code()

    def execute_statistic(self, rvs, **kwargs):
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
        w2 = -1 + math.sqrt(2 * (beta2 - 1))
        delta = 1 / math.sqrt(0.5 * math.log(w2))
        alpha = math.sqrt(2.0 / (w2 - 1))
        y = np.where(y == 0, 1, y)  # TODO: ???
        z = delta * np.log(y / alpha + np.sqrt((y / alpha) ** 2 + 1))

        return z


class KurtosisTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'KURTOSIS' + super(KurtosisTest, KurtosisTest).code()

    def execute_statistic(self, rvs, **kwargs):
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

        e = 3.0 * (n - 1) / (n + 1)
        var_b2 = 24.0 * n * (n - 2) * (n - 3) / ((n + 1) * (n + 1.) * (n + 3) * (n + 5))  # [1]_ Eq. 1
        x = (b2 - e) / np.sqrt(var_b2)  # [1]_ Eq. 4
        # [1]_ Eq. 2:
        sqrt_beta1 = 6.0 * (n * n - 5 * n + 2) / ((n + 7) * (n + 9)) * np.sqrt((6.0 * (n + 3) * (n + 5)) /
                                                                               (n * (n - 2) * (n - 3)))
        # [1]_ Eq. 3:
        a = 6.0 + 8.0 / sqrt_beta1 * (2.0 / sqrt_beta1 + np.sqrt(1 + 4.0 / (sqrt_beta1 ** 2)))
        term1 = 1 - 2 / (9.0 * a)
        denom = 1 + x * np.sqrt(2 / (a - 4.0))
        term2 = np.sign(denom) * np.where(denom == 0.0, np.nan,
                                          np.power((1 - 2.0 / a) / np.abs(denom), 1 / 3.0))
        # if np.any(denom == 0):
        #    msg = ("Test statistic not defined in some cases due to division by "
        #           "zero. Return nan in that case...")
        #    warnings.warn(msg, RuntimeWarning, stacklevel=2)

        z = (term1 - term2) / np.sqrt(2 / (9.0 * a))  # [1]_ Eq. 5

        return z


class DAPTest(SkewTest, KurtosisTest):

    @staticmethod
    @override
    def code():
        return 'DAP' + super(DAPTest, DAPTest).code()

    def execute_statistic(self, rvs, **kwargs):
        x = np.asanyarray(rvs)
        y = np.sort(x)

        s = self.skew_test(y)
        k = self.kurtosis_test(y)
        k2 = s * s + k * k
        return k2


# https://github.com/puzzle-in-a-mug/normtest
class FilliTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'Filli' + super(FilliTest, FilliTest).code()

    def execute_statistic(self, rvs, **kwargs):
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
class LooneyGulledgeTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'LG' + super(LooneyGulledgeTest, LooneyGulledgeTest).code()

    def execute_statistic(self, rvs, **kwargs):
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
class RyanJoinerTest(NormalityTest):
    def __init__(self, weighted=False, cte_alpha="3/8"):
        super().__init__()
        self.weighted = weighted
        self.cte_alpha = cte_alpha

    @staticmethod
    @override
    def code():
        return 'RJ' + super(RyanJoinerTest, RyanJoinerTest).code()

    def execute_statistic(self, rvs, **kwargs):
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


class SFTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SF' + super(SFTest, SFTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        rvs = np.sort(rvs)

        x_mean = np.mean(rvs)
        alpha = 0.375
        terms = (np.arange(1, n + 1) - alpha) / (n - 2 * alpha + 1)
        e = -scipy_stats.norm.ppf(terms)

        w = np.sum(e * rvs) ** 2 / (np.sum((rvs - x_mean) ** 2) * np.sum(e ** 2))
        return w


# https://habr.com/ru/articles/685582/
class EPTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'EP' + super(EPTest, EPTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        x = np.sort(rvs)
        x_mean = np.mean(x)
        m2 = np.var(x, ddof=0)

        a = np.sqrt(2) * np.sum([np.exp(-(x[i] - x_mean) ** 2 / (4 * m2)) for i in range(n)])
        b = 2 / n * np.sum(
            [np.sum([np.exp(-(x[j] - x[k]) ** 2 / (2 * m2)) for j in range(0, k)])
             for k in range(1, n)])
        t = 1 + n / np.sqrt(3) + b - a
        return t


class Hosking2Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'HOSKING2' + super(Hosking2Test, Hosking2Test).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:

            x_tmp = [0] * n
            l21, l31, l41 = 0.0, 0.0, 0.0
            mu_tau41, v_tau31, v_tau41 = 0.0, 0.0, 0.0
            for i in range(n):
                x_tmp[i] = rvs[i]
            x_tmp = np.sort(x_tmp)
            for i in range(2, n):
                l21 += x_tmp[i - 1] * self.pstarmod1(2, n, i)
                l31 += x_tmp[i - 1] * self.pstarmod1(3, n, i)
                l41 += x_tmp[i - 1] * self.pstarmod1(4, n, i)
            l21 = l21 / (2.0 * math.comb(n, 4))
            l31 = l31 / (3.0 * math.comb(n, 5))
            l41 = l41 / (4.0 * math.comb(n, 6))
            tau31 = l31 / l21
            tau41 = l41 / l21
            if 1 <= n <= 25:
                mu_tau41 = 0.067077
                v_tau31 = 0.0081391
                v_tau41 = 0.0042752
            if 25 < n <= 50:
                mu_tau41 = 0.064456
                v_tau31 = 0.0034657
                v_tau41 = 0.0015699
            if 50 < n:
                mu_tau41 = 0.063424
                v_tau31 = 0.0016064
                v_tau41 = 0.00068100
            return pow(tau31, 2.0) / v_tau31 + pow(tau41 - mu_tau41, 2.0) / v_tau41

        return 0

    @staticmethod
    def pstarmod1(r, n, i):
        res = 0.0
        for k in range(r):
            res = res + (-1.0) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 1 - 1 - k) * math.comb(n - i, 1 + k)

        return res


class Hosking1Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'HOSKING1' + super(Hosking1Test, Hosking1Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat10(rvs)

    @staticmethod
    def stat10(x):
        n = len(x)

        if n > 3:
            x_tmp = x[:n].copy()
            x_tmp.sort()
            tmp1 = n * (n - 1)
            tmp2 = tmp1 * (n - 2)
            tmp3 = tmp2 * (n - 3)
            b0 = sum(x_tmp[:3]) + sum(x_tmp[3:])
            b1 = 1.0 * x_tmp[1] + 2.0 * x_tmp[2] + sum(i * x_tmp[i] for i in range(3, n))
            b2 = 2.0 * x_tmp[2] + sum((i * (i - 1)) * x_tmp[i] for i in range(3, n))
            b3 = sum((i * (i - 1) * (i - 2)) * x_tmp[i] for i in range(3, n))
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
                mu_tau4 = 0.12383
                v_tau3 = 0.0088038
                v_tau4 = 0.0049295
            elif 25 < n <= 50:
                mu_tau4 = 0.12321
                v_tau3 = 0.0040493
                v_tau4 = 0.0020802
            else:
                mu_tau4 = 0.12291
                v_tau3 = 0.0019434
                v_tau4 = 0.00095785

            stat_tl_mom = (tau3 ** 2) / v_tau3 + (tau4 - mu_tau4) ** 2 / v_tau4
            return stat_tl_mom


class Hosking3Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'HOSKING3' + super(Hosking3Test, Hosking3Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat12(rvs)

    def stat12(self, x):
        n = len(x)

        if n > 3:
            x_tmp = x[:n]
            x_tmp.sort()
            l22 = 0.0
            l32 = 0.0
            l42 = 0.0
            for i in range(2, n):
                l22 += x_tmp[i - 1] * self.pstarmod2(2, n, i)
                l32 += x_tmp[i - 1] * self.pstarmod2(3, n, i)
                l42 += x_tmp[i - 1] * self.pstarmod2(4, n, i)
            l22 /= 2.0 * math.comb(n, 6)
            l32 /= 3.0 * math.comb(n, 7)
            l42 /= 4.0 * math.comb(n, 8)
            tau32 = l32 / l22
            tau42 = l42 / l22

            if 1 <= n <= 25:
                mu_tau42 = 0.044174
                v_tau32 = 0.0086570
                v_tau42 = 0.0042066
            elif 25 < n <= 50:
                mu_tau42 = 0.040389
                v_tau32 = 0.0033818
                v_tau42 = 0.0013301
            else:
                mu_tau42 = 0.039030
                v_tau32 = 0.0015120
                v_tau42 = 0.00054207

            stat_tl_mom2 = (tau32 ** 2) / v_tau32 + (tau42 - mu_tau42) ** 2 / v_tau42
            return stat_tl_mom2

    @staticmethod
    def pstarmod2(r, n, i):
        res = 0.0
        for k in range(r):
            res += (-1) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 2 - 1 - k) * math.comb(n - i, 2 + k)
        return res


class Hosking4Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'HOSKING4' + super(Hosking4Test, Hosking4Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat13(rvs)

    def stat13(self, x):
        n = len(x)

        if n > 3:
            x_tmp = x[:n]
            x_tmp.sort()
            l23 = 0.0
            l33 = 0.0
            l43 = 0.0
            for i in range(2, n):
                l23 += x_tmp[i - 1] * self.pstarmod3(2, n, i)
                l33 += x_tmp[i - 1] * self.pstarmod3(3, n, i)
                l43 += x_tmp[i - 1] * self.pstarmod3(4, n, i)
            l23 /= 2.0 * math.comb(n, 8)
            l33 /= 3.0 * math.comb(n, 9)
            l43 /= 4.0 * math.comb(n, 10)
            tau33 = l33 / l23
            tau43 = l43 / l23

            if 1 <= n <= 25:
                mu_tau43 = 0.033180
                v_tau33 = 0.0095765
                v_tau43 = 0.0044609
            elif 25 < n <= 50:
                mu_tau43 = 0.028224
                v_tau33 = 0.0033813
                v_tau43 = 0.0011823
            else:
                mu_tau43 = 0.026645
                v_tau33 = 0.0014547
                v_tau43 = 0.00045107

            stat_tl_mom3 = (tau33 ** 2) / v_tau33 + (tau43 - mu_tau43) ** 2 / v_tau43
            return stat_tl_mom3

    @staticmethod
    def pstarmod3(r, n, i):
        res = 0.0
        for k in range(r):
            res += (-1) ** k * math.comb(r - 1, k) * math.comb(i - 1, r + 3 - 1 - k) * math.comb(n - i, 3 + k)
        return res


class ZhangWuCTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'ZWC' + super(ZhangWuCTest, ZhangWuCTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:
            phiz = np.zeros(n)
            mean_x = np.mean(rvs)
            var_x = np.var(rvs, ddof=1)
            sd_x = np.sqrt(var_x)
            for i in range(n):
                phiz[i] = scipy_stats.norm.cdf((rvs[i] - mean_x) / sd_x)
            phiz.sort()
            stat_zc = 0.0
            for i in range(1, n + 1):
                stat_zc += np.log((1.0 / phiz[i - 1] - 1.0) / ((n - 0.5) / (i - 0.75) - 1.0)) ** 2
            return stat_zc


class ZhangWuATest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'ZWA' + super(ZhangWuATest, ZhangWuATest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:
            phiz = np.zeros(n)
            mean_x = np.mean(rvs)
            var_x = np.var(rvs)
            sd_x = np.sqrt(var_x)
            for i in range(n):
                phiz[i] = scipy_stats.norm.cdf((rvs[i] - mean_x) / sd_x)
            phiz.sort()
            stat_za = 0.0
            for i in range(1, n + 1):
                stat_za += np.log(phiz[i - 1]) / ((n - i) + 0.5) + np.log(1.0 - phiz[i - 1]) / (i - 0.5)
            stat_za = -stat_za
            stat_za = 10.0 * stat_za - 32.0
            return stat_za


class GlenLeemisBarrTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'GLB' + super(GlenLeemisBarrTest, GlenLeemisBarrTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:
            phiz = np.zeros(n)
            mean_x = np.mean(rvs)
            var_x = np.var(rvs, ddof=1)
            sd_x = np.sqrt(var_x)
            for i in range(n):
                phiz[i] = scipy_stats.norm.cdf((rvs[i] - mean_x) / sd_x)
            phiz.sort()
            for i in range(1, n + 1):
                phiz[i - 1] = scipy_stats.beta.cdf(phiz[i - 1], i, n - i + 1)
            phiz.sort()
            stat_ps = 0
            for i in range(1, n + 1):
                stat_ps += (2 * n + 1 - 2 * i) * np.log(phiz[i - 1]) + (2 * i - 1) * np.log(1 - phiz[i - 1])
            return -n - stat_ps / n


class DoornikHansenTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'DH' + super(DoornikHansenTest, DoornikHansenTest).code()

    def execute_statistic(self, rvs, **kwargs):
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

    @staticmethod
    def skewness_to_z1(skew, n):
        b = 3 * ((n ** 2) + 27 * n - 70) * (n + 1) * (n + 3) / ((n - 2) * (n + 5) * (n + 7) * (n + 9))
        w2 = -1 + math.sqrt(2 * (b - 1))
        d = 1 / math.sqrt(math.log(math.sqrt(w2)))
        y = skew * math.sqrt((n + 1) * (n + 3) / (6 * (n - 2)))
        a = math.sqrt(2 / (w2 - 1))
        z = d * math.log((y / a) + math.sqrt((y / a) ** 2 + 1))
        return z

    @staticmethod
    def kurtosis_to_z2(skew, kurt, n):
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


class RobustJarqueBeraTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'RJB' + super(RobustJarqueBeraTest, RobustJarqueBeraTest).code()

    def execute_statistic(self, rvs, **kwargs):
        y = np.sort(rvs)
        n = len(rvs)
        m = np.median(y)
        c = np.sqrt(math.pi / 2)
        j = (c / n) * np.sum(np.abs(rvs - m))
        m_3 = scipy_stats.moment(y, moment=3)
        m_4 = scipy_stats.moment(y, moment=4)
        rjb = (n / 6) * (m_3 / j ** 3) ** 2 + (n / 64) * (m_4 / j ** 4 - 3) ** 2
        return rjb


class BontempsMeddahi1Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'BM1' + super(BontempsMeddahi1Test, BontempsMeddahi1Test).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:
            z = [0.0] * n
            var_x = 0.0
            mean_x = 0.0
            tmp3 = 0.0
            tmp4 = 0.0

            for i in range(n):
                mean_x += rvs[i]
            mean_x /= n

            for i in range(n):
                var_x += rvs[i] ** 2
            var_x = (n * (var_x / n - mean_x ** 2)) / (n - 1)
            sd_x = math.sqrt(var_x)

            for i in range(n):
                z[i] = (rvs[i] - mean_x) / sd_x

            for i in range(n):
                tmp3 += (z[i] ** 3 - 3 * z[i]) / math.sqrt(6)
                tmp4 += (z[i] ** 4 - 6 * z[i] ** 2 + 3) / (2 * math.sqrt(6))

            stat_bm34 = (tmp3 ** 2 + tmp4 ** 2) / n
            return stat_bm34


class BontempsMeddahi2Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'BM2' + super(BontempsMeddahi2Test, BontempsMeddahi2Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat15(rvs)

    @staticmethod
    def stat15(x):
        n = len(x)

        if n > 3:
            z = np.zeros(n)
            mean_x = np.mean(x)
            var_x = np.var(x, ddof=1)
            sd_x = np.sqrt(var_x)
            for i in range(n):
                z[i] = (x[i] - mean_x) / sd_x
            tmp3 = np.sum((z ** 3 - 3 * z) / np.sqrt(6))
            tmp4 = np.sum((z ** 4 - 6 * z ** 2 + 3) / (2 * np.sqrt(6)))
            tmp5 = np.sum((z ** 5 - 10 * z ** 3 + 15 * z) / (2 * np.sqrt(30)))
            tmp6 = np.sum((z ** 6 - 15 * z ** 4 + 45 * z ** 2 - 15) / (12 * np.sqrt(5)))
            stat_bm36 = (tmp3 ** 2 + tmp4 ** 2 + tmp5 ** 2 + tmp6 ** 2) / n
            return stat_bm36


class BonettSeierTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'BS' + super(BonettSeierTest, BonettSeierTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat17(rvs)

    @staticmethod
    def stat17(x):
        n = len(x)

        if n > 3:
            m2 = 0.0
            mean_x = 0.0
            term = 0.0

            for i in range(n):
                mean_x += x[i]

            mean_x = mean_x / float(n)

            for i in range(n):
                m2 += (x[i] - mean_x) ** 2
                term += abs(x[i] - mean_x)

            m2 = m2 / float(n)
            term = term / float(n)
            omega = 13.29 * (math.log(math.sqrt(m2)) - math.log(term))
            stat_tw = math.sqrt(float(n + 2)) * (omega - 3.0) / 3.54
            return stat_tw


class MartinezIglewiczTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'MI' + super(MartinezIglewiczTest, MartinezIglewiczTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat32(rvs)

    @staticmethod
    def stat32(x):
        n = len(x)

        if n > 3:
            x_tmp = np.copy(x)
            x_tmp.sort()
            if n % 2 == 0:
                m = (x_tmp[n // 2] + x_tmp[n // 2 - 1]) / 2.0
            else:
                m = x_tmp[n // 2]

            aux1 = x - m
            x_tmp = np.abs(aux1)
            x_tmp.sort()
            if n % 2 == 0:
                a = (x_tmp[n // 2] + x_tmp[n // 2 - 1]) / 2.0
            else:
                a = x_tmp[n // 2]
            a = 9.0 * a

            z = aux1 / a
            term1 = np.sum(aux1 ** 2 * (1 - z ** 2) ** 4)
            term2 = np.sum((1 - z ** 2) * (1 - 5 * z ** 2))
            term3 = np.sum(aux1 ** 2)

            sb2 = (n * term1) / term2 ** 2
            stat_in = (term3 / (n - 1)) / sb2
            return stat_in


class CabanaCabana1Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'CC1' + super(CabanaCabana1Test, CabanaCabana1Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat19(rvs)

    @staticmethod
    def stat19(x):
        n = len(x)

        if n > 3:
            z_data = (x - np.mean(x)) / np.std(x, ddof=1)
            mean_h3 = np.sum(z_data ** 3 - 3 * z_data) / (np.sqrt(6) * np.sqrt(n))
            mean_h4 = np.sum(z_data ** 4 - 6 * z_data ** 2 + 3) / (2 * np.sqrt(6) * np.sqrt(n))
            mean_h5 = np.sum(z_data ** 5 - 10 * z_data ** 3 + 15 * z_data) / (2 * np.sqrt(30) * np.sqrt(n))
            mean_h6 = np.sum(z_data ** 6 - 15 * z_data ** 4 + 45 * z_data ** 2 - 15) / (12 * np.sqrt(5) * np.sqrt(n))
            mean_h7 = np.sum(z_data ** 7 - 21 * z_data ** 5 + 105 * z_data ** 3 - 105 * z_data) / (
                    12 * np.sqrt(35) * np.sqrt(n))
            mean_h8 = np.sum(z_data ** 8 - 28 * z_data ** 6 + 210 * z_data ** 4 - 420 * z_data ** 2 + 105) / (
                    24 * np.sqrt(70) * np.sqrt(n))
            vector_aux1 = (mean_h4 + mean_h5 * z_data / np.sqrt(2)
                           + mean_h6 * (z_data ** 2 - 1) / np.sqrt(6) + mean_h7 * (z_data ** 3 - 3 * z_data)
                           / (2 * np.sqrt(6)) + mean_h8 * (z_data ** 4 - 6 * z_data ** 2 + 3) / (
                                 2 * np.sqrt(30)))
            stat_tsl = np.max(np.abs(scipy_stats.norm.cdf(z_data) * mean_h3
                                     - scipy_stats.norm.pdf(z_data) * vector_aux1))
            return stat_tsl


class CabanaCabana2Test(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'CC2' + super(CabanaCabana2Test, CabanaCabana2Test).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat20(rvs)

    @staticmethod
    def stat20(x):
        n = len(x)

        if n > 3:
            # TODO: Move variance calculation
            var_x = n * np.var(x) / (n - 1)
            sd_x = np.sqrt(var_x)
            z = (x - np.mean(x)) / sd_x
            h0 = np.zeros(n)
            h1 = np.zeros(n)
            h2 = np.zeros(n)
            h3 = np.zeros(n)
            h4 = np.zeros(n)
            h5 = np.zeros(n)
            h6 = np.zeros(n)
            h7 = np.zeros(n)
            h8 = np.zeros(n)

            h3_tilde = 0
            h4_tilde = 0
            h5_tilde = 0
            h6_tilde = 0
            h7_tilde = 0
            h8_tilde = 0

            for i in range(n):
                h0[i] = 1
                h1[i] = z[i]
                h2[i] = (math.pow(z[i], 2.0) - 1.0) / np.sqrt(2.0)
                h3[i] = (math.pow(z[i], 3.0) - 3.0 * z[i]) / np.sqrt(6.0)
                h4[i] = (math.pow(z[i], 4.0) - 6.0 * math.pow(z[i], 2.0) + 3.0) / (2.0 * np.sqrt(6.0))
                h5[i] = (math.pow(z[i], 5.0) - 10.0 * math.pow(z[i], 3.0) + 15.0 * z[i]) / (2.0 * np.sqrt(30.0))
                h6[i] = (math.pow(z[i], 6.0) - 15.0 * math.pow(z[i], 4.0) + 45.0 * math.pow(z[i], 2.0) - 15.0) / (
                        12.0 * np.sqrt(5.0))
                h7[i] = (math.pow(z[i], 7.0) - 21.0 * math.pow(z[i], 5.0) + 105.0 * math.pow(z[i], 3.0) - 105.0 * z[
                    i]) / (
                                12.0 * np.sqrt(35.0))
                h8[i] = (math.pow(z[i], 8.0) - 28.0 * math.pow(z[i], 6.0) + 210.0 * math.pow(z[i],
                                                                                             4.0) - 420.0 * math.pow(
                    z[i],
                    2.0) + 105.0) / (
                                24.0 * np.sqrt(70.0))

                h3_tilde = h3_tilde + h3[i]
                h4_tilde = h4_tilde + h4[i]
                h5_tilde = h5_tilde + h5[i]
                h6_tilde = h6_tilde + h6[i]
                h7_tilde = h7_tilde + h7[i]
                h8_tilde = h8_tilde + h8[i]

            h3_tilde = h3_tilde / np.sqrt(n)
            h4_tilde = h4_tilde / np.sqrt(n)
            h5_tilde = h5_tilde / np.sqrt(n)
            h6_tilde = h6_tilde / np.sqrt(n)
            h7_tilde = h7_tilde / np.sqrt(n)
            h8_tilde = h8_tilde / np.sqrt(n)

            vector_aux2 = (np.sqrt(2) * h0 + h2) * h5_tilde + (np.sqrt(3 / 2) * h1 + h3) * h6_tilde + (
                    np.sqrt(4 / 3) * h2 + h4) * h7_tilde + (np.sqrt(5 / 4) * h3 + h5) * h8_tilde + (
                                 np.sqrt(5 / 4) * h3 + h5) * h8_tilde
            stat_tkl = np.max(np.abs(-scipy_stats.norm.pdf(z) * h3_tilde + (
                    scipy_stats.norm.cdf(z) - z * scipy_stats.norm.pdf(z)) * h4_tilde - scipy_stats.norm.pdf(
                z) * vector_aux2))
            return stat_tkl


class ChenShapiroTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'CS' + super(ChenShapiroTest, ChenShapiroTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat26(rvs)

    @staticmethod
    def stat26(x):
        n = len(x)

        if n > 3:
            xs = np.sort(x)
            mean_x = np.mean(x)
            var_x = np.var(x, ddof=1)
            m = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 0.25) - 0.375 / (n + 0.25))
            stat_cs = np.sum((xs[1:] - xs[:-1]) / (m[1:] - m[:-1])) / ((n - 1) * np.sqrt(var_x))
            stat_cs = np.sqrt(n) * (1.0 - stat_cs)
            return stat_cs


class ZhangQTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'ZQ' + super(ZhangQTest, ZhangQTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat27(rvs)

    @staticmethod
    def stat27(x):
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
            stat_q = np.log(q1 / q2)
            return stat_q


class CoinTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'COIN' + super(CoinTest, CoinTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat30(rvs)

    def stat30(self, x):
        n = len(x)

        if n > 3:
            z = [0] * n
            m = [n // 2]
            sp = [0] * m[0]
            a = [0] * n
            var_x = 0.0
            mean_x = 0.0
            term1 = 0.0
            term2 = 0.0
            term3 = 0.0
            term4 = 0.0
            term6 = 0.0

            for i in range(n):
                mean_x += x[i]
            mean_x /= n

            for i in range(n):
                var_x += x[i] ** 2
            var_x = (n * (var_x / n - mean_x ** 2)) / (n - 1)
            sd_x = math.sqrt(var_x)

            for i in range(n):
                z[i] = (x[i] - mean_x) / sd_x

            z.sort()
            self.nscor2(sp, n, m)

            if n % 2 == 0:
                for i in range(n // 2):
                    a[i] = -sp[i]
                for i in range(n // 2, n):
                    a[i] = sp[n - i - 1]
            else:
                for i in range(n // 2):
                    a[i] = -sp[i]
                a[n // 2] = 0.0  # TODO: ???
                for i in range(n // 2 + 1, n):
                    a[i] = sp[n - i - 1]

            for i in range(n):
                term1 += a[i] ** 4
                term2 += a[i] * z[i]
                term3 += a[i] ** 2
                term4 += a[i] ** 3 * z[i]
                term6 += a[i] ** 6

            stat_beta32 = ((term1 * term2 - term3 * term4) / (term1 * term1 - term3 * term6)) ** 2
            return stat_beta32

    @staticmethod
    def correc(i, n):
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


class DagostinoTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'D' + super(DagostinoTest, DagostinoTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)
        if n > 3:
            xs = np.sort(rvs)  # We sort the data
            mean_x = sum(xs) / n
            var_x = sum(x_i ** 2 for x_i in xs) / n - mean_x ** 2
            t = sum((i - 0.5 * (n + 1)) * xs[i - 1] for i in range(1, n + 1))
            d = t / ((n ** 2) * math.sqrt(var_x))
            stat_da = math.sqrt(n) * (d - 0.28209479) / 0.02998598

            return stat_da  # Here is the test statistic value


class ZhangQStarTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'ZQS' + super(ZhangQStarTest, ZhangQStarTest).code()

    def execute_statistic(self, rvs, **kwargs):
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

            q1_star = -np.dot(a, xs[::-1])
            q2_star = -np.dot(b, xs[::-1])

            q_star = np.log(q1_star / q2_star)
            return q_star


class ZhangQQStarTest(NormalityTest):  # TODO: check for correctness

    @staticmethod
    @override
    def code():
        return 'ZQQ' + super(ZhangQQStarTest, ZhangQQStarTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat28(rvs)

    @staticmethod
    def stat28(x):
        n = len(x)

        if n > 3:
            # Computation of the value of the test statistic
            def stat27(x):
                pass

            def stat34(x):
                pass

            p_value27 = [1.0]
            p_value34 = [1.0]

            stat27(x)  # stat Q de Zhang

            if p_value27[0] > 0.5:
                p_val1 = 1.0 - p_value27[0]
            else:
                p_val1 = p_value27[0]

            stat34(x)  # stat Q* de Zhang

            if p_value34[0] > 0.5:
                p_val2 = 1.0 - p_value34[0]
            else:
                p_val2 = p_value34[0]

            stat = -2.0 * (np.log(p_val1) + np.log(p_val2))  # Combinaison des valeurs-p (Fisher, 1932)

            return stat  # Here is the test statistic value


class SWRGTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SWRG' + super(SWRGTest, SWRGTest).code()

    def execute_statistic(self, rvs, **kwargs):
        n = len(rvs)

        if n > 3:
            # Computation of the value of the test statistic
            mi = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
            fi = scipy_stats.norm.pdf(mi)
            aux2 = 2 * mi * fi
            aux1 = np.concatenate(([0], mi[:-1] * fi[:-1]))
            aux3 = np.concatenate((mi[1:] * fi[1:], [0]))
            aux4 = aux1 - aux2 + aux3
            ai_star = -((n + 1) * (n + 2)) * fi * aux4
            norm2 = np.sum(ai_star ** 2)
            ai = ai_star / np.sqrt(norm2)

            xs = np.sort(rvs)
            mean_x = np.mean(xs)
            aux6 = np.sum((xs - mean_x) ** 2)
            stat_wrg = np.sum(ai * xs) ** 2 / aux6

            return stat_wrg  # Here is the test statistic value


class GMGTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'GMG' + super(GMGTest, GMGTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat33(rvs)

    @staticmethod
    def stat33(x):
        n = len(x)

        if n > 3:
            import math
            x_tmp = [0] * n
            var_x = 0.0
            mean_x = 0.0
            jn = 0.0
            pi = 4.0 * math.atan(1.0)  # or use pi = M_PI, where M_PI is defined in math.h

            # calculate sample mean
            for i in range(n):
                mean_x += x[i]
            mean_x = mean_x / n

            # calculate sample var and standard deviation
            for i in range(n):
                var_x += (x[i] - mean_x) ** 2
            var_x = var_x / n
            sd_x = math.sqrt(var_x)

            # calculate sample median
            for i in range(n):
                x_tmp[i] = x[i]

            x_tmp = np.sort(x_tmp)  # We sort the data

            if n % 2 == 0:
                m = (x_tmp[n // 2] + x_tmp[n // 2 - 1]) / 2.0
            else:
                m = x_tmp[n // 2]  # sample median

            # calculate statRsJ
            for i in range(n):
                jn += abs(x[i] - m)
            jn = math.sqrt(pi / 2.0) * jn / n

            stat_rsj = sd_x / jn

            return stat_rsj  # Here is the test statistic value


class BHSTest(NormalityTest):  # TODO: check for correctness

    @staticmethod
    @override
    def code():
        return 'BHS' + super(BHSTest, BHSTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat16(rvs)

    def stat16(self, x):
        n = len(x)

        if n > 3:
            x1 = np.array(x)
            x1 = np.sort(x1)

            if n % 2 == 0:
                in2 = n // 2
                in3 = n // 2
                x2 = x1[:in2]
                x3 = x1[in2:]
            else:
                in2 = n // 2 + 1
                in3 = n // 2 + 1
                x2 = x1[:in2]
                x3 = x1[in2 - 1:]

            eps = [2.220446e-16, 2.225074e-308]
            iter = [1000, 0]
            w1 = self.mc_c_d(x1, n, eps, iter)
            iter = [1000, 0]
            w2 = self.mc_c_d(x2, in2, eps, iter)
            iter = [1000, 0]
            w3 = self.mc_c_d(x3, in3, eps, iter)

            omega1 = 0.0
            omega2 = 0.198828
            omega3 = 0.198828

            vec1 = w1 - omega1
            vec2 = -w2 - omega2
            vec3 = w3 - omega3

            inv_v11 = 0.8571890822945882
            inv_v12 = -0.1051268907484579
            inv_v13 = 0.1051268907484580
            inv_v21 = -0.1051268907484579
            inv_v22 = 0.3944817329840534
            inv_v23 = -0.01109532299714422
            inv_v31 = 0.1051268907484579
            inv_v32 = -0.01109532299714422
            inv_v33 = 0.3944817329840535

            stat_tmclr = n * ((vec1 * inv_v11 + vec2 * inv_v21 + vec3 * inv_v31) * vec1 + (
                    vec1 * inv_v12 + vec2 * inv_v22 + vec3 * inv_v32) * vec2 + (
                                     vec1 * inv_v13 + vec2 * inv_v23 + vec3 * inv_v33) * vec3)
            return stat_tmclr  # Here is the test statistic value

    def mc_c_d(self, z, n, eps, iter):
        trace_lev = iter[0]
        it = 0
        converged = True
        med_c = 0.0
        large = float('inf') / 4.0

        if n < 3:
            med_c = 0.0
            iter[0] = it
            iter[1] = converged
            return med_c

        x = [0.0] * (n + 1)
        for i in range(n):
            zi = z[i]
            x[i + 1] = -large if zi == float('inf') else (-large if zi == float('-inf') else zi)

        x.sort()

        x_med = 0.0
        if n % 2:
            x_med = x[(n // 2) + 1]
        else:
            ind = n // 2
            x_med = (x[ind] + x[ind + 1]) / 2

        if abs(x[1] - x_med) < eps[0] * (eps[0] + abs(x_med)):
            med_c = -1.0
            iter[0] = it
            iter[1] = converged
            return med_c
        elif abs(x[n] - x_med) < eps[0] * (eps[0] + abs(x_med)):
            med_c = 1.0
            iter[0] = it
            iter[1] = converged
            return med_c

        if trace_lev:
            print(f"mc_C_d(z[1:{n}], trace_lev={trace_lev}): Median = {x_med} (not at the border)")

        i, j = 0, 0
        for i in range(1, n + 1):
            x[i] -= x_med

        x_den = -2 * max(-x[1], x[n])
        for i in range(1, n + 1):
            x[i] /= x_den
        x_med /= x_den
        if trace_lev >= 2:
            print(f" x[] has been rescaled (* 1/s) with s = {x_den}")

        j = 1
        x_eps = eps[0] * (eps[0] + abs(x_med))
        while j <= n and x[j] > x_eps:
            j += 1

        if trace_lev >= 2:
            print(f"   x1[] := {{x | x_j > x_eps = {x_eps}}}    has {j - 1} (='j-1') entries")

        i = 1
        x2 = x[j - 1:]
        while j <= n and x[j] > -x_eps:
            j += 1
            i += 1

        if trace_lev >= 2:
            print(f"'median-x' {{x | -eps < x_i <= eps}} has {i - 1} (= 'k') entries")

        h1 = j - 1
        h2 = i + (n - j)

        if trace_lev:
            print(f"  now allocating 2+5 work arrays of size (1+) h2={h2} each:")

        a_cand = [0.0] * h2
        a_srt = [0.0] * h2
        iw_cand = [0] * h2
        left = [1] * (h2 + 1)
        right = [h1] * (h2 + 1)
        p = [0] * (h2 + 1)
        q = [0] * (h2 + 1)

        for i in range(1, h2 + 1):
            left[i] = 1
            right[i] = h1

        nr = h1 * h2
        knew = nr // 2 + 1

        if trace_lev >= 2:
            print(f" (h1,h2, nr, knew) = ({h1},{h2}, {nr}, {knew})")

        trial = -2.0
        work = [0.0] * n
        iwt = [0] * n
        is_found = False
        nl = 0
        neq = 0

        while not is_found and (nr - nl + neq > n) and it < iter[0]:
            it += 1
            j = 0
            for i in range(h2):
                if left[i + 1] <= right[i + 1]:
                    iwt[j] = right[i + 1] - left[i + 1] + 1
                    k = left[i + 1] + (iwt[j] // 2)
                    work[j] = self.h_kern(x[k], x2[i], k, i + 1, h1 + 1, eps[1])
                    j += 1

            if trace_lev >= 4:
                print(f" before whi_med(): work and iwt, each [0:{j - 1}]:")
                if j >= 100:
                    for i in range(90):
                        print(f" {work[i]}", end="")
                    print("\n  ... ", end="")
                    for i in range(j - 4, j):
                        print(f" {work[i]}", end="")
                    print()
                    for i in range(90):
                        print(f" {iwt[i]}", end="")
                    print("\n  ... ", end="")
                    for i in range(j - 4, j):
                        print(f" {iwt[i]}", end="")
                    print()
                else:
                    for i in range(j):
                        print(f" {work[i]}", end="")
                    print()
                    for i in range(j):
                        print(f" {iwt[i]}", end="")
                    print()

            trial = self.whi_med_i(work, iwt, j, a_cand, a_srt, iw_cand)
            eps_trial = eps[0] * (eps[0] + abs(trial))
            if trace_lev >= 3:
                print(f"  it={it}, whi_med(*, n={j})= {trial} ", end="")

            j = 1
            for i in range(h2, 0, -1):
                while j <= h1 and self.h_kern(x[j], x2[i - 1], j, i, h1 + 1, eps[1]) - trial > eps_trial:
                    j += 1
                p[i] = j - 1

            j = h1
            for i in range(1, h2 + 1):
                while j >= 1 and trial - self.h_kern(x[j], x2[i - 1], j, i, h1 + 1, eps[1]) > eps_trial:
                    j -= 1
                q[i] = j + 1

            if trace_lev >= 3:
                if trace_lev == 3:
                    print(f"sum_(p,q)= ({sum(p)}, {sum(q)})", end="")
                else:
                    print(f"\n   p[1:{h2}]:", end="")
                    lrg = h2 >= 100
                    i_m = 95 if lrg else h2
                    for i in range(i_m):
                        print(f" {p[i + 1]}", end="")
                    if lrg:
                        print(" ...", end="")
                    print(f" sum={sum(p)}\n   q[1:{h2}]:", end="")
                    for i in range(i_m):
                        print(f" {q[i + 1]}", end="")
                    if lrg:
                        print(" ...", end="")
                    print(f" sum={sum(q)}")

            if knew <= sum(p):
                if trace_lev >= 3:
                    print("; sum_p >= kn")
                for i in range(h2):
                    right[i + 1] = p[i + 1]
                    if left[i + 1] > right[i + 1] + 1:
                        neq += left[i + 1] - right[i + 1] - 1
                nr = sum(p)
            else:
                is_found = knew <= sum(q)
                if trace_lev >= 3:
                    print(f"; s_p < kn ?<=? s_q: {'TRUE' if is_found else 'no'}")
                if is_found:
                    med_c = trial
                else:
                    for i in range(h2):
                        left[i + 1] = q[i + 1]
                        if left[i + 1] > right[i + 1] + 1:
                            neq += left[i + 1] - right[i + 1] - 1
                    nl = sum(q)

        converged = is_found or (nr - nl + neq <= n)
        if not converged:
            print(f"maximal number of iterations ({iter[0]} =? {it}) reached prematurely")
            med_c = trial

        if converged and trace_lev >= 2:
            print(f"converged in {it} iterations")

        iter[0] = it
        iter[1] = converged

        return med_c

    @staticmethod
    def h_kern(a, b, ai, bi, ab, eps):
        if abs(a - b) < 2.0 * eps or b > 0:
            return math.copysign(1, ab - (ai + bi))
        else:
            return (a + b) / (a - b)

    @staticmethod
    def whi_med_i(a, w, n, a_cand, a_srt, w_cand):
        w_tot = sum(w)
        wrest = 0

        while True:
            for i in range(n):
                a_srt[i] = a[i]
            n2 = n // 2
            a_srt.sort()
            trial = a_srt[n2]

            w_left = 0
            w_mid = 0
            wright = 0
            for i in range(n):
                if a[i] < trial:
                    w_left += w[i]
                elif a[i] > trial:
                    wright += w[i]
                else:
                    w_mid += w[i]

            k_cand = 0
            if 2 * (wrest + w_left) > w_tot:
                for i in range(n):
                    if a[i] < trial:
                        a_cand[k_cand] = a[i]
                        w_cand[k_cand] = w[i]
                        k_cand += 1
            elif 2 * (wrest + w_left + w_mid) <= w_tot:
                for i in range(n):
                    if a[i] > trial:
                        a_cand[k_cand] = a[i]
                        w_cand[k_cand] = w[i]
                        k_cand += 1
                wrest += w_left + w_mid
            else:
                return trial

            n = k_cand
            for i in range(n):
                a[i] = a_cand[i]
                w[i] = w_cand[i]


class SpiegelhalterTest(NormalityTest):

    @staticmethod
    @override
    def code():
        return 'SH' + super(SpiegelhalterTest, SpiegelhalterTest).code()

    def execute_statistic(self, rvs, **kwargs):
        return self.stat41(rvs)

    @staticmethod
    def stat41(x):
        n = len(x)

        if n > 3:
            stat_sp, var_x, mean = 0.0, 0.0, 0.0
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
                var_x += (x[i] - mean) ** 2
            var_x /= (n - 1)
            sd = math.sqrt(var_x)
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

            stat_sp = ((cn * u) ** (-(n - 1)) + g ** (-(n - 1))) ** (1 / (n - 1))

            return stat_sp  # Here is the test statistic value

# TODO: fix all weak warnings
# TODO: check tests
