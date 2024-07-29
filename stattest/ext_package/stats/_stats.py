import math

import numpy as np
import numpy.typing as npt
from statistics import NormalDist
import scipy.stats as sts

normal_dist = NormalDist()
inf, phi, Phi = float('inf'), normal_dist.pdf, normal_dist.cdf

# Values from Stephens, M A, "EDF Statistics for Goodness of Fit and
#             Some Comparisons", Journal of the American Statistical
#             Association, Vol. 69, Issue 347, Sept. 1974, pp 730-737
_Avals_norm = np.array([0.576, 0.656, 0.787, 0.918, 1.092])


def chisquare(f_obs: npt.ArrayLike, f_exp=None, ddof=0, axis=0):
    f_obs = np.asanyarray(f_obs)
    f_obs_float = f_obs.astype(np.float64)
    terms = (f_obs_float - f_exp) ** 2 / f_exp
    stat = terms.sum(axis=axis)
    return stat


def kstest(rvs, cdfvals, alternative='two-sided', method='auto'):
    # x = np.sort(rvs)
    Dplus, dplus_location = _compute_dplus(cdfvals, rvs)
    Dminus, dminus_location = _compute_dminus(cdfvals, rvs)
    if Dplus > Dminus:
        D = Dplus
        d_location = dplus_location
        d_sign = 1
    else:
        D = Dminus
        d_location = dminus_location
        d_sign = -1

    return D


def adstest(x):
    n = len(x)

    s = np.std(x, ddof=1, axis=0)
    y = np.sort(x)
    xbar = np.mean(x, axis=0)
    w = (y - xbar) / s
    # fit_params = xbar, s
    logcdf = sts.distributions.norm.logcdf(w)
    logsf = sts.distributions.norm.logsf(w)
    # sig = np.array([15, 10, 5, 2.5, 1])
    # critical = np.around(_Avals_norm / (1.0 + 4.0 / n - 25.0 / n / n), 3)

    i = np.arange(1, n + 1)
    A2 = -n - np.sum((2 * i - 1.0) / n * (logcdf + logsf[::-1]), axis=0)
    return A2


def cvmtest(x):
    n = len(x)

    vals = np.sort(np.asarray(x))
    cdfvals = sts.norm.cdf(vals)

    u = (2 * np.arange(1, n + 1) - 1) / (2 * n)
    CM = 1 / (12 * n) + np.sum((u - cdfvals) ** 2)
    return CM


def lilliefors(x):
    n = len(x)
    vals = np.sort(np.asarray(x))
    s = np.arange(0, n) / n
    cdfvals = sts.norm.cdf(vals)
    return np.max(np.abs(cdfvals - s))


def dastest(x):
    x = np.asanyarray(x)
    y = np.sort(x)
    n = len(x)

    x_mean = np.mean(x)
    m2 = np.sum((x - x_mean) ** 2) / n
    i = np.arange(1, n + 1)
    c = (n + 1) / 2
    terms = (i - c) * y
    stat = terms.sum() / (n ** 2 * np.sqrt(m2))
    return stat


def dapstest(x):
    x = np.asanyarray(x)
    y = np.sort(x)
    n = len(x)

    k = np.arange(1, n + 1)
    p = k / (n + 1)
    theta = sts.norm.ppf(p)
    m2 = p * (1 - p) / ((n + 2) * sts.norm.pdf(theta) ** 2)
    t = (n + 1) / 2
    stat = np.sum((k - t) * y) / (n ** 2 * np.sqrt(m2))
    print(stat)
    return stat


# TODO: whose test?
def sfstest(x):
    n = len(x)

    x_mean = np.mean(x)
    alpha = 0.375
    terms = (np.arange(1, n + 1) - alpha) / (n - 2 * alpha + 1)
    e = -sts.norm.ppf(terms)

    w = np.sum(e * x) ** 2 / (np.sum((x - x_mean) ** 2) * np.sum(e ** 2))
    return w


# TODO: whose test?
def swstest(f_obs):
    f_obs = np.asanyarray(f_obs)
    f_obs_sorted = np.sort(f_obs)
    x_mean = np.mean(f_obs)

    denominator = (f_obs - x_mean) ** 2
    denominator = denominator.sum()

    a = ordered_statistic(len(f_obs))
    terms = a * f_obs_sorted
    return (terms.sum() ** 2) / denominator


def filli_test(x):
    y = np.sort(x)
    n = len(x)
    n1 = 1 / n
    n2 = n + 0.365
    i = (np.arange(2, n) - 0.3175) / n2
    m = np.concatenate([[1 - 0.5 ** n1], i, [0.5 ** n1]])
    M = sts.norm.ppf(m)
    var = np.var(y)
    return np.sum(y * M) / (np.sqrt(np.sum(M ** 2) * (n - 1) * var))


def mi_test(x):
    n = len(x)
    M = np.median(x)
    A = np.median(np.abs(x - M))
    z = (x - M) / (9 * A)
    i = (abs(z) < 1).nonzero()
    z1 = np.take(z, i)
    x1 = np.take(x, i)
    S = (n * np.sum((x1 - M) ** 2 * (1 - z1 ** 2) ** 4)) / (np.sum((1 - z1 ** 2) * (1 - 5 * z1 ** 2)) ** 2)
    return np.sum((x - M) ** 2) / ((n - 1) * S)


# https://doi.org/10.1007/BF02613501
def ep_test(x):
    y = np.sort(x)
    n = len(x)
    mean = np.mean(x)
    m_2 = sts.moment(y, moment=2)
    indexes = range(1, n + 1)
    s = 0
    for k in indexes:
        x1 = np.take(range(k))
        s += np.exp((-(x1 - x[k]) ** 2) / (2 * m_2))
    T = 1 + n / np.cbrt(3) + 2 * s / n - np.sqrt(2) * np.sum(np.exp((-(x - mean) ** 2) / (4 * m_2)))
    return T


def jb_test(x):
    y = np.sort(x)
    n = len(x)
    m_2 = sts.moment(y, moment=2)
    m_3 = sts.moment(y, moment=3)
    m_4 = sts.moment(y, moment=4)
    s = m_3 ** 2 / m_2 ** 3
    k = m_4 / m_2 ** 3
    JB = (n / 6) * (s + (k - 3) ** 2 / 4)
    return JB


def hosking_test(x, variation=1):
    y = np.sort(x)
    n = len(x)

    return 0


# https://journals.sagepub.com/doi/pdf/10.1177/1536867X1201200302
def chen_s_test(x):
    y = np.sort(x)
    n = len(x)
    s = sts.tstd(x)
    H = (np.arange(1, n + 1) - 3 / 8) / (n + 1 / 4)
    t = np.zeros(n)
    for i in range(n):
        t[i] = (y[i + 1] - y[i]) / (H[i + 1] - H[i])
    SC = (1 / ((n - 1) * s)) * np.sum(t)
    return SC


# Yulia R. Gel; Joseph L. Gastwirth (2008). A robust modification of the Jarque–Bera test of normality. , 99(1), 0–32.         doi:10.1016/j.econlet.2007.05.022
def rjb_test(x):
    y = np.sort(x)
    n = len(x)
    M = np.median(y)
    c = np.sqrt(math.pi / 2)
    J = (c / n) * np.sum(np.abs(x - M))
    m_3 = sts.moment(y, moment=3)
    m_4 = sts.moment(y, moment=4)
    RJB = (n / 6) * (m_3 / J ** 3) ** 2 + (n / 64) * (m_4 / J ** 4 - 3) ** 2
    return RJB


# Rahman, M. Mahibbur; Govindarajulu, Z. (1997). A modification of the test of Shapiro and Wilk for normality. Journal of Applied Statistics, 24(2), 219–236. doi:10.1080/02664769723828
def swrg_test(x):
    f_obs = np.asanyarray(x)
    f_obs_sorted = np.sort(f_obs)
    x_mean = np.mean(f_obs)
    n = len(f_obs)

    denominator = (f_obs - x_mean) ** 2
    denominator = denominator.sum()

    p = np.arange(1, n + 1) / (n + 1)
    m = sts.norm.ppf(p)
    f = sts.norm.pdf(m)
    t = m * f
    a = np.zeros(n)
    for i in range(n):
        ti_1 = 0 if i == 0 else t[i - 1]
        ti_2 = 0 if i == n - 1 else t[i + 1]
        a[i] = -(n + 1) * (n + 2) * sts.norm.pdf(m[i]) * (ti_1 - 2 * t[i] + ti_2)
    terms = a * f_obs_sorted
    return (terms.sum() ** 2) / denominator


def gmg_test(x):
    y = np.sort(x)
    n = len(x)
    M = np.median(y)
    c = np.sqrt(math.pi / 2)
    J = (c / n) * np.sum(np.abs(x - M))
    s = np.std(y)
    return s / J


def glb_test(x):
    n = len(x)
    p = np.array([])  # TODO:
    i = np.arange(1, n + 1)
    t = (2 * n + 1 - 2 * i) * np.log(p) + (2 * i - 1) * np.log(1 - p)
    P = -n - (1 / n) * np.sum(t)
    return P


def bs_test(x):
    n = len(x)
    x_mean = np.mean(x)
    a = x - x_mean
    m2 = (1 / n) * np.sum(a)
    t = np.sum(np.abs(a))
    w = 13.29 * (np.log(m2) - np.log(t / n))
    T = (np.sqrt(n + 2) * (w - 3)) / 3.54
    return T


def zw1_test(x):
    n = len(x)
    i = np.arange(1, n + 1)
    f = (i - 0.5) / n
    t = np.log(f) / (n - i + 0.5) + (np.log(1 - f)) / (i - 0.5)
    Z = -np.sum(t)
    return Z


def zw2_test(x):
    n = len(x)
    i = np.arange(1, n + 1)
    f = (i - 0.5) / n
    t = (1 / f - 1) / ((n - 0.5) / (i - 0.75) - 1)
    Z = np.sum(np.log(t) ** 2)
    return Z


def dh_test(x):
    n = len(x)

    m_2 = sts.moment(x, moment=2)
    m_3 = sts.moment(x, moment=3)
    m_4 = sts.moment(x, moment=4)
    s = m_3 / (np.sqrt(m_2) ** 3)
    k = m_4 / (m_2 ** 2)

    b = (3 * (n ** 2 + 27 * n - 70) * (n + 1) * (n + 3)) / ((n - 2) * (n + 5) * (n + 7) * (n + 9))
    w2 = -1 + np.sqrt(2 * (b - 1))
    delta = 1 / np.sqrt(np.log(w2))
    y = s * np.sqrt(((w2 - 1) * (n + 1) * (n + 3)) / (12 * (n - 2)))
    z1 = delta * np.log(y + np.sqrt(y ** 2 - 1))

    delta1 = (n - 3) * (n + 1) * (n ** 2 + 15 * n - 4)
    a = ((n - 2) * (n + 5) * (n + 7) * (n ** 2 + 27 * n - 70)) / (6 * delta1)
    c = ((n - 7) * (n + 5) * (n + 7) * (n ** 2 + 2 * n - 5)) / (6 * delta1)
    l = ((n + 5) * (n + 7) * (n ** 3 + 37 * n ** 2 + 11 * n - 313)) / (12 * delta1)
    hi = 2 * l * (k - 1 - s ** 2)
    alpha = a + c * s ** 2
    z2 = np.sqrt(2 * alpha) * (
            1 / (9 * alpha) - 1 + np.cbrt(hi / (2 * alpha)))  # TODO: np.sqrt(2 * alpha) vs np.sqrt(9 * alpha)

    DH = z1 ** 2 + z2 ** 2
    return DH


def _compute_dplus(cdfvals, x):
    n = len(cdfvals)
    dplus = (np.arange(1.0, n + 1) / n - cdfvals)
    amax = dplus.argmax()
    loc_max = x[amax]
    return (dplus[amax], loc_max)


def _compute_dminus(cdfvals, x):
    n = len(cdfvals)
    dminus = (cdfvals - np.arange(0.0, n) / n)
    amax = dminus.argmax()
    loc_max = x[amax]
    return (dminus[amax], loc_max)


def _compute_m2(x, n: int):
    x_float = x.astype(np.float64)
    x_mean = np.mean(x)
    terms = (x_float - x_mean) ** 2
    m2 = terms.sum() / n
    return m2


def blom(r, n):
    alpha = 0.375


def ordered_statistic(n):
    if n == 3:
        sqrt = np.sqrt(0.5)
        return np.array([sqrt, 0, -sqrt])

    m = np.array([sts.norm.ppf((i - 3 / 8) / (n + 0.25)) for i in range(1, n + 1)])

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
