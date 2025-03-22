import numpy as np
import scipy.stats as scipy_stats
from pysatl.criterion import AbstractStatistic

from stattest.experiment.hypothesis import AbstractHypothesis
from stattest.persistence.models import ICriticalValueStore


def calculate_critical_value(
    test: AbstractStatistic,
    hypothesis: AbstractHypothesis,
    size: int,
    alpha: float,
    count,
) -> tuple[float, list[float]]:
    # Calculate critical value
    distribution = np.zeros(count)

    for i in range(count):
        x = hypothesis.generate(size=size)
        distribution[i] = test.execute_statistic(x)

    distribution.sort()

    ecdf = scipy_stats.ecdf(distribution)
    critical_value = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha))
    return critical_value, distribution.tolist()


def calculate_two_tailed_critical_value(
    test: AbstractStatistic,
    hypothesis: AbstractHypothesis,
    size: int,
    alpha: float,
    count: int,
) -> tuple[tuple[float, float], list[float]]:
    distribution = np.zeros(count)

    for i in range(count):
        x = hypothesis.generate(size=size)
        distribution[i] = test.execute_statistic(x)

    distribution.sort()

    ecdf = scipy_stats.ecdf(distribution)
    lower_critical = float(np.quantile(ecdf.cdf.quantiles, q=alpha / 2))
    upper_critical = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha / 2))

    return (lower_critical, upper_critical), distribution.tolist()


def get_or_calculate_critical_value(
    test: AbstractStatistic,
    hypothesis: AbstractHypothesis,
    size: int,
    alpha: float,
    store: ICriticalValueStore,
    count: int,
) -> float | tuple[float, float]:
    critical_values = test.calculate_two_tailed_critical_values(size, alpha)
    if critical_values is not None:
        return critical_values

    critical_value = test.calculate_critical_value(size, alpha)
    if critical_value is not None:
        return critical_value

    critical_value = store.get_critical_value(test.code(), size, alpha)
    if critical_value is not None:
        return critical_value

    distribution = store.get_distribution(test.code(), size)
    if distribution is not None:
        ecdf = scipy_stats.ecdf(distribution)
        if test.two_tailed:
            lower_critical = float(np.quantile(ecdf.cdf.quantiles, q=alpha / 2))
            upper_critical = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha / 2))
            critical_value = (lower_critical, upper_critical)
        else:
            critical_value = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha))

        store.insert_critical_value(test.code(), size, alpha, critical_value)
        return critical_value

    if test.two_tailed:
        critical_value, distribution = calculate_two_tailed_critical_value(
            test, hypothesis, size, alpha, count
        )
    else:
        critical_value, distribution = calculate_critical_value(
            test, hypothesis, size, alpha, count
        )

    store.insert_critical_value(test.code(), size, alpha, critical_value)
    store.insert_distribution(test.code(), size, distribution)

    return critical_value
