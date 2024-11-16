import numpy as np
import scipy.stats as scipy_stats
from scipy import special
from typing_extensions import override

from stattest.test.models import AbstractTestStatistic


class KSTestStatistic(AbstractTestStatistic):

    def __init__(self, alternative='two-sided', mode='auto'):
        self.alternative = alternative
        if mode == 'auto':  # Always select exact
            mode = 'exact'
        self.mode = mode

    @staticmethod
    def code():
        raise NotImplementedError("Method is not implemented")

    @override
    def execute_statistic(self, rvs, cdf_vals=None):
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

        Parameters
        ----------
        cdf_vals
        """
        # rvs = np.sort(rvs)
        n = len(rvs)

        d_minus, _ = KSTestStatistic.__compute_dminus(cdf_vals, rvs)

        if self.alternative == 'greater':
            d_plus, d_location = KSTestStatistic.__compute_dplus(cdf_vals, rvs)
            return d_plus
        if self.alternative == 'less':
            d_minus, d_location = KSTestStatistic.__compute_dminus(cdf_vals, rvs)
            return d_minus

        # alternative == 'two-sided':
        d_plus, d_plus_location = KSTestStatistic.__compute_dplus(cdf_vals, rvs)
        d_minus, d_minus_location = KSTestStatistic.__compute_dminus(cdf_vals, rvs)
        if d_plus > d_minus:
            D = d_plus
            d_location = d_plus_location
            d_sign = 1
        else:
            D = d_minus
            d_location = d_minus_location
            d_sign = -1

        if self.mode == 'exact':
            prob = scipy_stats.distributions.kstwo.sf(D, n)
        elif self.mode == 'asymp':
            prob = scipy_stats.distributions.kstwobign.sf(D * np.sqrt(n))
        else:
            # mode == 'approx'
            prob = 2 * scipy_stats.distributions.ksone.sf(D, n)
        prob = np.clip(prob, 0, 1)
        return D

    @override
    def calculate_critical_value(self, rvs_size, sl):
        return scipy_stats.distributions.kstwo.ppf(1 - sl, rvs_size)

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


class ADTestStatistic(AbstractTestStatistic):

    @staticmethod
    @override
    def code():
        raise NotImplementedError("Method is not implemented")

    @override
    def execute_statistic(self, rvs, log_cdf=None, log_sf=None, w=None):
        """
        Title: The Anderson-Darling test Ref. (book or article): See package nortest and also Table 4.9 p. 127 in M.
        A. Stephens, “Tests Based on EDF Statistics,” In: R. B. D’Agostino and M. A. Stephens, Eds., Goodness-of-Fit
        Techniques, Marcel Dekker, New York, 1986, pp. 97-193.

        :param rvs:
        :return:
        """
        n = len(rvs)

        i = np.arange(1, n + 1)
        A2 = -n - np.sum((2 * i - 1.0) / n * (log_cdf + log_sf[::-1]), axis=0)
        return A2


class LillieforsTest(KSTestStatistic):

    @staticmethod
    @override
    def code():
        raise NotImplementedError("Method is not implemented")

    @override
    def execute_statistic(self, rvs, cdf_vals=None):
        x = np.asarray(rvs)
        z = (x - x.mean()) / x.std(ddof=1)

        d_ks = super().execute_statistic(z, cdf_vals)

        return d_ks


class CrammerVonMisesTestStatistic(AbstractTestStatistic):
    @override
    def execute_statistic(self, rvs, cdf_vals):
        n = len(rvs)

        u = (2 * np.arange(1, n + 1) - 1) / (2 * n)
        w = 1 / (12 * n) + np.sum((u - cdf_vals) ** 2)

        return w


class Chi2TestStatistic(AbstractTestStatistic):

    @staticmethod
    def _m_sum(a, *, axis, preserve_mask, xp):
        if np.ma.isMaskedArray(a):
            sum = a.sum(axis)
            return sum if preserve_mask else np.asarray(sum)
        return xp.sum(a, axis=axis)

    @override
    def execute_statistic(self, f_obs, f_exp, lambda_):
        # `terms` is the array of terms that are summed along `axis` to create
        # the test statistic.  We use some specialized code for a few special
        # cases of lambda_.
        f_obs = np.array(f_obs)
        if lambda_ == 1:
            # Pearson's chi-squared statistic
            terms = (f_obs - f_exp) ** 2 / f_exp
        elif lambda_ == 0:
            # Log-likelihood ratio (i.e. G-test)
            terms = 2.0 * special.xlogy(f_obs, f_obs / f_exp)
        elif lambda_ == -1:
            # Modified log-likelihood ratio
            terms = 2.0 * special.xlogy(f_exp, f_exp / f_obs)
        else:
            # General Cressie-Read power divergence.
            terms = f_obs * ((f_obs / f_exp) ** lambda_ - 1)
            terms /= 0.5 * lambda_ * (lambda_ + 1)

        return terms.sum()

    @override
    def calculate_critical_value(self, rvs_size, sl):
        return scipy_stats.distributions.chi2.ppf(1 - sl, rvs_size - 1)


class MinToshiyukiTestStatistic(AbstractTestStatistic):

    @override
    def execute_statistic(self, cdf_vals):
        n = len(cdf_vals)
        d_plus = (np.arange(1.0, n + 1) / n - cdf_vals)
        d_minus = (cdf_vals - np.arange(0.0, n) / n)
        d = np.maximum.reduce([d_plus, d_minus])

        fi = 1/(cdf_vals*(1-cdf_vals))

        s = np.sum(d * np.sqrt(fi))
        return s / np.sqrt(n)

# TODO: fix signatures
