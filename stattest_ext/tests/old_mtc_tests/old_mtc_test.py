import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as scipy_stats

from stattest_ext.src.tests_generators.stat_gen import StatisticGenerator
from stattest_std.src.stat_tests.abstract_test import AbstractTest
from stattest_std.src.stat_tests.normality_tests import KSTest


def monte_carlo(_test: AbstractTest, rvs_size, count=100000):
    result = np.zeros(count)

    for i in range(count):
        generator = StatisticGenerator(_test)
        x = generator.generate(size=rvs_size)
        result[i] = generator.execute_statistic(x)

    result.sort()

    ecdf = scipy_stats.ecdf(result)
    x_cr = np.quantile(ecdf.cdf.quantiles, q=0.95)
    print('Critical value', x_cr, ecdf.cdf.quantiles)

    # fig, ax = plt.subplots()
    # ax.set_title("PDF from Template")
    # ax.hist(result, density=True, bins=100)
    # ax.legend()
    # fig.show()

    ecdf = scipy_stats.ecdf(result)
    plt.plot(result, ecdf.cdf.probabilities)
    plt.ylabel('some numbers')
    plt.show()


def test(_test: AbstractTest, rvs_size, count=5):
    for i in range(count):
        x = _test.test(scipy_stats.uniform.rvs(size=rvs_size), 0.05)
        print(x)


if __name__ == '__main__':
    monte_carlo(KSTest(), 30)
