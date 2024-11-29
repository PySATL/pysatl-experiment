import numpy as np
import scipy.stats as scipy_stats

from stattest.experiment.configuration.configuration import AbstractHypothesis
from stattest.persistence.models import ICriticalValueStore
from stattest.test import AbstractTestStatistic


def calculate_critical_value(test: AbstractTestStatistic, hypothesis: AbstractHypothesis, size: int, alpha: float,
                             count) -> (float, [float]):
    # Calculate critical value
    distribution = np.zeros(count)

    for i in range(count):
        x = hypothesis.generate(size=size)
        distribution[i] = test.execute_statistic(x)

    distribution.sort()

    ecdf = scipy_stats.ecdf(distribution)
    critical_value = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha))
    return critical_value, distribution


def get_or_calculate_critical_value(test: AbstractTestStatistic, hypothesis: AbstractHypothesis, size: int, alpha: float,
                                    store: ICriticalValueStore, count: int) -> float:
    # Get critical value distribution is known
    critical_value = test.calculate_critical_value(size, alpha)
    if critical_value is not None:
        return critical_value

    # Get critical value if exists
    critical_value = store.get_critical_value(test.code(), size, alpha)
    if critical_value is not None:
        return critical_value

    distribution = store.get_distribution(test.code(), size)
    if distribution is not None:
        ecdf = scipy_stats.ecdf(distribution)
        critical_value = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha))
        store.insert_critical_value(test.code(), size, alpha, critical_value)
        return critical_value

    # Calculate critical value
    critical_value, distribution = calculate_critical_value(test, hypothesis, size, alpha, count)

    # Save critical value
    store.insert_critical_value(test.code(), size, alpha, critical_value)
    # Save distribution
    store.insert_distribution(test.code(), size, distribution)

    return critical_value
