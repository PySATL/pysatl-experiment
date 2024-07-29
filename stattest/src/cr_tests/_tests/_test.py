import scipy.stats as scipy_stats
import numpy as np
import matplotlib.pyplot as plt

from stattest.src.cr_tests.criteria.abstract_test import AbstractTest
from stattest.src.cr_tests.criteria.normality_tests import KSTest


def monte_carlo(test: AbstractTest, rvs_size, count=100000):  # TODO: relocate to tests
    result = np.zeros(count)

    for i in range(count):
        x = test.generate(size=rvs_size)
        result[i] = test.execute_statistic(x)

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


def test(test: AbstractTest, rvs_size, count=5):
    for i in range(count):
        x = test.test(scipy_stats.uniform.rvs(size=rvs_size), 0.05)
        print(x)


if __name__ == '__main__':
    monte_carlo(KSTest(), 30)
