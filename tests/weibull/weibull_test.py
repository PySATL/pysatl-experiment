import numpy
import pytest
from numpy import nan

from stattest.test import (
    ADWeibullTest,
    KSWeibullTest,
    LOSWeibullTestStatistic,
    MSFWeibullTestStatistic,
    OKWeibullTestStatistic,
    REJGWeibullTestStatistic,
    RSBWeibullTestStatistic,
    SBWeibullTestStatistic,
    SPPWeibullTestStatistic,
    ST1WeibullTestStatistic,
    ST2WeibullTestStatistic,
    TSWeibullTestStatistic,
)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.38323312,
                    -1.10386561,
                    0.75226465,
                    -2.23024566,
                    -0.27247827,
                    0.95926434,
                    0.42329541,
                    -0.11820711,
                    0.90892169,
                    -0.29045373,
                ],
                0.686501978410317,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1.0),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], 1.0),  # Negative values test
    ],
)
def test_ks_weibull_test(data, result):
    statistic = KSWeibullTest().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.00001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.38323312,
                    -1.10386561,
                    0.75226465,
                    -2.23024566,
                    -0.27247827,
                    0.95926434,
                    0.42329541,
                    -0.11820711,
                    0.90892169,
                    -0.29045373,
                ],
                0.686501978410317,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
@pytest.mark.skip(reason="no way of currently testing this")
def test_ad_weibull_test(data, result):
    statistic = ADWeibullTest().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.00001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                1.1845,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_los_weibull_test(data, result):
    statistic = LOSWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.1, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                0.67173,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_msf_weibull_test(data, result):
    statistic = MSFWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.01, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                1.8927,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_ok_weibull_test(data, result):
    statistic = OKWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.0001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                0.84064,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_rejg_weibull_test(data, result):
    statistic = REJGWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.00001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                8.4755,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_rsb_weibull_test(data, result):
    statistic = RSBWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.0001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                1.0644,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_sb_weibull_test(data, result):
    statistic = SBWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.01, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                0.78178,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_spp_weibull_test(data, result):
    statistic = SPPWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.1, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                1.1202,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_st1_weibull_test(data, result):
    statistic = ST1WeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                3.218,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_st2_weibull_test(data, result):
    statistic = ST2WeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.00001, nan_ok=True)


@pytest.mark.parametrize(
    ("data", "result"),
    [
        # Weibull
        (
                [
                    0.92559015,
                    0.9993195,
                    1.15193844,
                    0.84272073,
                    0.97535299,
                    0.83745092,
                    0.92161732,
                    1.02751619,
                    0.90079826,
                    0.79149641,
                ],
                0.71566,
        ),
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], nan),  # Zero exception test
        ([-4, -1, -6, -8, -4, -2, 0, -2, 0, -3], nan),  # Negative values test
    ],
)
def test_ts_weibull_test(data, result):  # TODO: should move it to abstract class??
    statistic = TSWeibullTestStatistic().execute_statistic(data)
    assert result == pytest.approx(statistic, 0.01, nan_ok=True)
