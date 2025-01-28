from typing import List

from stattest.experiment.configuration.configuration import AbstractHypothesis
from stattest.experiment.test.critical_value import get_or_calculate_critical_value
from stattest.persistence.models import ICriticalValueStore
from stattest.test import AbstractTestStatistic


def execute_test(
    test: AbstractTestStatistic,
    hypothesis: AbstractHypothesis,
    rvs: List[float],
    alpha: float,
    store: ICriticalValueStore,
    count: int,
):
    x_cr = get_or_calculate_critical_value(test, hypothesis, len(rvs), alpha, store, count)
    statistic = test.execute_statistic(rvs)

    return False if statistic > x_cr else True


def calculate_test_power(
    test: AbstractTestStatistic,
    data: List[List[float]],
    hypothesis: AbstractHypothesis,
    alpha: float,
    store: ICriticalValueStore,
    count: int,
):
    """
    Calculate statistic test power.

    :param hypothesis: hypothesis to test
    :param store: critical value store
    :param test: statistic test
    :param data: alternative data
    :param alpha: significant level
    :param count: count of test execution
    :return:
    """

    k = 0
    for rvs in data:
        x = execute_test(test, hypothesis, rvs, alpha, store, count)
        if x is False:
            k = k + 1
    return k / len(data)
