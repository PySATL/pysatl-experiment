from scipy.stats import norm
import numpy as np
from stattest.src._ext_package._utils import _check_sample_length, _scale_sample


def eptest_exp(x):
    """
    Epps and Pulley test statistic for exponentiality.

    Parameters
    ----------
    x : array_like
        Array of sample data.

    Returns
    -------
    statistic : float
        The test statistic.
    """
    n = len(x)
    _check_sample_length(x)
    x_scaled = _scale_sample(x)

    statistic_sum = 0
    for j in range(n):
        statistic_sum += np.exp(-x_scaled[j])

    statistic = ((48 * n) ** 0.5) * ((statistic_sum / n) - 0.5)

    return statistic


def cmtest_exp(x):
    """
    Cramer-von-Mises test statistic for exponentiality.

    Parameters
    ----------
    x : array_like
        Array of sample data.

    Returns
    -------
    statistic : float
        The test statistic.
    """
    n = len(x)
    _check_sample_length(x)
    x_scaled_sorted = sorted(_scale_sample(x))

    statistic_sum = 0
    for j in range(n):
        statistic_sum += ((1 - np.exp(-x_scaled_sorted[j])) - (2 * j - 1) / (2 * n)) ** 2

    statistic = (1 / 12 * n) + statistic_sum

    return statistic


def kstest_exp(x):
    """
    Kolmogorov and Smirnov test statistic for exponentiality.

    Parameters
    ----------
    x : array_like
        Array of sample data.

    Returns
    -------
    statistic : float
        The test statistic.
    """
    n = len(x)
    _check_sample_length(x)
    x_scaled_sorted = sorted(_scale_sample(x))

    ks_plus = float('-inf')
    ks_minus = float('-inf')

    for j in range(n):
        ks_plus = max(j / n - (1 - np.exp(-x_scaled_sorted[j])), ks_plus)
        ks_minus = max((1 - np.exp(-x_scaled_sorted[j]) - (j - 1) / n), ks_minus)

    statistic = max(ks_plus, ks_minus)

    return statistic


def zptest_exp(x):
    """
    Zardasht et al. test statistic for exponentiality.

    Parameters
    ----------
    x : array_like
        Array of sample data.

    Returns
    -------
    statistic : float
        The test statistic.
    """
    n = len(x)
    _check_sample_length(x)
    x_scaled = _scale_sample(x)

    statistic_sum = 0
    for j in range(n):
        statistic_sum += x_scaled[j] * np.exp(-x_scaled[j])

    statistic = statistic_sum / n - (1 / 4)

    return statistic
