from typing import override
import numpy as np
import scipy.stats as scipy_stats

from stattest_ext.src.tests_generators.stat_gen import StatisticGenerator
from stattest_std.src.stat_tests.goodness_test import GoodnessOfFitTest


class StatGenGoodnessOfFitTest(StatisticGenerator, GoodnessOfFitTest):
    def __init__(self, criterion: GoodnessOfFitTest):
        super().__init__()
        self.criterion = criterion

    @override
    def _get_statistic(self, rvs_size, alpha, keys_cr, count):
        result = np.zeros(count)

        for i in range(count):
            x = self.generate(rvs_size)
            result[i] = self.criterion.execute_statistic(x)

        result.sort()

        ecdf = scipy_stats.ecdf(result)
        x_cr = np.quantile(ecdf.cdf.quantiles, q=1 - alpha)
        self.criterion.cache.put_with_level(keys_cr, x_cr)
        self.criterion.cache.put_distribution(self.criterion.code(), rvs_size, result)
        self.criterion.cache.flush()
        return x_cr

    @override
    def _get_distribution_from_cache(self, rvs_size, alpha, keys_cr):
        return self.criterion._get_distribution_from_cache(rvs_size, alpha, keys_cr)
