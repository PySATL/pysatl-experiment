from pysatl.criterion import AbstractStatistic

from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.experiment.test.critical_value import get_or_calculate_critical_value
from stattest.persistence.models import ICriticalValueStore


def execute_test(
    test: AbstractStatistic,
    hypothesis: AbstractHypothesis,
    rvs: list[float],
    alpha: float,
    store: ICriticalValueStore,
    count: int,
):
    critical_values = get_or_calculate_critical_value(
        test, hypothesis, len(rvs), alpha, store, count
    )

    statistic = test.execute_statistic(rvs)

    if isinstance(critical_values, tuple):
        lower_critical, upper_critical = critical_values
        return not (lower_critical > statistic or statistic > upper_critical)
    else:
        return not (statistic > critical_values)


def calculate_test_power(
    test: AbstractStatistic,
    data: list[list[float]],
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
