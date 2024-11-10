import numpy as np
from scipy.stats import kstest

from stattest.experiment.configuration.configuration import AbstractHypothesis
from stattest.test import AbstractTestStatistic, KSWeibullTest
import scipy.stats as scipy_stats
import multiprocessing


def get_value(test1: AbstractTestStatistic, hypothesis: AbstractHypothesis, size):
    x = hypothesis.generate(size=size)
    return test1.execute_statistic(x)


def calculate_critical_value1(test1: AbstractTestStatistic, hypothesis: AbstractHypothesis, size: int, alpha: float,
                              count) -> (float, [float]):
    # Calculate critical value
    tests = count*[test1]
    hypothesis = count*[hypothesis]
    sizes = count*[size]

    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        distribution = pool.starmap(get_value, zip(tests, hypothesis, sizes))

    distribution.sort()

    ecdf = scipy_stats.ecdf(distribution)
    critical_value = float(np.quantile(ecdf.cdf.quantiles, q=1 - alpha))
    return critical_value, distribution


if __name__ == '__main__':
    test = KSWeibullTest()
    rvs = np.sort(rvs)
    cdf_vals = generate_weibull_cdf(rvs, l=self.l, k=self.k)
    kstest()
    '''start = timeit.default_timer()
    value = calculate_critical_value(test, StandardNormalHypothesis(), 30, 0.05, 1_000_000)
    end = timeit.default_timer()
    print(end - start, value)

    start = timeit.default_timer()
    value1, _ = calculate_critical_value1(test, StandardNormalHypothesis(), 30, 0.05, 1_000_000)
    end = timeit.default_timer()
    print(end - start, value1)'''
